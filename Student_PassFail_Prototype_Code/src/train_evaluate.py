"""Train and evaluate pass/fail models; writes tables and figures to outputs/."""
import json, sys
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score,
                             roc_auc_score, confusion_matrix, ConfusionMatrixDisplay)
from sklearn.inspection import permutation_importance
import joblib
from common import *

OUT = "../outputs/"
res = {}
for subject, path in (("Mathematics", "../data/student-mat.csv"), ("Portuguese", "../data/student-por.csv")):
    df = load(path)
    res[subject] = {"n": len(df), "pass_rate": float(df.passed.mean()), "scenarios": {}}
    for scen, cols in feature_sets(df).items():
        X, y = df[cols], df["passed"]
        Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, stratify=y, random_state=SEED)
        cv = StratifiedKFold(5, shuffle=True, random_state=SEED)
        rows = {}
        for m in MODELS:
            pipe = make_model(m, Xtr)
            cvf1 = cross_val_score(pipe, Xtr, ytr, cv=cv, scoring="f1").mean()
            pipe.fit(Xtr, ytr)
            p = pipe.predict(Xte)
            prob = pipe.predict_proba(Xte)[:, 1]
            # "at-risk" = fail class (0): recall of failing students is what an early-warning tool needs
            rows[m] = dict(accuracy=accuracy_score(yte, p),
                           precision_pass=precision_score(yte, p, zero_division=0),
                           recall_pass=recall_score(yte, p, zero_division=0),
                           f1_pass=f1_score(yte, p, zero_division=0),
                           precision_fail=precision_score(yte, p, pos_label=0, zero_division=0),
                           recall_fail=recall_score(yte, p, pos_label=0, zero_division=0),
                           f1_fail=f1_score(yte, p, pos_label=0, zero_division=0),
                           auc=roc_auc_score(yte, prob), cv_f1_pass=cvf1,
                           cm=confusion_matrix(yte, p).tolist(), n_test=len(yte))
            if subject == "Mathematics":
                joblib.dump({"model": pipe, "cols": cols}, f"{OUT}model_{scen}_{m.replace(' ','_')}.joblib") if m == "Random Forest" else None
        res[subject]["scenarios"][scen] = rows

        if subject == "Mathematics":
            # permutation importance for Random Forest on held-out set
            rf = make_model("Random Forest", Xtr).fit(Xtr, ytr)
            pi = permutation_importance(rf, Xte, yte, n_repeats=30, random_state=SEED, scoring="f1")
            imp = pd.Series(pi.importances_mean, index=cols).sort_values(ascending=False).head(8)
            res[subject].setdefault("importance", {})[scen] = imp.round(4).to_dict()
            fig, ax = plt.subplots(figsize=(6, 3.6))
            imp[::-1].plot.barh(ax=ax, color="#2f6f9f")
            ax.set_xlabel("Mean drop in F1 when feature is shuffled"); ax.set_title(f"Top predictors – {scen.replace('_',' ')}")
            fig.tight_layout(); fig.savefig(f"{OUT}fig_importance_{scen}.png", dpi=200); plt.close(fig)
            # confusion matrix for RF
            fig, ax = plt.subplots(figsize=(3.6, 3.2))
            ConfusionMatrixDisplay(confusion_matrix(yte, rf.predict(Xte)), display_labels=["Fail", "Pass"]).plot(ax=ax, cmap="Blues", colorbar=False)
            ax.set_title(f"Random Forest – {scen.replace('_',' ')}", fontsize=8)
            fig.tight_layout(); fig.savefig(f"{OUT}fig_cm_{scen}.png", dpi=200); plt.close(fig)
            # fairness: recall of failing students by sex (RF)
            pred = rf.predict(Xte); g = df.loc[Xte.index, "sex"].values
            fair = {}
            for s in ("F", "M"):
                mk = g == s
                fair[s] = dict(n=int(mk.sum()), acc=float(accuracy_score(yte[mk], pred[mk])),
                               recall_fail=float(recall_score(yte[mk], pred[mk], pos_label=0, zero_division=0)),
                               n_fail=int((yte[mk] == 0).sum()))
            res[subject].setdefault("fairness_sex", {})[scen] = fair

json.dump(res, open(OUT + "results.json", "w"), indent=1)
print(json.dumps({s: {k: v for k, v in r.items() if k != "scenarios"} for s, r in res.items()}, indent=1))
for s, r in res.items():
    for sc, rows in r["scenarios"].items():
        print("\n", s, sc)
        print(pd.DataFrame(rows).T.drop(columns="cm").round(3).to_string())
