import json, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, numpy as np
cv = json.load(open("../outputs/cv_results.json")); O = "../outputs/"
models = ["Majority baseline", "Logistic Regression", "Decision Tree", "Random Forest"]
fig, axs = plt.subplots(1, 2, figsize=(7.2, 3.4), sharey=True)
for ax, scen, t in zip(axs, ["A_background_only", "B_with_midterm_grades"], ["Scenario A: background only", "Scenario B: + mid-term grades"]):
    acc = [cv[f"Mathematics|{scen}|{m}"]["accuracy"] for m in models]
    ax.bar(range(4), [a[0] for a in acc], yerr=[a[1] for a in acc], color=["#999", "#2f6f9f", "#5b9bd5", "#1b4f72"], capsize=3)
    ax.set_xticks(range(4)); ax.set_xticklabels(["Baseline", "LogReg", "Tree", "Forest"], fontsize=8)
    ax.set_title(t, fontsize=9); ax.set_ylim(0.5, 1.0)
    for i, a in enumerate(acc): ax.text(i, a[0] + a[1] + .008, f"{a[0]:.3f}", ha="center", fontsize=7)
axs[0].set_ylabel("Accuracy (10×5-fold CV, mean ± SD)")
fig.tight_layout(); fig.savefig(O + "fig_accuracy_compare.png", dpi=200)
for name in ("demo_with_grades", "demo_no_grades"):
    txt = open(O + name + ".txt").read().rstrip()
    n = txt.count("\n") + 1
    fig = plt.figure(figsize=(8.2, 0.19 * n + 0.4)); fig.patch.set_facecolor("#1e1e1e")
    fig.text(0.01, 0.99, txt, family="monospace", fontsize=6.6, color="#e6e6e6", va="top")
    fig.savefig(O + f"fig_terminal_{name}.png", dpi=200, facecolor="#1e1e1e", bbox_inches="tight", pad_inches=0.15); plt.close(fig)
