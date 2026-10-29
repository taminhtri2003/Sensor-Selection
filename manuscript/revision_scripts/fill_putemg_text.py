"""Fill the %PUTEMG_*% placeholders from generated macros (2026-09-21 revision).

Written BEFORE any putEMG result was seen (only one timing fold had run). The wording branches
only on values in results_macros.tex, so the text cannot be tailored to the outcome afterwards.
All numbers stay as macros; this script never inserts a numeric literal.
"""
import re
import sys
from pathlib import Path

M = Path(__file__).resolve().parent.parent
mac = dict(re.findall(r"\\newcommand\{\\(\w+)\}\{([^}]*)\}",
                      (M / "generated/results_macros.tex").read_text(encoding="utf-8")))
if "PutKStarPtTwo" not in mac:
    sys.exit("putEMG macros missing: run scripts/37 put and scripts/40 first")

kstar = mac["PutKStarPtTwo"]
passes = kstar != "none"
holm_same = mac["PutKStarHolmPtTwo"] == kstar
sig = {k: mac[f"PutVsRandK{k}P"].startswith("<") or float(mac[f"PutVsRandK{k}P"].split("=")[1]) < 0.05
       for k in ("Six", "Twelve", "Eighteen")}
pos = {k: mac[f"PutVsRandK{k}Diff"].startswith("+") for k in ("Six", "Twelve", "Eighteen")}

# ---------------- Results paragraph
r = [r"\rev{\paragraph{putEMG (exploratory, added post hoc)}",
     r"With all 24 electrodes, LOSO Macro-F1 over the 44 participants was \PutFull\ (95\% CI "
     r"\PutFullLCB--\PutFullUCB; range \PutFullMin--\PutFullMax; 7 gestures, chance about 0.143)."]
if passes:
    r.append("")
    w = {str(i): n for i, n in enumerate(
        "Zero One Two Three Four Five Six Seven Eight Nine Ten Eleven Twelve Thirteen Fourteen "
        "Fifteen Sixteen Seventeen Eighteen Nineteen Twenty TwentyOne TwentyTwo TwentyThree".split())}
    kw, km1 = w[kstar], w[str(int(kstar) - 1)]
    r[-1] = (r"At $\delta = 0.02$ the smallest non-inferior subset was $k^* = \PutKStarPtTwo$ of 24 "
             rf"electrodes ($\bar\Delta = \PutDeltaK{kw}$, 95\% CI $\PutDeltaK{kw}LCB$ to "
             rf"$\PutDeltaK{kw}UCB$), a reduction of \PutKStarReductionPct\%; at $k = "
             rf"\PutKStarMinusOne$ the lower bound was $\PutDeltaK{km1}LCB$.")
    r.append(r"The passing $k$ values were contiguous up to 23." if mac["PutContiguous"] == "yes"
             else r"The passing $k$ values were not contiguous: some larger $k$ failed the margin.")
    r.append(r"With Holm correction over the 23 tested $k$, $k^* = \PutKStarHolmPtTwo$" +
             (r", unchanged." if holm_same else r".") +
             r" Under 200 alternative bootstrap seeds, $k^*$ was non-inferior in \PutSeedFrac\% of cases.")
else:
    r.append(r"No subset smaller than 24 electrodes was non-inferior at $\delta = 0.02$ "
             r"($k^* = \PutKStarPtTwo$; for example, $k = 18$: $\bar\Delta = \PutDeltaKEighteen$, "
             r"lower bound $\PutDeltaKEighteenLCB$).")
r.append(r"Under the sensitivity margins, $k^*$ was \PutKStarPtOne\ at $\delta = 0.01$ and "
         r"\PutKStarPtThree\ at $\delta = 0.03$ (Fig.~\ref{fig:generalisation}d).")
r.append(r"The mean curve " + (r"increased monotonically with $k$." if mac["PutMonotone"] == "yes"
                               else r"increased broadly with $k$ but was not monotone."))
parts = []
for k, kk in (("Six", 6), ("Twelve", 12), ("Eighteen", 18)):
    parts.append(rf"$k = {kk}$: $\PutVsRandK{k}Diff$ (95\% CI $\PutVsRandK{k}LCB$ to "
                 rf"$\PutVsRandK{k}UCB$), $p_{{\mathrm{{Holm}}}} \PutVsRandK{k}P$")
n_sig_pos = sum(sig[k] and pos[k] for k in sig)
lead = ("Ranked subsets exceeded the mean of ten random subsets at all three sizes tested"
        if n_sig_pos == 3 else
        "Ranked subsets exceeded the mean of ten random subsets at "
        + ", ".join(str(kk) for k, kk in (("Six", 6), ("Twelve", 12), ("Eighteen", 18))
                    if sig[k] and pos[k]) + " electrodes"
        if n_sig_pos else
        "No statistically detectable difference was observed between ranked subsets and the mean "
        "of ten random subsets")
r.append(lead + " (" + "; ".join(parts) + ").")
r.append(r"The modal top four electrodes were \PutTopFourSet\ (\PutTopFourFolds\ of 44 folds); of "
         r"the top-8 positions across folds, \PutTopEightElbowPct\%, \PutTopEightMiddlePct\% and "
         r"\PutTopEightWristPct\% fell in the electrode bands 1--8, 9--16 and 17--24. The top-12 set was "
         r"identical under all four $\lambda$ in \PutTopTwelveLambdaSame\ of 44 folds. Because putEMG "
         r"has a different montage, electrode count and gesture set, only the behaviour of the "
         r"procedure, not the retained fraction, is comparable with GRABMyo.}")
results = " ".join(r)

# ---------------- Abstract sentence
if passes:
    abstract = (r"In an exploratory replication added after the main analysis (putEMG, 44 participants, "
                r"24 electrodes), $k^* = \PutKStarPtTwo$ of 24 at the same margin.")
else:
    abstract = (r"In an exploratory replication added after the main analysis (putEMG, 44 participants, "
                r"24 electrodes), no subset was non-inferior at the same margin.")

# ---------------- Discussion sentence
if passes:
    disc = (r"\rev{On putEMG, a larger cohort with a three-band, 24-electrode montage added after the "
            r"main analysis, the same procedure also found a non-inferior reduction ($k^* = "
            r"\PutKStarPtTwo$ of 24). Because this analysis was post hoc and the montage differs, it "
            r"supports the transferability of the procedure rather than any particular retained "
            r"fraction.}")
else:
    disc = (r"\rev{On putEMG, a larger cohort with a three-band, 24-electrode montage added after the "
            r"main analysis, no electrode could be removed within the same margin. Together with the "
            r"bipolar result, this indicates that the size of a tolerable reduction depends on the "
            r"montage and task.}")

# ---------------- Conclusion clause
concl = (r"In an exploratory, post-hoc replication on putEMG, " +
         (r"$k^* = \PutKStarPtTwo$ of 24 electrodes met the same tolerance."
          if passes else r"no reduction of the 24-electrode array met the same tolerance."))

for f, ph, txt in (("main_elsevier.tex", "%PUTEMG_ABSTRACT%", abstract),
                   ("sections/04_results.tex", "%PUTEMG_RESULTS%", results),
                   ("sections/05_discussion.tex", "%PUTEMG_DISCUSSION%", disc),
                   ("sections/06_conclusion.tex", "%PUTEMG_CONCLUSION%", concl)):
    p = M / f
    s = p.read_text(encoding="utf-8")
    if ph not in s:
        sys.exit(f"placeholder {ph} not found in {f}")
    p.write_text(s.replace(ph, txt), encoding="utf-8")
    print("filled", ph)
