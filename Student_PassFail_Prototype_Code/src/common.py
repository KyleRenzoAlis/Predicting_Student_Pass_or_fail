"""Shared data loading and model definitions for the pass/fail predictor."""
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.dummy import DummyClassifier

PASS_MARK = 10  # final grade G3 (0-20 scale) >= 10 means "pass"
SEED = 42

def load(path):
    df = pd.read_csv(path, sep=";", quotechar='"')
    for c in ("G1", "G2"):
        df[c] = pd.to_numeric(df[c])
    df["passed"] = (df["G3"] >= PASS_MARK).astype(int)
    return df

def feature_sets(df):
    """Scenario A = early warning (no grades). Scenario B = adds mid-term grades G1, G2."""
    base = [c for c in df.columns if c not in ("G1", "G2", "G3", "passed")]
    return {"A_background_only": base, "B_with_midterm_grades": base + ["G1", "G2"],
            "C_absences_and_grades": ["absences", "G1", "G2"]}  # C = the web prototype's model

def make_model(name, X):
    cat = [c for c in X.columns if not pd.api.types.is_numeric_dtype(X[c])]
    num = [c for c in X.columns if c not in cat]
    scale = StandardScaler() if name == "Logistic Regression" else "passthrough"
    pre = ColumnTransformer([("cat", OneHotEncoder(handle_unknown="ignore"), cat),
                             ("num", scale, num)])
    clf = {
        "Majority baseline": DummyClassifier(strategy="most_frequent"),
        "Logistic Regression": LogisticRegression(max_iter=2000, random_state=SEED),
        "Decision Tree": DecisionTreeClassifier(max_depth=4, random_state=SEED),
        "Random Forest": RandomForestClassifier(n_estimators=300, random_state=SEED),
    }[name]
    return Pipeline([("pre", pre), ("clf", clf)])

MODELS = ["Majority baseline", "Logistic Regression", "Decision Tree", "Random Forest"]
