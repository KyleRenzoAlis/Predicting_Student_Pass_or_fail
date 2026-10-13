"""Demo: predict pass/fail for a student and explain the main drivers.

Usage:
  python predict.py --demo                      # three built-in sample students
  python predict.py --row 17                    # predict for row 17 of the Math dataset
  python predict.py --json '{"G1":8,"G2":7,"failures":1,...}'   # full feature dict
Add --no-grades to use the early-warning model (background factors only).
"""
import argparse, json, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from common import *

def build(no_grades):
    df = load("../data/student-mat.csv")
    cols = feature_sets(df)["A_background_only" if no_grades else "B_with_midterm_grades"]
    pipe = make_model("Logistic Regression", df[cols]).fit(df[cols], df.passed)
    return df, cols, pipe

def explain(pipe, row, k=3):
    pre, clf = pipe.named_steps["pre"], pipe.named_steps["clf"]
    x = pre.transform(row)
    contrib = np.asarray(x.todense() if hasattr(x, "todense") else x).ravel() * clf.coef_[0]
    names = pre.get_feature_names_out()
    order = np.argsort(contrib)
    clean = lambda n: n.split("__", 1)[1]
    return [(clean(names[i]), contrib[i]) for i in order[:k]], [(clean(names[i]), contrib[i]) for i in order[::-1][:k]]

def report(label, row, pipe):
    p = pipe.predict_proba(row)[0, 1]
    tier = "LOW risk" if p >= 0.75 else "MODERATE risk" if p >= 0.5 else "HIGH risk"
    neg, pos = explain(pipe, row)
    print(f"Student: {label}")
    print(f"  Predicted outcome : {'PASS' if p >= .5 else 'FAIL'}   (P(pass) = {p:.2f}, {tier})")
    print("  Pushing toward FAIL: " + ", ".join(f"{n} ({v:+.2f})" for n, v in neg))
    print("  Pushing toward PASS: " + ", ".join(f"{n} ({v:+.2f})" for n, v in pos))
    print()

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true"); ap.add_argument("--row", type=int)
    ap.add_argument("--json"); ap.add_argument("--no-grades", action="store_true")
    a = ap.parse_args()
    df, cols, pipe = build(a.no_grades)
    mode = "early-warning (no grades)" if a.no_grades else "with mid-term grades G1, G2"
    print(f"=== Student Pass/Fail Predictor | Logistic Regression | {mode} ===\n")
    if a.json:
        report("custom input", pd.DataFrame([json.loads(a.json)])[cols], pipe)
    elif a.row is not None:
        r = df.iloc[[a.row]]
        report(f"dataset row {a.row} (actual G3 = {int(r.G3.iloc[0])})", r[cols], pipe)
    else:
        base = df[cols].iloc[0].to_dict()
        for label, upd in (("A – steady performer", dict(G1=14, G2=15, failures=0, absences=2, studytime=3)),
                           ("B – borderline, falling grades", dict(G1=11, G2=9, failures=1, absences=8, studytime=2)),
                           ("C – at risk", dict(G1=6, G2=5, failures=2, absences=14, studytime=1, higher="no"))):
            r = dict(base); r.update({k: v for k, v in upd.items() if k in cols})
            report(label, pd.DataFrame([r])[cols], pipe)
