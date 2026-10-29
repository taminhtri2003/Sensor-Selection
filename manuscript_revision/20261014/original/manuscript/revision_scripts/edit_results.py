"""2026-09-21 revision of sections/04_results.tex (pre-submission audit). Blue = \\rev{}."""
from pathlib import Path

p = Path(__file__).resolve().parent.parent / "sections" / "04_results.tex"
s = p.read_text(encoding="utf-8")


def rep(a, b):
    global s
    assert a in s, a[:70]
    s = s.replace(a, b)


rep(r"""XGBoost and the SVM did not differ: the paired difference was""",
    r"""\rev{No statistically detectable difference was observed between XGBoost and the SVM}: the paired difference was""")

rep(r"""Every $k$ from 12 to 15 was non-inferior, so the result is not an isolated crossing. For the same reason, the result survives the multiplicity of testing 15 values of $k$. A fixed-sequence procedure, testing $k = 15, 14, \ldots$ in order and stopping at the first failure, controls the familywise error rate without adjustment and yields the same $k^*$.""",
    r"""Every $k$ from 12 to 15 was non-inferior, so the result is not an isolated crossing. \rev{The plan specified Holm correction within H1, which the primary analysis did not apply. Applied post hoc (one-sided cluster-bootstrap $p$, 15 values of $k$), it gave the same $k^*$ at all three margins ($\KStarHolmPtOne$, $\KStarHolm$ and $\KStarHolmPtThree$ at $\delta = 0.01$, 0.02 and 0.03; $k = 12$: $p_{\mathrm{Holm}} \HolmPKTwelve$; Supplementary Table~\ref{tab:h1_holm}). A post-hoc fixed-sequence analysis from $k = 15$ downward also gave $k^* = \KStarFixSeq$.}""")

rep(r"""\subsection{H2: attribution-ranked subsets beat random subsets; other rankings match them}""",
    r"""\subsection{H2: attribution-ranked subsets \rev{exceed the mean of random subsets}}""")
rep(r"""Attribution therefore reliably beats the average random subset, but it rarely finds the best subset available for a given person.""",
    r"""\rev{Attribution-ranked subsets exceeded the mean of the sampled random subsets at every $k$, but rarely fell in the upper tail ($\geq$ 95th percentile) of each participant's sampled random-subset distribution.}""")
rep(r"""In exploratory contrasts, attribution was not better than simpler alternatives. It did not differ from permutation importance at $k = 4$, 8 or 12 (e.g.\ $k = 8$: $\VSPermKEightDiff$, $p \VSPermKEightP$), and it exceeded it only at $k = 6$ ($\VSPermKSixDiff$, $p \VSPermKSixP$). The geometric baseline, which spreads electrodes evenly around both rings without using any data, matched SR-CFA at $k = 4$ ($\VSGeomKFourDiff$, $p \VSGeomKFourP$), $k = 8$ ($\VSGeomKEightDiff$, $p \VSGeomKEightP$) and $k = 12$ ($\VSGeomKTwelveDiff$, $p \VSGeomKTwelveP$). It was worse only at $k = 6$ ($\VSGeomKSixDiff$, $p \VSGeomKSixP$).""",
    r"""\rev{In exploratory, uncorrected contrasts, attribution showed limited additional benefit over simpler alternatives. No statistically detectable difference from permutation importance was observed at $k = 4$, 8 or 12} (e.g.\ $k = 8$: $\VSPermKEightDiff$, $p \VSPermKEightP$)\rev{; SR-CFA was higher at $k = 6$} ($\VSPermKSixDiff$, $p \VSPermKSixP$). The geometric baseline, which spreads electrodes evenly around both rings without using any data, \rev{showed no statistically detectable difference from SR-CFA at} $k = 4$ ($\VSGeomKFourDiff$, $p \VSGeomKFourP$), $k = 8$ ($\VSGeomKEightDiff$, $p \VSGeomKEightP$) and $k = 12$ ($\VSGeomKTwelveDiff$, $p \VSGeomKTwelveP$)\rev{; SR-CFA was higher at $k = 6$} ($\VSGeomKSixDiff$, $p \VSGeomKSixP$). \rev{These contrasts do not show that the methods are equivalent.}""")

rep(r"""H3 is not supported. In these data, the cross-fitted magnitude ranking is already stable enough that a stability penalty has nothing to correct.""",
    r"""H3 is not supported. \rev{Under this protocol the stability penalty produced no measurable improvement, consistent with the small instability term.}""")

rep(r"""\subsection{H4: the attribution is faithful}""", r"""\subsection{H4: \rev{deletion with retraining supports faithfulness}}""")
rep(r"""At six retained electrodes, top-removed scored \FaithTopKSix, random \FaithRandomKSix\ and bottom-removed \FaithBottomKSix\ (top $-$ random $\FaithTRKSixDiff$, $p_{\mathrm{Holm}} \FaithTRKSixP$; random $-$ bottom $\FaithRBKSixDiff$, $p_{\mathrm{Holm}} \FaithRBKSixP$). The only non-significant contrast was top- versus bottom-removal at 14 retained electrodes ($\FaithTBKFourteenDiff$, $p_{\mathrm{Holm}} \FaithTBKFourteenP$), where only two electrodes are removed. The gap between arms was largest at intermediate sizes and small at the extremes. With few electrodes left all arms perform poorly; with many left, the array is redundant enough that any two electrodes can be spared.""",
    r"""\rev{With six channels retained, Remove-Top} scored \FaithTopKSix, \rev{Remove-Random} \FaithRandomKSix\ and \rev{Remove-Bottom} \FaithBottomKSix\ (\rev{Remove-Top $-$ Remove-Random} $\FaithTRKSixDiff$, $p_{\mathrm{Holm}} \FaithTRKSixP$; \rev{Remove-Random $-$ Remove-Bottom} $\FaithRBKSixDiff$, $p_{\mathrm{Holm}} \FaithRBKSixP$). The only non-significant contrast was \rev{Remove-Top versus Remove-Bottom with 14 channels retained} ($\FaithTBKFourteenDiff$, $p_{\mathrm{Holm}} \FaithTBKFourteenP$), where only two electrodes are removed. \rev{The separation between deletion orders was largest at intermediate sizes and small at the extremes.}""")

rep(r"""Performance on later sessions was not lower than on the training session. The session-2 score was higher ($\CSSTwoVsSOneDiff$, 95\% CI $\CSSTwoVsSOneLCB$ to $\CSSTwoVsSOneUCB$, uncorrected $p \CSSTwoVsSOneP$), and session 3 did not differ ($\CSSThreeVsSOneDiff$, $p \CSSThreeVsSOneP$).""",
    r"""\rev{Mean Macro-F1 on sessions 2 and 3 was numerically higher than on session 1. The session-2 difference was nominally significant} ($\CSSTwoVsSOneDiff$, 95\% CI $\CSSTwoVsSOneLCB$ to $\CSSTwoVsSOneUCB$, uncorrected $p \CSSTwoVsSOneP$), and \rev{no statistically detectable difference was observed for session 3} ($\CSSThreeVsSOneDiff$, $p \CSSThreeVsSOneP$).""")

rep(r"""In deployable sensor units, then, the array showed no redundancy within the prespecified tolerance.""",
    r"""\rev{With derived bipolar pairs as the unit, no reduction met the primary margin. The reference here is the $k = 8$ model of the bipolar curve (\BipCurveRefK), trained on the same subsample as the other curve points.}""")

rep(r"""Under the frozen rule, $k^* = \DBFiveKStarMarginPtTwo$ at $\delta = 0.02$ ($\bar\Delta_{12} = \DBFiveDeltaKTwelve$, lower bound $\DBFiveDeltaKTwelveLCB$). This result is fragile. The lower bound lies on the margin,""",
    r"""Under the frozen rule, $k^* = \DBFiveKStarMarginPtTwo$ at $\delta = 0.02$ ($\bar\Delta_{12} = \DBFiveDeltaKTwelve$, lower bound $\rev{\DBFiveDeltaKTwelveLCBSix}$). This result is fragile. The lower bound lies on the margin,""")
rep(r"""A fixed-sequence procedure starting at $k = 15$ would stop immediately and report no non-inferior subset. With ten subjects, DB5 does not support a claim that a quarter of the channels can be removed. The procedure itself transferred without modification, and the ranked curve had the same monotone shape.""",
    r"""\rev{With Holm correction over the 15 tested $k$ (not required for this exploratory analysis), no subset was non-inferior at $\delta = 0.02$ ($k^* = \DBFiveKStarHolmPtTwo$), and a post-hoc fixed-sequence analysis from $k = 15$ would stop at the first step.} With ten subjects, DB5 does not support a claim that a quarter of the channels can be removed. \rev{The procedure ran on DB5 without modification; the mean curve increased broadly with $k$ but was not monotone.}""")

rep(r"""Channel rankings were almost unchanged: the median per-fold Spearman $\rho$ between rankings with and without IEMG was \RedundRho, and the top-12 set was identical in \RedundTopTwelveSame\ of 43 folds. The duplicated feature therefore did not distort the channel ranking.""",
    r"""Channel rankings were almost unchanged: the median per-fold Spearman $\rho$ between rankings with and without IEMG was \RedundRho, and the top-12 set was identical in \RedundTopTwelveSame\ of 43 folds. \rev{Removing the duplicated feature therefore had little measurable effect on the channel ranking.}""")

# putEMG paragraph placeholder, filled by edit_results_putemg.py once results exist
rep(r"""\paragraph{Fixed layout (post hoc)}""", r"""%PUTEMG_RESULTS%

\paragraph{Fixed layout (post hoc)}""")

# figure captions
rep(r"""(b) Paired difference to the $k = 16$ model with 95\% CI. Dashed lines mark the prespecified margin ($\delta = 0.02$) and the two sensitivity margins.}""",
    r"""(b) Paired difference to the $k = 16$ model with 95\% CI. \rev{The thick dark dashed line marks the primary margin ($-\delta$, $\delta = 0.02$); thin grey lines mark the sensitivity margins (0.01, 0.03).}}""")
rep(r"""Random removal is available where random subsets were sampled ($n$ = 4, 6, 8, 12).}""",
    r"""\rev{Remove-Random} is available where random subsets were sampled ($n$ = 4, 6, 8, 12).}""")
rep(r"""\caption{Exploratory analyses. (a) Cross-session: each point is one held-out participant (bar = median); all conditions are also subject-independent. (b) NinaPro DB5 sparse curve (10 subjects; mean and 95\% cluster-bootstrap CI; dotted line = chance). (c) GRABMyo bipolar-pair sparse curve (43 participants; $\lambda = 0$).}""",
    r"""\caption{\rev{Exploratory analyses. (a) Cross-session: grey lines join the same held-out participant across conditions (bar = median); all conditions are also subject-independent. (b--d) Paired difference to the full-array reference of the same curve, $\bar\Delta_k$ with 95\% cluster-bootstrap CI, for (b) NinaPro DB5 (10 subjects, reference $k = 16$), (c) GRABMyo derived bipolar pairs (43 participants, $\lambda = 0$, reference $k = 8$) and (d) putEMG (44 participants, reference $k = 24$). Thick dashed line = primary margin $-0.02$; filled markers = lower bound above the margin.}}""")
p.write_text(s, encoding="utf-8")
print("results revised")
