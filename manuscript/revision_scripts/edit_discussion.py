"""2026-09-21 revision of sections/05_discussion.tex and 06_conclusion.tex. Blue = \\rev{}."""
from pathlib import Path

root = Path(__file__).resolve().parent.parent / "sections"
p = root / "05_discussion.tex"
s = p.read_text(encoding="utf-8")


def rep(a, b):
    global s
    assert a in s, a[:70]
    s = s.replace(a, b)


rep(r"""Under a margin fixed before the curve was computed, four of the 16 GRABMyo electrodes could be removed while remaining non-inferior to the full array. Five could not. Every $k$ from 12 to 15 met the margin, so the result does not rest on a single lucky crossing.""",
    r"""Under a margin fixed before the curve was computed, four of the 16 GRABMyo electrodes could be removed while remaining non-inferior to the full array. Five could not. Every $k$ from 12 to 15 met the margin, so the result does not rest on a single \rev{isolated} crossing\rev{, and the plan's Holm correction, applied post hoc, left $k^*$ unchanged}.""")
rep(r"""The practical reading is modest: in a subject-independent setting, this 16-electrode array contains only limited redundancy for 16-gesture recognition. User-dependent studies that retain far fewer channels answer a different question~\cite{phinyomark2018emg,qu2021reduce}, and their results should not be taken as evidence that a population-level layout can be equally sparse.""",
    r"""The practical reading is modest: in a subject-independent setting, this 16-electrode \rev{monopolar} array contains only limited redundancy for 16-gesture recognition. User-dependent studies that retain far fewer channels answer a different question~\cite{phinyomark2018emg,qu2021reduce}, and their results should not be taken as evidence that a \rev{layout intended for many users} can be equally sparse.""")
rep(r"""Attribution-ranked subsets beat the average random subset at every size tested (H2), and deletion with retraining showed the expected ordering at every size (H4). The ranking is therefore not decorative: it reflects what the retrained models depend on. The stability penalty, however, did nothing (H3).""",
    r"""Attribution-ranked subsets \rev{exceeded the mean of the random subsets} at every size tested (H2), and deletion with retraining showed the expected ordering at every size (H4). \rev{Deletion with retraining therefore supports that the ranking reflects channels on which the retrained models depend.} The stability penalty, however, \rev{produced no measurable benefit} (H3).""")
rep(r"""It could not reorder channels in a way that mattered. We report SR-CFA as a tested and unsupported variant. The supported method is plain cross-fitted TreeSHAP magnitude, and a related robustness-weighted score has been proposed independently~\cite{xiang2026roshap}.""",
    r"""\rev{It changed the top-12 set in at most one fold.} We report SR-CFA as a tested and unsupported variant. \rev{The evidence therefore favours plain cross-fitted TreeSHAP magnitude over the regularised variant;} a related robustness-weighted score has been proposed independently~\cite{xiang2026roshap}.""")
rep(r"""\paragraph{Attribution is not better than simple alternatives}
The exploratory comparisons temper H2. Beating random subsets is a low bar. A data-free geometric rule that spreads electrodes around both rings matched the attribution ranking at 4, 8 and 12 electrodes, and permutation importance matched it at three of four sizes. Attribution had a clear advantage only at $k = 6$.""",
    r"""\paragraph{\rev{Limited additional benefit over simple alternatives}}
The exploratory comparisons temper H2. \rev{Exceeding the mean of random subsets} is a low bar. \rev{In exploratory comparisons, neither a data-free geometric rule nor permutation importance differed detectably from the attribution ranking at 4, 8 and 12 electrodes; attribution was higher at $k = 6$. Absence of a detectable difference is not evidence of equivalence.}""")
rep(r"""This fits a picture in which even circumferential coverage explains most of what any ranking can achieve, and the choice among well-spread layouts matters little. For a device designer, the evidence favours a well-spread layout of about 12 electrodes over trusting any particular ranking to identify an unusually good sparse subset.""",
    r"""\rev{One hypothesis consistent with this pattern is that even circumferential coverage accounts for much of what a ranking achieves. Whether a data-free, evenly spread layout is itself non-inferior to the full array was not tested and is a question for future work.}""")
rep(r"""We deliberately do not map them to named muscles. The dataset documents ring positions, not the anatomical placement of each circumferential index.""",
    r"""We deliberately do not map them to named muscles. The dataset documents ring positions, not the anatomical placement of each circumferential index\rev{, and no imaging-based registration of electrodes to muscles was available}.""")
rep(r"""This fits the finding that many different well-spread subsets perform similarly.""",
    r"""\rev{Physiologically, it is plausible that a few circumferential sites capture activity shared by several gestures, but these data cannot attribute that activity to specific muscles.}""")
rep(r"""Held-out participants were not recognised worse on later days than on the training day. This shows only that no extra cross-day loss was detectable on top of the cross-user gap, not that electrode shift is harmless~\cite{hargrove2006effect,kaufmann2010fluctuating,vidovic2016improving}.""",
    r"""\rev{No additional loss on later days was detected on top of the cross-user gap.} This \rev{does not show} that electrode shift is harmless~\cite{hargrove2006effect,kaufmann2010fluctuating,vidovic2016improving}.""")
rep(r"""On DB5 the whole procedure ran without modification, but the replication was underpowered. Ten subjects and a low baseline left the $k = 12$ decision on the margin, with neighbouring $k$ failing. It is best read as a non-contradiction rather than a replication of the reduction.""",
    r"""On DB5 the whole procedure ran without modification, but \rev{with 10 subjects the estimates were imprecise, and the $k = 12$ decision depended on the bootstrap seed and did not survive Holm correction, with neighbouring $k$ failing. The result neither replicates nor contradicts the GRABMyo reduction.} %PUTEMG_DISCUSSION%""")
rep(r"""All participants were able-bodied, and all analysis was offline. The SVM was trained on a subsample and is a lower bound. The H2 and H4 comparisons used a lighter comparison model than the headline curve. The count-feature threshold was a single scalar set from pooled data. $\lambda$ was not selected, and the detailed H2--H4 test families were specified after the underlying results were computed (Section~\ref{sec:deviations}). Cross-model attribution, window-length sensitivity and the 17-class task were listed as exploratory in the plan and were not run.""",
    r"""All participants were able-bodied, and all analysis was offline\rev{: filtering was zero-phase (non-causal) and windows were 250~ms, so the results are an offline benchmark and do not establish performance in real-time, causal control. Fatigue, limb posture and electrode shift were not isolated. Rankings were computed from full-array models and could shift if models were trained only on a reduced array. No imaging-based registration of electrodes to muscles was available.} The SVM was trained on a subsample and is \rev{likely} a lower bound. The H2 and H4 comparisons used a lighter comparison model than the headline curve. The count-feature threshold was a single scalar set \rev{once rather than per fold (a leave-one-out check found no effect), training-set sizes were calibrated on two held-out folds, and the bipolar threshold's derivation is not fully recorded}. $\lambda$ was not selected, and the detailed H2--H4 test families were specified after the underlying results were computed (Section~\ref{sec:deviations}). \rev{The fixed-layout analysis and the putEMG replication were post hoc, and DB5 had only 10 subjects.} Cross-model attribution, window-length sensitivity and the 17-class task were listed as exploratory in the plan and were not run.""")
p.write_text(s, encoding="utf-8")

p = root / "06_conclusion.tex"
p.write_text(r"""\section{Conclusion}
\label{sec:conclusion}

\rev{We evaluated explainability-guided electrode reduction for subject-independent sEMG gesture recognition using cross-fitted attribution and prespecified primary decision rules.}

\rev{\textit{Supported}, for subject-independent, offline recognition with a two-ring monopolar forearm montage in able-bodied participants: removal of four of 16 electrodes within a prespecified 0.02 Macro-F1 tolerance, unchanged under Holm correction, but not of five; attribution-ranked subsets above the mean of random subsets of the same size; deletion-based support for the faithfulness of the ranking; and no measurable benefit from the stability penalty. %PUTEMG_CONCLUSION%}

\rev{\textit{Not established}: clinical performance; reduction of physical bipolar hardware (with derived bipolar pairs, no pair could be removed within the same tolerance); equivalence to, or superiority over, a data-free geometric selection; real-time use; muscle-level localisation; and generalisation beyond these cohorts and montages.}

\rev{Validation in target clinical populations (e.g.\ people with upper-limb loss) and in online, causal control settings is required.}
""", encoding="utf-8")
print("discussion + conclusion revised")
