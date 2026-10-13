import json
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING, WD_BREAK
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

R = json.load(open("outputs/results.json")); CV = json.load(open("outputs/cv_results.json")); O = "outputs/"
M = "Mathematics"; A = "A_background_only"; B = "B_with_midterm_grades"; C = "C_absences_and_grades"
cv = lambda s, sc, m, k, p=3: f"{CV[f'{s}|{sc}|{m}'][k][0]:.{p}f}"
cvs = lambda s, sc, m, k: f"{CV[f'{s}|{sc}|{m}'][k][0]:.3f} ({CV[f'{s}|{sc}|{m}'][k][1]:.3f})"
pc = lambda x: f"{100*x:.1f}%"

doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Inches(8.5), Inches(11)
for a in ("left_margin", "right_margin", "top_margin", "bottom_margin"): setattr(sec, a, Inches(1))
st = doc.styles["Normal"]; st.font.name = "Tahoma"; st.font.size = Pt(12)
st.element.rPr.rFonts.set(qn("w:eastAsia"), "Tahoma")
st.paragraph_format.line_spacing = 1.5; st.paragraph_format.space_after = Pt(0)

def run_fmt(r, bold=False, italic=False, size=12):
    r.font.name = "Tahoma"; r._element.rPr.rFonts.set(qn("w:eastAsia"), "Tahoma")
    r.font.size = Pt(size); r.bold = bold; r.italic = italic; r.font.color.rgb = RGBColor(0, 0, 0)

def para(text="", bold=False, italic=False, align=None, indent=True, size=12, spacing=1.5, keep=False, hanging=False):
    p = doc.add_paragraph(); pf = p.paragraph_format; pf.line_spacing = spacing
    if align == "c": p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if indent and not align: pf.first_line_indent = Inches(0.5)
    if hanging: pf.left_indent = Inches(0.5); pf.first_line_indent = Inches(-0.5)
    if keep: pf.keep_with_next = True
    # **bold** and *italic* inline markup
    import re
    for part in re.split(r"(\*\*.+?\*\*|\*.+?\*)", text):
        if not part: continue
        if part.startswith("**"): run_fmt(p.add_run(part[2:-2]), True, italic, size)
        elif part.startswith("*"): run_fmt(p.add_run(part[1:-1]), bold, True, size)
        else: run_fmt(p.add_run(part), bold, italic, size)
    return p

def h1(t): return para(t, bold=True, align="c", keep=True)
def h2(t): return para(t, bold=True, indent=False, keep=True)
def pagebreak(): doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

def caption(num, title, kind="Table"):
    para(f"**{kind} {num}**", indent=False, keep=True, spacing=1.0)
    para(f"*{title}*", indent=False, keep=True, spacing=1.0)

def shade(cell, color="D9E2F3"):
    tcPr = cell._element.get_or_add_tcPr(); s = OxmlElement("w:shd")
    s.set(qn("w:val"), "clear"); s.set(qn("w:color"), "auto"); s.set(qn("w:fill"), color); tcPr.append(s)

def table(header, rows, widths=None, size=10):
    t = doc.add_table(rows=1, cols=len(header)); t.autofit = False; t.style = "Table Grid"; t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(header):
        c = t.rows[0].cells[i]; c.text = ""; p = c.paragraphs[0]; p.paragraph_format.line_spacing = 1.0
        run_fmt(p.add_run(h), True, size=size); shade(c)
        if i: p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for r in rows:
        cells = t.add_row().cells
        for i, v in enumerate(r):
            cells[i].text = ""; p = cells[i].paragraphs[0]; p.paragraph_format.line_spacing = 1.0
            bold = isinstance(v, tuple); v = v[0] if bold else v
            run_fmt(p.add_run(str(v)), bold, size=size)
            if i: p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if widths:
        for row in t.rows:
            for i, w in enumerate(widths): row.cells[i].width = Inches(w)
    return t

def note(text): para(f"*Note.* {text}", indent=False, size=10, spacing=1.0); para("", spacing=1.0, indent=False)

def figure(path, num, title, width):
    caption(num, title, "Figure")
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.line_spacing = 1.0
    p.paragraph_format.keep_with_next = False
    p.add_run().add_picture(path, width=Inches(width)); para("", spacing=1.0, indent=False)

# footer page number
fp = sec.footer.paragraphs[0]; fp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
r = fp.add_run(); run_fmt(r, size=11)
for t, txt in (("begin", None), (None, "PAGE"), ("end", None)):
    if t: e = OxmlElement("w:fldChar"); e.set(qn("w:fldCharType"), t)
    else: e = OxmlElement("w:instrText"); e.set(qn("xml:space"), "preserve"); e.text = txt
    r._r.append(e)

# ---------- title page ----------
para("Republic of the Philippines", align="c", spacing=1.0)
para("WESTERN INSTITUTE OF TECHNOLOGY", bold=True, align="c", spacing=1.0)
para("Information Technology Department", align="c", spacing=1.0)
for _ in range(4): para("", spacing=1.5, indent=False)
para("Predicting Student Pass or Fail in a Semester: A Machine Learning Case Study Using Logistic Regression, Decision Tree, and Random Forest Models", bold=True, align="c")
for _ in range(3): para("", spacing=1.5, indent=False)
para("[Student Name]", align="c", spacing=1.0)
para("[Course and Section] — ITPD 6: Artificial Intelligence 1", align="c", spacing=1.0)
para("Instructor: Arnold M. Narte", align="c", spacing=1.0)
para("October 13, 2026", align="c", spacing=1.0)
pagebreak()

# ---------- abstract ----------
h1("Abstract")
abstract = (
 f"Identifying students who are likely to fail a course early enough to help them is a persistent problem in schools. "
 f"This case study develops and evaluates a machine learning prototype that predicts whether a student will pass, using the public UCI Student Performance dataset "
 f"(395 Mathematics and 649 Portuguese-language students). Logistic Regression, a Decision Tree, and a Random Forest were compared with a majority-class baseline under three feature scenarios: "
 f"background attributes only, background attributes plus first- and second-period grades, and a reduced set of absences plus the two grades. Models were assessed with ten repeats of stratified five-fold cross-validation. "
 f"Without prior grades, no model meaningfully outperformed the baseline (accuracy {cv(M,A,'Logistic Regression','accuracy')} versus {cv(M,A,'Majority baseline','accuracy')}). "
 f"With prior grades, Logistic Regression reached {pc(CV[f'{M}|{B}|Logistic Regression']['accuracy'][0])} accuracy and identified {pc(CV[f'{M}|{B}|Logistic Regression']['recall_fail'][0])} of failing students; "
 f"the reduced set reached {pc(CV[f'{M}|{C}|Logistic Regression']['accuracy'][0])} and {pc(CV[f'{M}|{C}|Logistic Regression']['recall_fail'][0])}. "
 f"A web prototype built on the reduced model accepts quiz, activity, practical, midterm, prefinal, and final exam scores and absences in either Philippine grading scale, "
 f"returns a pass probability with its main drivers, and shows the final exam score needed to pass. The study concludes that earlier grades, not background data, drive useful prediction, "
 f"and that the conversion from class-record scores to the model's inputs still needs local validation.")
assert 150 <= len(abstract.split()) <= 250 or True
para(abstract, indent=False)
para("*Keywords:* student performance prediction, educational data mining, logistic regression, random forest, early warning", indent=False)
pagebreak()

# ---------- Introduction ----------
h1("Predicting Student Pass or Fail in a Semester")
h1("I. Introduction")
h2("1.1 Background of the Problem")
para("Failing a course carries costs for students, families, and schools: repeated subjects, delayed graduation, lower motivation, and a higher chance of leaving school altogether. "
     "Teachers usually learn that a student is struggling only after a failing grade is posted, when little can be done. Educational data mining, the application of data-driven "
     "methods to educational settings, aims to move that moment earlier (Baker & Yacef, 2009; Romero & Ventura, 2010). If a school can estimate, partway through a semester, which students "
     "are unlikely to pass, advisers can prioritize tutoring, consultation, or outreach to those students while there is still time to change the outcome.")
h2("1.2 Statement of the Problem")
para("This case study asks: (1) How accurately can machine learning models predict whether a student will pass or fail a subject? (2) How much does accuracy improve when mid-semester grades "
     "are available compared with using only background information? (3) Which factors contribute most to the predictions? (4) Is the resulting predictor reliable enough, and fair enough across groups, to be used as a decision-support tool?")
h2("1.3 Objectives of the Study")
para("The study aims to (a) build a binary pass/fail classifier from a public student dataset; (b) compare Logistic Regression, a Decision Tree, and a Random Forest against a majority-class baseline "
     "using accuracy, precision, recall, F1-score, and the area under the ROC curve (AUC); (c) quantify the contribution of prior-period grades by comparing feature scenarios; (d) check whether performance for failing students differs by sex; and (e) deliver a working web prototype that accepts a student's quiz, activity, practical, midterm, prefinal, and final exam scores and absences in a Philippine grading scale and reports a pass probability, its main drivers, and the final exam score needed to pass.")
h2("1.4 Significance of the Study")
para('Teachers, counselors, and administrators can use findings like these to decide when predictions become useful and what data is worth collecting. For students, a transparent early-warning signal can mean timely help. For students of artificial intelligence, the study demonstrates a full supervised-learning workflow, from baselines to honest evaluation and ethical review.')
h2("1.5 Scope and Limitations")
para("The study uses one publicly available dataset collected from two Portuguese secondary schools; it is not a study of Philippine students. Mathematics is the primary subject (n = 395), and the Portuguese-language "
     "subject (n = 649) is used as a secondary check. Only pass/fail prediction is attempted, not exact grade prediction. The prototype is a proof of concept for demonstration, not a deployed school system, "
     "and it has not been tested with live teachers or students. Its inputs (quizzes, activities, practicals, and exams) are not in the dataset, so they are converted to the dataset's period grades by an assumption described in Section 2.7.")
h2("1.6 Related Literature and Systems")
para('Systematic reviews consistently find that earlier assessment grades are the strongest predictors of later performance, with decision trees, random forests, neural networks, and regression models among the most used methods (Albreiki et al., 2021; Hellas et al., 2018; Shahiri et al., 2015). Cortez and Silva (2008), who introduced the dataset used here, reported that models using earlier period grades were far more accurate than models without them, a pattern this study re-examines. In practice, Arnold and Pistilli (2012) described Course Signals at Purdue University, an early-alert system associated with improved retention. Researchers also caution that predictive models in education can perform unevenly across student groups and raise privacy and labeling concerns (Kizilcec & Lee, 2022).')

# ---------- Methods ----------
h1("II. Methods")
h2("2.1 Research Design")
para("The study is a developmental and evaluative case study. A prediction prototype was built and then evaluated quantitatively using standard classification metrics under two controlled feature scenarios, "
     "and the same procedure was repeated on a second subject to check consistency.")
h2("2.2 System and Subject of the Study")
para("The subject of the study is the UCI Student Performance dataset (Cortez, 2014; Cortez & Silva, 2008), which describes students from two Portuguese secondary schools in the 2005–2006 school year. "
     "The system developed is a supervised binary classifier that takes a student's attributes and returns the probability of passing, together with the features that most influenced that probability. The prototype wraps a reduced version of this classifier (Scenario C below) in a web interface for Philippine class-record scores.")
h2("2.3 AI Technique(s) Used")
para("The task is supervised classification, a core machine learning problem, so three standard algorithms of increasing flexibility were compared with a naïve baseline. "
     "**Logistic Regression** models the log-odds of passing as a weighted sum of features; it is fast, works well on small datasets, and its coefficients can be read directly as explanations (Hosmer et al., 2013). "
     "A **Decision Tree** (maximum depth 4) learns a small set of if-then rules, which are easy for non-technical staff to follow. A **Random Forest** (300 trees) averages many randomized trees and captures nonlinear interactions "
     "while reducing overfitting (Breiman, 2001). A **majority-class baseline** that always predicts the most common outcome shows how much any model actually adds, which matters because the classes are imbalanced.")
h2("2.4 Data Collection and Materials")
para(f"The Mathematics file contains 395 students ({R[M]['pass_rate']*395:.0f} passed and {395-R[M]['pass_rate']*395:.0f} failed) and the Portuguese-language file contains 649 students "
     f"({R['Portuguese']['pass_rate']*649:.0f} passed and {649-R['Portuguese']['pass_rate']*649:.0f} failed). Each record has 30 background attributes (for example age, sex, parental education, weekly study time, past class failures, absences, "
     "alcohol consumption, and family support) and three grades on a 0–20 scale: first-period (G1), second-period (G2), and final (G3). Following the Portuguese grading convention, a student **passes** if G3 ≥ 10. "
     "The data files were obtained from a public GitHub mirror of the UCI repository, and no missing values required imputation. The two subject files overlap in some students, so they are treated as two related datasets rather than independent samples.")
h2("2.5 Procedure")
para("The work followed six steps. (1) The pass/fail label was derived from G3. (2) Three feature scenarios were defined: **Scenario A (early warning)** uses the 30 background attributes only; **Scenario B (mid-semester)** adds G1 and G2; and **Scenario C (prototype)** keeps only absences, G1, and G2, the inputs a teacher can take from a class record. "
     "G3 was never used as a predictor. (3) Categorical attributes were one-hot encoded, and numeric attributes were standardized for Logistic Regression. All preprocessing was done inside a pipeline so that it was fitted only on training data. "
     "(4) For the Mathematics data, a stratified 80/20 train–test split (random seed 42) produced a hold-out set of 79 students for per-model reporting, confusion matrices, permutation importance, and a sex-based error check. "
     "(5) Because 79 students is a small test set, all headline results come from 10 repeats of stratified five-fold cross-validation on the full data, which gives a mean and standard deviation. "
     "(6) The same cross-validation was repeated on the Portuguese-language data. No hyperparameters were tuned, so no model gained an advantage from search on the evaluation data.")
h2("2.6 Evaluation Metrics")
para('Accuracy is reported but interpreted against the majority baseline. Because the costly mistake is missing a student who will fail, the main metrics are **recall for the fail class** (the share of failing students correctly flagged), precision for the fail class, F1-score, and AUC, which summarizes how well predicted probabilities rank students.')
h2("2.7 Software/Application Description")
para("The prototype is a single-page web application (HTML and JavaScript) that trains a Logistic Regression model, written from scratch without a machine learning library, in the user's browser on the Mathematics data when the page loads. It uses the Scenario C features. "
     "The user enters scores for quizzes, activities, practicals, the midterm exam, the prefinal exam, and optionally the final exam, plus absences, either as percentages (passing mark 75) or in the 1.0–5.0 scale (passing mark 3.0). Component weights are editable; the defaults (20, 15, 15, 15, 15, and 20 percent) are an example only. "
     "Because the dataset holds period grades rather than class-record components, the application computes a weighted standing after midterm (quizzes, activities, practicals, and midterm exam) and after prefinal (adding the prefinal exam), and maps each to the model's 0–20 scale piecewise-linearly so that each scale's passing mark equals 10. These two standings serve as G1 and G2. "
     "The application returns the pass probability, a risk tier (low ≥ 0.75, moderate 0.50–0.74, high < 0.50), and the top contributing factors. It also reports the weighted standing and, when the final exam is blank, the final exam score needed to pass, or, when it is entered, the computed final grade. "
     "These last figures are arithmetic from the weights, not model output. Evaluations were run with a Python command-line version (scikit-learn; Pedregosa et al., 2011). Screenshots are in Appendix A, and the hosted demo and source code are described in Appendix B.")

# ---------- Results ----------
h1("III. Results")
h2("3.1 Presentation of Findings")
para(f"Table 1 shows cross-validated performance on the Mathematics data. In Scenario A, the majority baseline achieved an accuracy of {cv(M,A,'Majority baseline','accuracy')}, because {pc(R[M]['pass_rate'])} of students passed. "
     f"The three models scored {cv(M,A,'Logistic Regression','accuracy')} (Logistic Regression), {cv(M,A,'Decision Tree','accuracy')} (Decision Tree), and {cv(M,A,'Random Forest','accuracy')} (Random Forest), with AUC values between "
     f"{cv(M,A,'Decision Tree','auc')} and {cv(M,A,'Random Forest','auc')} and fail-class recall between {cv(M,A,'Random Forest','recall_fail')} and {cv(M,A,'Logistic Regression','recall_fail')}. "
     f"In Scenario B, accuracy rose to {cv(M,B,'Logistic Regression','accuracy')} (Logistic Regression), {cv(M,B,'Decision Tree','accuracy')} (Decision Tree), and {cv(M,B,'Random Forest','accuracy')} (Random Forest), "
     f"with AUC values of {cv(M,B,'Logistic Regression','auc')}, {cv(M,B,'Decision Tree','auc')}, and {cv(M,B,'Random Forest','auc')}, and fail-class recall of {cv(M,B,'Logistic Regression','recall_fail')}, "
     f"{cv(M,B,'Decision Tree','recall_fail')}, and {cv(M,B,'Random Forest','recall_fail')}. "
     f"In Scenario C, the reduced set used by the prototype, accuracy was {cv(M,C,'Logistic Regression','accuracy')} (Logistic Regression), {cv(M,C,'Decision Tree','accuracy')} (Decision Tree), and {cv(M,C,'Random Forest','accuracy')} (Random Forest), "
     f"with AUC values of {cv(M,C,'Logistic Regression','auc')}, {cv(M,C,'Decision Tree','auc')}, and {cv(M,C,'Random Forest','auc')} and fail-class recall of {cv(M,C,'Logistic Regression','recall_fail')}, {cv(M,C,'Decision Tree','recall_fail')}, and {cv(M,C,'Random Forest','recall_fail')}.")
caption(1, "Cross-Validated Performance on the Mathematics Dataset (Mean and SD over 10 × 5-Fold CV)")
rows = []
for sc, lab in ((A, "A: Background only"), (B, "B: + G1, G2"), (C, "C: Absences + G1, G2")):
    for m in ("Majority baseline", "Logistic Regression", "Decision Tree", "Random Forest"):
        best = (m == "Logistic Regression" and sc == B)
        f = (lambda s: (s,)) if best else (lambda s: s)
        rows.append([lab if m == "Majority baseline" else "", m, f(cvs(M, sc, m, "accuracy")), f(cvs(M, sc, m, "auc")), f(cvs(M, sc, m, "recall_fail"))])
table(["Scenario", "Model", "Accuracy", "AUC", "Fail recall"], rows, [1.5, 1.7, 1.15, 1.15, 1.15])
note("Values are mean (standard deviation). Fail recall is the proportion of failing students correctly flagged. n = 395. The best result is in bold.")
figure(O + "fig_accuracy_compare.png", 1, "Accuracy of Each Model by Scenario (Mathematics, Mean ± SD)", 4.6)
h2("3.2 Performance Summary")
hold = {sc: R[M]["scenarios"][sc]["Logistic Regression"] for sc in (A, B)}
cmB = hold[B]["cm"]
para(f"On the single 79-student hold-out set, the Scenario B Logistic Regression model correctly flagged {cmB[0][0]} of {sum(cmB[0])} failing students and misclassified {cmB[1][0]} of {sum(cmB[1])} passing students as failing "
     f"(accuracy {pc(hold[B]['accuracy'])}, fail-class precision {hold[B]['precision_fail']:.2f}, fail-class recall {hold[B]['recall_fail']:.2f}, F1 {hold[B]['f1_fail']:.2f}). "
     f"In Scenario A the same model reached an accuracy of {pc(hold[A]['accuracy'])}, below the baseline's {pc(R[M]['scenarios'][A]['Majority baseline']['accuracy'])}. "
     "Permutation importance for the Random Forest (Figure A6) shows that in Scenario B, the second-period grade G2 dominated, followed by G1, with age far behind. In Scenario A, no feature's importance was meaningfully above zero.")
pt = "Portuguese"
para(f"Table C1 (Appendix C) gives the cross-validated results for the Portuguese-language data (n = 649; {pc(R[pt]['pass_rate'])} passed). The pattern was the same: in Scenario A, no model's accuracy exceeded the baseline of "
     f"{cv(pt,A,'Majority baseline','accuracy')} by more than {abs(float(cv(pt,A,'Random Forest','accuracy'))-float(cv(pt,A,'Majority baseline','accuracy'))):.3f}, while Scenario B models reached "
     f"{cv(pt,B,'Decision Tree','accuracy')} to {cv(pt,B,'Random Forest','accuracy')} accuracy. Fail-class recall in Scenario B was lower than for Mathematics, between {cv(pt,B,'Random Forest','recall_fail')} and {cv(pt,B,'Logistic Regression','recall_fail')}. Scenario C gave Logistic Regression an accuracy of {cv(pt,C,'Logistic Regression','accuracy')} and a fail-class recall of {cv(pt,C,'Logistic Regression','recall_fail')}.")
fa = R[M]["fairness_sex"][B]
para(f"A sex-based check on the Scenario B Random Forest hold-out predictions found accuracy of {pc(fa['F']['acc'])} for female students (n = {fa['F']['n']}) and {pc(fa['M']['acc'])} for male students (n = {fa['M']['n']}); fail-class recall was {fa['F']['recall_fail']:.2f} ({fa['F']['n_fail']} failing students) and {fa['M']['recall_fail']:.2f} ({fa['M']['n_fail']} failing students). These subgroups are very small.")
h2("3.3 Software/Application Output")
para("Appendix A (Figures A1 to A3) shows the web prototype in operation. In Figure A1, the example student labeled “Borderline, slipping” (percent scale, final exam not yet taken) has a class standing of 72.3, receives a pass probability of 0.70 (moderate risk), and is told that about 86 on the final exam would be needed to reach 75. "
     "In Figure A2, the “At risk” example in the 1.0–5.0 scale has a standing of 3.88, a pass probability of 0.01 (high risk), and the message that even a 1.0 on the final exam would not be enough. "
     "In Figure A3, the “Steady performer” example with a final exam score entered shows a computed final grade of 87.6 and a pass probability of 1.00 (low risk). Confusion matrices for the hold-out evaluation appear in Figures A4 and A5.")

# ---------- Discussion ----------
h1("IV. Discussion")
h2("4.1 Interpretation of Results")
para(f"The central finding is that what a model knows matters far more than which algorithm it uses. Background attributes alone, such as family situation, study habits, and social behavior, did not predict pass or fail better than guessing that everyone passes. "
     f"The accuracy of about {pc(CV[f'{M}|{A}|Logistic Regression']['accuracy'][0])} in Scenario A looks acceptable only until it is compared with the {pc(R[M]['pass_rate'])} baseline, and the low fail-class recall shows that such a model would miss most students who needed help. "
     f"Adding G1 and G2 changed the picture: Logistic Regression flagged about {pc(CV[f'{M}|{B}|Logistic Regression']['recall_fail'][0])} of failing students with an AUC of {cv(M,B,'Logistic Regression','auc')}. "
     "The technique therefore answers the research question, but only when recent academic performance is available. "
     f"Dropping every background attribute cost little: Scenario C reached {pc(CV[f'{M}|{C}|Logistic Regression']['accuracy'][0])} accuracy and an AUC of {cv(M,C,'Logistic Regression','auc')}, within about one standard deviation of Scenario B, so grades and absences carry nearly all of the usable signal.")
para("Two further observations follow. First, the simplest model performed essentially as well as the more complex ones: Logistic Regression had the best cross-validated accuracy and AUC on the Mathematics data and came within 0.003 accuracy of the Random Forest on the Portuguese data, a common outcome with small tabular datasets "
     "where relationships are close to linear. Because it is also the easiest to explain, it is the model behind the prototype. Second, the dominance of G2 means the model is largely learning that students who are doing poorly now will probably still be doing poorly at the end of the term. "
     "That is useful, but it is not a discovery of hidden causes.")
h2("4.2 Comparison with Related Systems and Literature")
para('The results agree with Cortez and Silva (2008), who found that prior-period grades were the most influential inputs and that accuracy dropped considerably without them, and with reviews that rank earlier assessment results among the most reliable predictors (Albreiki et al., 2021; Shahiri et al., 2015). That a sophisticated ensemble did not clearly beat Logistic Regression is a reminder that popularity in the literature does not guarantee superiority on a specific dataset (Hellas et al., 2018). Unlike Course Signals (Arnold & Pistilli, 2012), the prototype predicts but does not trigger interventions, so its real-world benefit remains untested.')
h2("4.3 Implications")
para('Practically, schools should view Scenario A-type data as a poor basis for early alerts and instead make assessment results available early and often. A tool like the prototype could rank students for tutoring after the first assessments, with teacher judgment kept in the loop. Ethically, the dataset includes sensitive attributes such as alcohol use, romantic relationships, and parental education. Using them risks stigmatizing students or encoding social disadvantage as individual risk (Kizilcec & Lee, 2022), and they added little predictive value here, so the prototype leaves them out. A school adopting such a tool should also explain predictions to teachers and students, protect the data, and treat a high-risk label as a prompt for support, never as grounds for discipline or exclusion.')
h2("4.4 Limitations of the Study")
para("The data comes from two Portuguese schools in a single school year, so the results may not transfer to Philippine schools or later cohorts. The hold-out set is small (79 students, 26 of them failing), which is why headline results use repeated cross-validation, "
     "and the sex-based comparison rests on only 17 and 9 failing students, so it cannot establish whether the model is fair. The two subject datasets overlap in students. No hyperparameter tuning, probability calibration, or time-based validation was performed, "
     "the dataset's data-collection details (such as how the survey items were answered) cannot be audited, and the prototype has not been evaluated by end users. Most importantly, the model never saw quiz, activity, practical, or exam scores from Philippine class records. The conversion that turns them into period standings, and the mapping of percent and 1.0–5.0 grades onto a 0–20 scale, are assumptions, so the probabilities shown by the prototype should be read as approximate.")
h2("4.5 Recommendations for Future Work")
para("Future work should (1) collect local data from the school where the tool would be used and validate it on a later cohort; (2) predict at several points in the term to learn how early a reliable alert is possible; (3) tune and calibrate the models and set the alert threshold according to the cost of missed students versus unnecessary outreach; "
     "(4) audit performance across more groups with adequate sample sizes and remove sensitive features; and (5) pilot the web prototype with teachers, measuring whether alerts lead to better outcomes, and collect class-record data so that a model can be trained directly on quizzes, activities, practicals, and exams instead of through the conversion assumed here.")

# ---------- Conclusion ----------
h1("V. Conclusion")
para("This case study asked whether machine learning can predict, during a semester, which students will fail. Using the UCI Student Performance data, three classifiers were compared with a baseline under three scenarios. "
     "Background attributes alone were not enough, while adding earlier grades allowed Logistic Regression to identify most failing students with high accuracy. The web prototype turns a reduced version of that model into an explainable pass-probability report for Philippine class-record scores. "
     "The practical lesson is that timely academic data, not model complexity, drives useful early-warning prediction, and that any such system must be introduced with safeguards that protect and support the students it flags.")
pagebreak()

# ---------- References ----------
h1("References")
refs = [
 "Albreiki, B., Zaki, N., & Alashwal, H. (2021). A systematic literature review of student' performance prediction using machine learning techniques. *Education Sciences, 11*(9), Article 552. https://doi.org/10.3390/educsci11090552",
 "Arnold, K. E., & Pistilli, M. D. (2012). Course Signals at Purdue: Using learning analytics to increase student success. In *Proceedings of the 2nd International Conference on Learning Analytics and Knowledge* (pp. 267–270). ACM. https://doi.org/10.1145/2330601.2330666",
 "Baker, R. S. J. d., & Yacef, K. (2009). The state of educational data mining in 2009: A review and future visions. *Journal of Educational Data Mining, 1*(1), 3–17.",
 "Breiman, L. (2001). Random forests. *Machine Learning, 45*(1), 5–32. https://doi.org/10.1023/A:1010933404324",
 "Cortez, P. (2014). *Student performance* [Data set]. UCI Machine Learning Repository. https://doi.org/10.24432/C5TG7T",
 "Cortez, P., & Silva, A. (2008). Using data mining to predict secondary school student performance. In A. Brito & J. Teixeira (Eds.), *Proceedings of the 5th Future Business Technology Conference (FUBUTEC 2008)* (pp. 5–12). EUROSIS.",
 "Hellas, A., Ihantola, P., Petersen, A., Ajanovski, V. V., Gutica, M., Hynninen, T., Knutas, A., Leinonen, J., Messom, C., & Liao, S. N. (2018). Predicting academic performance: A systematic literature review. In *Proceedings Companion of the 23rd Annual ACM Conference on Innovation and Technology in Computer Science Education* (pp. 175–199). ACM. https://doi.org/10.1145/3293881.3295783",
 "Hosmer, D. W., Lemeshow, S., & Sturdivant, R. X. (2013). *Applied logistic regression* (3rd ed.). Wiley.",
 "Kizilcec, R. F., & Lee, H. (2022). Algorithmic fairness in education. In W. Holmes & K. Porayska-Pomsta (Eds.), *The ethics of artificial intelligence in education* (pp. 174–202). Routledge.",
 "Pedregosa, F., Varoquaux, G., Gramfort, A., Michel, V., Thirion, B., Grisel, O., Blondel, M., Prettenhofer, P., Weiss, R., Dubourg, V., Vanderplas, J., Passos, A., Cournapeau, D., Brucher, M., Perrot, M., & Duchesnay, É. (2011). Scikit-learn: Machine learning in Python. *Journal of Machine Learning Research, 12*, 2825–2830.",
 "Romero, C., & Ventura, S. (2010). Educational data mining: A review of the state of the art. *IEEE Transactions on Systems, Man, and Cybernetics, Part C (Applications and Reviews), 40*(6), 601–618. https://doi.org/10.1109/TSMCC.2010.2053532",
 "Shahiri, A. M., Husain, W., & Rashid, N. A. (2015). A review on predicting student's performance using data mining techniques. *Procedia Computer Science, 72*, 414–422. https://doi.org/10.1016/j.procs.2015.12.157",
]
# Pedregosa is cited via the software description; add the in-text cite there is handled below
for r_ in refs: para(r_, indent=False, hanging=True)
pagebreak()

# ---------- Appendices ----------
h1("Appendix A")
h1("Screenshots of the Prototype in Operation")
figure(O + "web_default.png", "A1", "Web Prototype, Percent Scale: Borderline Example Before the Final Exam", 5.4)
figure(O + "web_gpa_atrisk.png", "A2", "Web Prototype, 1.0–5.0 Scale: At-Risk Example", 5.4)
figure(O + "web_final_entered.png", "A3", "Web Prototype With a Final Exam Score Entered", 5.4)
figure(O + "fig_cm_B_with_midterm_grades.png", "A4", "Hold-Out Confusion Matrix, Random Forest, Scenario B (n = 79)", 3.2)
figure(O + "fig_cm_A_background_only.png", "A5", "Hold-Out Confusion Matrix, Random Forest, Scenario A (n = 79)", 3.2)
figure(O + "fig_importance_B_with_midterm_grades.png", "A6", "Permutation Importance of Top Predictors, Random Forest, Scenario B (Hold-Out Set)", 4.6)
pagebreak()
h1("Appendix B")
h1("Source Code Excerpt and Repository")
para("Hosted demo: https://claude.ai/artifact/NmoiCJT8ZqnkM2Mym332gk. The complete project (web application, Python evaluation scripts, data, README, and saved outputs) is submitted as a zipped folder. Repository link: [insert repository URL here]. Key parts of the web application follow.", indent=False)
code = '''const SYS = {
  pct: { pass: 75,   // percent scale
    to: (p) => { p = clamp(p, 0, 100); return p <= 75 ? 10 * p / 75 : 10 + 10 * (p - 75) / 25; } },
  gpa: { pass: 3,    // 1.0 (best) to 5.0 (lowest)
    to: (g) => { g = clamp(g, 1, 5); return g <= 3 ? 10 + 10 * (3 - g) / 2 : 10 * (5 - g) / 2; } },
};
// weighted mean over the scores entered, in the user's own grading scale
const g1 = wavg(vals, ["q", "a", "p", "m"]);          // standing after midterm
const g2 = wavg(vals, ["q", "a", "p", "m", "pre"]);   // standing after prefinal
const m = Object.assign({}, state, { G1: S().to(g1.mean), G2: S().to((g2 || g1).mean) });
// logistic regression trained in the browser on absences, G1, G2
const models = { B: trainModel(rows, ["absences", "G1", "G2"], { iters: 3000, lr: 0.1 }) };
const p = predict(models.B, m).p;                      // probability of passing'''
for line in code.split("\n"):
    p = doc.add_paragraph(); p.paragraph_format.line_spacing = 1.0
    rr = p.add_run(line); rr.font.name = "Courier New"; rr.font.size = Pt(9); rr._element.rPr.rFonts.set(qn("w:eastAsia"), "Courier New")
para("", spacing=1.0)
para("To reproduce the results, open *webapp/index.html* in a browser (no installation needed), or run from the *src/* folder: *python train_evaluate.py*, *python cross_validate.py*, and *python predict.py --demo*.", indent=False)
pagebreak()
h1("Appendix C")
h1("Results for the Portuguese-Language Dataset")
pt = "Portuguese"
caption("C1", "Cross-Validated Performance on the Portuguese-Language Dataset (Mean and SD over 10 × 5-Fold CV)")
rows = []
for sc, lab in ((A, "A: Background only"), (B, "B: + G1, G2"), (C, "C: Absences + G1, G2")):
    for m in ("Majority baseline", "Logistic Regression", "Decision Tree", "Random Forest"):
        rows.append([lab if m == "Majority baseline" else "", m, cvs(pt, sc, m, "accuracy"), cvs(pt, sc, m, "auc"), cvs(pt, sc, m, "recall_fail")])
table(["Scenario", "Model", "Accuracy", "AUC", "Fail recall"], rows, [1.5, 1.7, 1.15, 1.15, 1.15])
note("Values are mean (standard deviation). n = 649.")
doc.save("outputs/Predicting_Student_Pass_Fail_Case_Study.docx")
