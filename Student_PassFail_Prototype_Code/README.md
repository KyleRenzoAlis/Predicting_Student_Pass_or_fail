# Predicting Student Pass/Fail in a Semester (ITPD 6 – AI 1 case study)

Prototype that predicts whether a secondary-school student will pass (final grade G3 >= 10 on a 0–20 scale)
using Logistic Regression, Decision Tree and Random Forest, and explains the main factors behind each prediction.

## Setup
    pip install -r requirements.txt

## Run (from the `src/` folder)
    python train_evaluate.py      # 80/20 hold-out evaluation + importance, confusion matrices, fairness check
    python cross_validate.py      # 10x repeated stratified 5-fold CV (numbers reported in the paper)
    python make_figures.py        # regenerates figures in ../outputs
    python predict.py --demo                 # demo: 3 sample students, with mid-term grades
    python predict.py --demo --no-grades     # demo: early-warning mode (background factors only)
    python predict.py --row 17               # predict for one real dataset row
    python predict.py --json '{...}'         # custom student (needs all feature keys; see data header)

## Data
`data/student-mat.csv` (395 students, Mathematics) and `data/student-por.csv` (649 students, Portuguese):
UCI "Student Performance" dataset (Cortez & Silva, 2008; Cortez, 2014). The copies here came from a public GitHub
mirror because the UCI site was unreachable from the build environment – compare them with the official download
(https://doi.org/10.24432/C5TG7T) before final submission.

## Layout
    src/common.py          data loading, pass/fail label, model pipelines
    src/train_evaluate.py  hold-out evaluation
    src/cross_validate.py  repeated cross-validation
    src/predict.py         demo application (CLI)
    src/make_figures.py    figures
    outputs/               results.json, cv_results.json, figures, saved demo output

## Web app (no installation)
`webapp/index.html` is a single file. Double-click it to open it in any browser. It trains the logistic regression
model in the browser and accepts quizzes, activities, practicals, midterm, prefinal and final exam scores plus absences,
in percent (75 passes) or 1.0–5.0 (3.0 passes). `webapp/ml_core.js` is the model code that is embedded in that page.
