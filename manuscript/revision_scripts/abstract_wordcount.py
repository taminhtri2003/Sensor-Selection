"""Count abstract words with macros expanded to their values (journal limit 300)."""
import re
from pathlib import Path

M = Path(__file__).resolve().parent.parent
mac = dict(re.findall(r"\\newcommand\{\\(\w+)\}\{([^}]*)\}",
                      (M / "generated/results_macros.tex").read_text(encoding="utf-8")))
s = (M / "main_iop.tex").read_text(encoding="utf-8")
a = s[s.index(r"\begin{abstract}") + len(r"\begin{abstract}"):s.index(r"\end{abstract}")]
a = re.sub(r"\\textit\{([^}]*)\}", r"\1", a)
a = re.sub(r"\\([A-Za-z]+)", lambda m: mac.get(m.group(1), ""), a)
a = re.sub(r"[{}$\\~]", " ", a)
print("abstract words:", len(a.split()))
