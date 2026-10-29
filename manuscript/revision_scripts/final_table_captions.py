"""Final table-caption pass (2026-09-22): self-contained captions (acronyms spelt out),
'electrode-count performance curve' terminology, cross-document reference to supplementary
table S1, and the rule-derived bipolar threshold. Values are untouched."""
from pathlib import Path

p = Path(__file__).resolve().parents[2] / "scripts" / "42_generate_tables.py"
s = p.read_text(encoding="utf-8")


def rep(a, b):
    global s
    assert a in s, a[:70]
    s = s.replace(a, b)


rep('"gestures; chance Macro-F1 $\\\\approx$ 0.063). CI: participant cluster bootstrap.",',
    '"gestures; chance Macro-F1 $\\\\approx$ 0.063). CI: 95\\\\% confidence interval from a "\n'
    '          "participant cluster bootstrap. RBF-SVM: support vector machine with a radial basis "\n'
    '          "function kernel.",')
rep('"Sparse sensor curve and non-inferiority (cross-fitted ranking, $\\\\lambda = 0$; 43 "',
    '"Electrode-count performance curve and non-inferiority on GRABMyo (cross-fitted ranking, "\n'
    '          "$\\\\lambda = 0$; 43 "')
rep('"sizes (Table~\\\\ref{tab:h1_holm}).")',
    '"sizes (supplementary table S1). CI: 95\\\\% confidence interval.")')
rep('"are comparable within the table but lower than Table~\\\\ref{tab:sparse_ni}. "',
    '"are comparable within the table but lower than table~\\\\ref{tab:sparse_ni}. SR-CFA: "\n'
    '          "stability-regularised cross-fitted attribution. "')
p.write_text(s, encoding="utf-8")
print("captions updated")
