"""Place the exploratory figure before the stability subsection so it floats near its text,
and flush floats at the end of the appendix so supplementary tables precede the references."""
from pathlib import Path

M = Path(__file__).resolve().parent.parent
p = M / "sections" / "04_results.tex"
s = p.read_text(encoding="utf-8")
start = s.index(r"\begin{figure*}[t]" + "\n" + r"\centering" + "\n"
                + r"\includegraphics[width=\textwidth]{figures/fig8_generalisation.pdf}")
end = s.index(r"\end{figure*}", start) + len(r"\end{figure*}") + 1
fig = s[start:end]
s = s[:start] + s[end:]
anchor = r"\subsection{Stability of the ranking across people}"
s = s.replace(anchor, fig.replace("[t]", "[!t]", 1) + "\n" + anchor)
p.write_text(s, encoding="utf-8")

p = M / "sections" / "07_appendix.tex"
s = p.read_text(encoding="utf-8").rstrip()
if not s.endswith(r"\clearpage"):
    s += "\n" + r"\clearpage"
p.write_text(s + "\n", encoding="utf-8")
print("moved")
