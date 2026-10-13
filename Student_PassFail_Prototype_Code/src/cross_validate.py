"""Repeated stratified 5-fold CV (10 repeats) on the full dataset: more stable than one 80/20 split."""
import json, warnings; warnings.filterwarnings("ignore")
import pandas as pd
from sklearn.model_selection import RepeatedStratifiedKFold, cross_validate
from sklearn.metrics import make_scorer, recall_score
from common import *
sc = {"accuracy": "accuracy", "auc": "roc_auc", "f1_pass": "f1",
      "recall_fail": make_scorer(recall_score, pos_label=0, zero_division=0)}
out = {}
for subject, path in (("Mathematics", "../data/student-mat.csv"), ("Portuguese", "../data/student-por.csv")):
    df = load(path)
    for scen, cols in feature_sets(df).items():
        X, y = df[cols], df.passed
        cv = RepeatedStratifiedKFold(n_splits=5, n_repeats=10, random_state=SEED)
        for m in MODELS:
            r = cross_validate(make_model(m, X), X, y, cv=cv, scoring=sc, n_jobs=-1)
            out[f"{subject}|{scen}|{m}"] = {k: [float(r[f"test_{k}"].mean()), float(r[f"test_{k}"].std())] for k in sc}
json.dump(out, open("../outputs/cv_results.json", "w"), indent=1)
t = pd.DataFrame({k: {m: f"{v[0]:.3f}±{v[1]:.3f}" for m, v in d.items()} for k, d in out.items()}).T
print(t.to_string())
