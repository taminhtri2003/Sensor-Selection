"""Order figures by first citation and make file names match printed numbers (IOP conversion).

1 overview (intro)  2 workflow (methods, now cited)  3 full channel  4 attribution
5 sparse curve  6 selection baselines  7 faithfulness  8 exploratory
"""
import re
from pathlib import Path

M = Path(__file__).resolve().parent.parent
ROOT = M.parent
RENAME = {"fig6_attribution": "fig4_attribution", "fig4_sparse_curve": "fig5_sparse_curve",
          "fig5_selection_baselines": "fig6_selection_baselines"}

# 1. cite the workflow figure in Methods
p = M / "sections" / "03_methods.tex"
s = p.read_text(encoding="utf-8")
old = "\\subsection{Datasets}\n"
new = ("\\rev{Figure~\\ref{fig:workflow} summarises the analysis workflow applied to every "
       "dataset.}\n\n\\subsection{Datasets}\n")
if "Figure~\\ref{fig:workflow}" not in s:
    assert old in s
    s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")

# 2. move the attribution figure to just after the first H1 paragraph, before the curve table
p = M / "sections" / "04_results.tex"
s = p.read_text(encoding="utf-8")
start = s.index("\\begin{figure*}")
blocks = [m.start() for m in re.finditer(r"\\begin\{figure\*\}", s)]
fig = None
for b in blocks:
    e = s.index("\\end{figure*}", b) + len("\\end{figure*}\n")
    if "fig6_attribution" in s[b:e] or "fig4_attribution" in s[b:e]:
        fig = s[b:e]
        s = s[:b] + s[e:]
        break
assert fig is not None
anchor = "Performance declined smoothly as electrodes were removed"
i = s.index(anchor)
s = s[:i] + fig + "\n" + s[i:]
for a, b in RENAME.items():
    s = s.replace(f"figures/{a}.pdf", f"figures/{b}.pdf")
p.write_text(s, encoding="utf-8")

# 3. figure script: new output names
p = ROOT / "scripts" / "44_figures.py"
s = p.read_text(encoding="utf-8")
for a, b in RENAME.items():
    s = s.replace(f'"{a}"', f'"{b}"')
p.write_text(s, encoding="utf-8")

# 4. remove stale files with old names
for a in RENAME:
    for ext in ("pdf", "png"):
        f = M / "figures" / f"{a}.{ext}"
        if f.exists():
            f.unlink()
print("renumbered")
