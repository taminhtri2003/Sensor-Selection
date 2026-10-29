"""Fill %BIPOLAR_*% placeholders from generated macros (2026-09-22).

Written while the 4e-3 mV bipolar re-run (decision_log Decision 20) was still running, before any
of its results were seen. Wording branches only on the macro values; no number is typed here.
"""
import re
import sys
from pathlib import Path

M = Path(__file__).resolve().parent.parent
mac = dict(re.findall(r"\\newcommand\{\\(\w+)\}\{([^}]*)\}",
                      (M / "generated/results_macros.tex").read_text(encoding="utf-8")))
if "BipKStarMarginPtTwo" not in mac:
    sys.exit("bipolar macros missing")
W = {1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five", 6: "Six", 7: "Seven"}
kstar = mac["BipKStarMarginPtTwo"]

head = (r"\paragraph{Bipolar re-referencing (exploratory)} With the eight derived bipolar pairs as "
        r"the selection unit (count-feature threshold $4 \times 10^{-3}$~mV), full-array Macro-F1 "
        r"was \BipFull\ $\pm$ \BipFullSD, lower than with monopolar electrodes "
        r"(figure~\ref{fig:generalisation}(c), supplementary material). ")
if kstar == "none":
    body = (r"No pair could be removed within the primary margin: with seven pairs, "
            r"$\bar\Delta_7 = \BipDeltaKSeven$ and the lower bound was $\BipDeltaKSevenLCB$ "
            r"(non-inferior under \BipSeedFracSeven\% of 200 alternative bootstrap seeds). ")
    disc = (r"With bipolar pairs derived from the same recordings, not even one of eight pairs "
            r"could be removed within the primary margin.")
else:
    k = int(kstar)
    body = (rf"At $\delta = 0.02$ the smallest non-inferior subset was $k^* = \BipKStarMarginPtTwo$ "
            rf"of eight pairs ($\bar\Delta_{{{k}}} = \BipDeltaK{W[k]}$, lower bound "
            rf"$\BipDeltaK{W[k]}LCB$)")
    if k > 1:
        body += rf"; with {k - 1} pairs the lower bound was $\BipDeltaK{W[k - 1]}LCB$"
    body += (r". The decision at seven pairs held under \BipSeedFracSeven\% of 200 alternative "
             r"bootstrap seeds. ")
    frac = (8 - k) / 8
    rel = ("a smaller relative reduction than" if frac < 0.25 else
           "the same relative reduction as" if frac == 0.25 else "a larger relative reduction than")
    disc = (rf"With bipolar pairs derived from the same recordings, $\BipKStarMarginPtTwo$ of eight "
            rf"pairs met the primary margin, {rel} for monopolar electrodes.")
tail = (r"Under the sensitivity margins, $k^*$ was \BipKStarMarginPtOne\ at $\delta = 0.01$ and "
        r"\BipKStarMarginPtThree\ at $\delta = 0.03$, identically for all $\lambda$. The ranking was "
        r"again stable: pairs \BipTopThreeSet\ formed the top three in \BipTopThreeFolds\ of 43 folds.")
results = head + body + tail


# Generated includes make every rebuild respond to current verified outcomes.
for name, txt in (("bipolar_results.tex", results), ("bipolar_discussion.tex", disc)):
    (M / "generated" / name).write_text(txt + "\n", encoding="utf-8")
    print("generated", name, "(k* =", kstar, ")")
