"""Fail the build if a result-like number is typed into the manuscript instead of a macro.

Scans main_iop.tex and sections/*.tex (not generated tables, which are produced from
artifacts). Every decimal number must either be a design constant from the frozen plan or Methods
(listed below with its justification) or come from a macro. Anything else is reported.

Also checks that every macro used in the text is defined in results_macros.tex, and that the
macro file is not a draft build.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
M = ROOT / "manuscript"

# design constants: value -> reason (not results)
ALLOWED = {
    "0.05": "prespecified significance level",
    "0.02": "prespecified primary margin", "0.01": "sensitivity margin", "0.03": "sensitivity margin",
    "0.25": "lambda candidate", "0.5": "lambda candidate", "0.1": "XGBoost learning rate",
    "0.8": "XGBoost subsampling", "0.063": "chance level 1/16", "0.083": "chance level 1/12", "0.143": "chance level 1/7 (putEMG)", "4.0": "CC BY-NC licence version", "0.9": "LaTeX float-placement fraction", "0.07": "LaTeX float-placement fraction",
    "1.15": "threshold / median |diff| ratio", "10.35": "mains audit ratio (signal audit report)",
    "0.62": "mains audit ratio (signal audit report)", "2.0": "ring spacing",
    "0.025": "one-sided alpha for Holm-adjusted non-inferiority (plan alpha 0.05 two-sided)",
}


def main():
    files = [M / "main_iop.tex", M / "supplementary_iop.tex"] + sorted((M / "sections").glob("*.tex"))
    macros = set(re.findall(r"\\newcommand\{\\([A-Za-z]+)\}",
                            (M / "generated" / "results_macros.tex").read_text(encoding="utf-8")))
    draft = "DRAFT BUILD" in (M / "generated" / "results_macros.tex").read_text(encoding="utf-8")
    problems = []
    for f in files:
        for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            if line.lstrip().startswith("%"):
                continue
            body = re.sub(r"\\(label|ref|cite|input|includegraphics|url)\{[^}]*\}", "", line)
            for num in re.findall(r"(?<![\w.])\d+\.\d+(?![\w.])", body):
                if num not in ALLOWED:
                    problems.append(f"{f.name}:{i}: literal {num}")
            for mac in re.findall(r"\\([A-Z][A-Za-z]+)", body):
                if (re.match(r"(Full|Curve|Delta|HTwo|HThree|Faith|Stab|CS|DBFive|Bip|Fixed|Redund|"
                             r"KStar|Top|Bottom|Dropped|UOver|Pct|VS|GRABMyo|SVMCalib|XGBvs|SVMvs|"
                             r"FoldTraining|Lambda|Put|LOO|Holm|Margin)", mac) and mac not in macros and mac not in {"Delta"}):
                    problems.append(f"{f.name}:{i}: undefined macro \\{mac}")
    if draft:
        problems.append("results_macros.tex is a DRAFT build")
    out = ROOT / "reports" / "manuscript_number_check.txt"
    out.write_text("\n".join(problems) or "PASS", encoding="utf-8")
    print("\n".join(problems) or "PASS: no untraceable numbers; all macros defined")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
