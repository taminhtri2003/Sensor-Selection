"""2026-09-21 revision of sections/03_methods.tex (pre-submission audit). Blue = \\rev{}."""
from pathlib import Path

p = Path(__file__).resolve().parent.parent / "sections" / "03_methods.tex"
s = p.read_text(encoding="utf-8")


def rep(a, b):
    global s
    assert a in s, a[:70]
    s = s.replace(a, b)


rep(r"""\caption{Study design. For every held-out participant $p$, all preprocessing statistics, model fitting and channel ranking use only the other participants $R_{-p}$. Rankings are cross-fitted: $R_{-p}$ is split into five participant-disjoint inner folds, and attributions are computed only on inner-held-out participants. Subsets of $k$ channels are then retrained from scratch and tested on $p$. Decision rules (margin, statistical unit, bootstrap, multiplicity, $k^*$) were frozen before any sparse-channel result existed.}""",
    r"""\caption{\rev{Study workflow. For each held-out participant $p$, z-scoring, model fitting and channel ranking use the other participants $R_{-p}$; attributions are computed on participant-disjoint inner folds of $R_{-p}$; $k$-electrode subsets are retrained and tested on $p$. The same workflow was applied separately to each dataset.}}""")

rep(r"""Its channel numbers bear no anatomical correspondence to GRABMyo's, so only the behaviour of the procedure is compared across datasets.
""", r"""Its channel numbers bear no anatomical correspondence to GRABMyo's, so only the behaviour of the procedure is compared across datasets.

\rev{\paragraph{putEMG (exploratory methodological replication, added post hoc)}
putEMG~\cite{kaczmarek2019putemg} provides 44 able-bodied participants recorded on two days at least one week apart (7 to 82 days in these files; median 14). A 24-electrode monopolar array forms three circumferential bands of 8 electrodes (1--8, 9--16, 17--24) on the forearm, sampled at 5120~Hz with a 12-bit converter. Each session contains three trajectories with 20 repetitions of each of 7 active gestures, labelled from video-verified ground truth. This analysis was added at the end of the study, after all GRABMyo and DB5 results existed; its design was recorded before any putEMG model was fitted, and it is exploratory. All 264 gesture files were readable and complete, and every participant had both sessions. As for DB5, the putEMG channel numbers have no correspondence with GRABMyo's.}
""")

rep(r"""The ZC, SSC and WAMP amplitude threshold was set to $10^{-2}$~mV, about 1.15 times the median absolute first difference of the signal. This single label-free scalar was computed from the pooled recordings, not per fold. That is a minor departure from strict fold-wise estimation, which we note as a limitation. An earlier threshold 87 times smaller had saturated WAMP and was discarded. For DB5 we used a 10--95~Hz band-pass, no notch, 250~ms windows (50 samples) and a threshold of 7 ADC units, derived in the same way.""",
    r"""The ZC, SSC and WAMP amplitude threshold was set to $10^{-2}$~mV, about 1.15 times the median absolute first difference of the \rev{unfiltered signal in 54 probe records from 6 participants (rounded to one significant figure). This label-free scalar was set once rather than per fold. To check whether this let a held-out participant influence the features, we recomputed the median in every outer fold without that participant (post hoc). The same rule gave $10^{-2}$~mV in \LOOMonoIdentical\ of \LOOMonoFolds\ folds (leave-one-out medians \LOOMonoMin--\LOOMonoMax${}\times 10^{-3}$~mV; only \LOOMonoInProbe\ folds held out a probe participant). Fold-wise estimation would therefore have produced identical features.} An earlier threshold 87 times smaller had saturated WAMP and was discarded. For DB5 we used a 10--95~Hz band-pass, no notch, 250~ms windows (50 samples) and a threshold of 7 ADC units, derived in the same way \rev{from all ten subjects; the leave-one-out recomputation gave the same value in \LOODBFiveIdentical\ of \LOODBFiveFolds\ folds}. \rev{For putEMG, raw values were converted to mV and processed as for GRABMyo (20--450~Hz band-pass, 50~Hz notch, 250~ms windows of 1280 samples, 50\% overlap), keeping only windows that lay entirely inside one active-gesture segment (idle and rejected samples excluded). Because raw putEMG differences are quantised at one converter step, which equals their median, the threshold rule was applied to the filtered signal; it gave \PutThresh${}\times 10^{-3}$~mV and the same value in \PutThreshIdentical\ of 44 leave-one-out folds. This gives 240 features per window.}""")

rep(r"""In fold $p$, z-scoring statistics, model fitting and channel ranking use only $R_{-p}$. The test participant contributes only to the score.""",
    r"""In fold $p$, z-scoring statistics, model fitting and channel ranking use only $R_{-p}$. \rev{Apart from the label-free threshold checked above and the training-set sizes described below, the test participant contributes only to the score.}""")

rep(r"""On one calibration fold, halving the SVM subsample from 40,000 to 20,000 windows lowered Macro-F1 from \SVMCalibFortyK\ to \SVMCalibTwentyK. The SVM had therefore not saturated, and its result is a lower bound. No hyperparameter was tuned on any outer test participant.""",
    r"""On one calibration fold, halving the SVM subsample from 40,000 to 20,000 windows lowered Macro-F1 from \SVMCalibFortyK\ to \SVMCalibTwentyK\rev{, suggesting that the SVM had not saturated; its reported result is therefore likely a lower bound. Model hyperparameters were fixed in advance and not tuned. The training-set sizes (the SVM and random-forest subsamples and the 200,000-window cap used for the channel analyses) were chosen from held-out Macro-F1 on two calibration folds (participants 1 and 7) before the confirmatory runs, a departure from strict fold-wise isolation for those two participants (Section~\ref{sec:deviations}). XGBoost used the \texttt{multi:softprob} objective and library defaults for all unlisted parameters.}""")

rep(r"""For inner fold $j$, an XGBoost model was trained on the other inner folds (capped at a 200,000-window stratified subsample and z-scored with inner-training statistics only). Exact TreeSHAP attributions~\cite{lundberg2020local} were then computed for up to 20,000 windows of the inner-held-out participants.""",
    r"""For inner fold $j$, an XGBoost model was trained on the other inner folds (capped at a \rev{uniformly sampled} 200,000-window subsample and z-scored with inner-training statistics only). Exact TreeSHAP attributions~\cite{lundberg2020local} were then computed for up to 20,000 windows of the inner-held-out participants\rev{, sampled uniformly without replacement from their pooled windows. The attribution is therefore window-weighted; because every participant contributes a similar number of windows (median \TestWindowsPerParticipant), this is close to participant-weighted}.""")

rep(r"""Channels were ranked by""", r"""Channels were ranked \rev{(ties broken by lower channel index)} by""")

rep(r"""A leakage assertion verified in every fold that no inner-held-out participant appeared in its inner training set. Unit tests verified that a participant-specific signal planted in the data could not raise that participant's score.""",
    r"""A leakage assertion verified in every fold that no inner-held-out participant appeared in its inner training set. \rev{Unit tests verified that the outer test participant is never attributed, that inner folds are participant-disjoint, and that a synthetic dataset with a participant-confounded signal detects scaler leakage.}""")

rep(r"""The primary margin $\delta = 0.02$ Macro-F1 is an engineering tolerance, not a clinically validated threshold. $\delta = 0.01$ and $0.03$ are prespecified sensitivity margins.""",
    r"""\rev{The primary margin $\delta = 0.02$ is an absolute difference in class-averaged F1 on a 0--1 scale. It was fixed before the curve was computed as the largest loss we would accept in exchange for fewer electrodes. Relative to the full-array curve reference it is about \MarginPctOfRef\% of performance, and about \MarginPctAboveChance\% of the distance above chance (1/16 under uniform guessing). It is an engineering tolerance: it has not been validated against clinical outcomes or user performance. Because $k^*$ depends strongly on $\delta$, the prespecified sensitivity margins $\delta = 0.01$ and $0.03$ are reported so that readers can apply a different tolerance. The plan also required Holm correction within H1. The primary analysis above did not apply it; we therefore also report, post hoc, one-sided cluster-bootstrap $p$-values for $H_0\colon \bar\Delta_k \le -\delta$ with Holm correction over the 15 tested $k$ at $\alpha = 0.025$ (Section~\ref{sec:deviations}).}""")

rep(r"""\item permutation importance, from a model fitted on a 20,000-window subsample and evaluated on 8,000 further windows with 3 repeats;
\item mutual information, estimated on the same subsample;
\item a geometric baseline, which selects electrodes by farthest-point sampling on the $2 \times 8$ montage;
\item random subsets: 100 draws per participant at each $k$, and 500 at the prespecified $k^*$.""",
    r"""\item permutation importance\rev{: from a 40,000-window stratified subsample of the outer-training data, a model was fitted on 20,000 windows and each of the 160 features was permuted in 8,000 of the remaining windows (3 repeats, Macro-F1 scoring); a channel's score is the mean over its 10 features};
\item mutual information \rev{between each feature and the gesture label, estimated on the same 20,000 windows; a channel's score is the mean over its 10 features};
\item a geometric baseline, which selects electrodes by farthest-point sampling on the $2 \times 8$ montage \rev{(circumferential arc distance on an assumed 24~cm circumference, 2~cm between rings; deterministic start at F1, ties to the lower index). It uses no data};
\item random subsets: 100 draws per participant at each $k$, and 500 at the prespecified $k^*$ \rev{($k$ electrodes without replacement within a draw; draws independent, so a subset can recur; seed fixed per participant)}.""")

rep(r"""We also report where the SR-CFA subset falls within each participant's random distribution.""",
    r"""We also report where the SR-CFA subset falls within each participant's random distribution. \rev{Here and below, ``SR-CFA'' refers to $\lambda = 0.5$ and ``cross-fitted SHAP'' to $\lambda = 0$.}""")

rep(r"""For $n \in \{2, 4, \ldots, 14\}$ retained channels, the model was retrained after removing either the $16 - n$ highest-ranked channels (keeping the $n$ lowest) or the $16 - n$ lowest-ranked (keeping the top $n$). Random removal is the mean over the random subsets above, which exist for $n \in \{4, 6, 8, 12\}$.""",
    r"""For $n \in \{2, 4, \ldots, 14\}$ \rev{channels retained}, the model was retrained after removing either the $16 - n$ highest-ranked channels (\rev{Remove-Top}: keeping the $n$ lowest) or the $16 - n$ lowest-ranked (\rev{Remove-Bottom}: keeping the top $n$). \rev{Remove-Random} is the mean over the random subsets above, which exist for $n \in \{4, 6, 8, 12\}$.""")
rep(r"""the top-$n$ arm selects the same electrodes""", r"""the \rev{Remove-Bottom} arm selects the same electrodes""")
rep(r"""A faithful ranking gives top-removed $<$ random $<$ bottom-removed.""",
    r"""A faithful ranking gives \rev{Remove-Top $<$ Remove-Random $<$ Remove-Bottom}.""")

rep(r"""The participant is the statistical unit ($n = 43$; $n = 10$ for DB5).""",
    r"""The participant is the statistical unit ($n = 43$; $n = 10$ for DB5\rev{; $n = 44$ for putEMG. We use ``participant'' for GRABMyo and putEMG and ``subject'' for DB5, following each dataset's documentation}).""")
rep(r"""Holm correction is applied within each confirmatory family. Exploratory analyses are uncorrected and labelled as such.""",
    r"""Holm correction is applied within each confirmatory family. Exploratory analyses are uncorrected and labelled as such. \rev{A non-significant difference is reported as ``no statistically detectable difference'', never as equivalence; no equivalence test was performed.}""")

rep(r"""\paragraph{Ranking stability} We measured the agreement of rankings computed from single participants' attributions, from the five inner folds, and from the 43 outer folds. Outer folds share about 98\% of their training participants, so their agreement is only an upper bound.""",
    r"""\rev{Exploratory analyses are described in the order in which their results are reported.}

\rev{\subsubsection{Ranking stability}} We measured the agreement of rankings computed from single participants' attributions, from the five inner folds, and from the 43 outer folds. \rev{A participant's profile is the mean of their normalised out-of-fold attribution over the outer folds in which they were an inner-held-out participant. Agreement between two rankings is Spearman's $\rho$ and Kendall's $\tau$ over the 16 channel ranks, and Jaccard@$k$, the size of the intersection of the two top-$k$ sets divided by the size of their union; single-participant agreement uses all 903 participant pairs.} Outer folds share about 98\% of their training participants, so their agreement is only an upper bound.""")
rep(r"""\paragraph{Cross-session} XGBoost""", r"""\rev{\subsubsection{Cross-session}} XGBoost""")
rep(r"""\paragraph{Bipolar montage} To express the selection unit as a conventional bipolar sensor, we derived $B_j = F_j - F_{j+8}$ ($j = 1, \ldots, 8$) and re-extracted features. The count-feature threshold was re-derived for this signal ($5 \times 10^{-3}$~mV), because the bipolar signal is about half the monopolar amplitude. We then repeated the LOSO baseline, the cross-fitted ranking and the sparse curve, with the $k = 8$ model as reference.""",
    r"""\rev{\subsubsection{Bipolar montage}} To express the selection unit as a \rev{bipolar pair}, we derived $B_j = F_j - F_{j+8}$ ($j = 1, \ldots, 8$) and re-extracted features. \rev{These are derived pairs of the monopolar recording, not physical bipolar electrodes.} The count-feature threshold was re-derived for this signal ($5 \times 10^{-3}$~mV), because the bipolar signal is about half the monopolar amplitude. \rev{How this value was derived is not fully recorded: on the documented probe records the bipolar median is \LOOBipPooled${}\times 10^{-3}$~mV, for which the stated rule gives $\LOOBipRule \times 10^{-3}$~mV. The leave-one-out medians vary little, so the value is not driven by any single held-out participant, but its provenance is a limitation of this exploratory analysis.} We then repeated the LOSO baseline, the cross-fitted ranking and the sparse curve\rev{. The reference is the $k = 8$ model of the same curve (200,000-window training subsample), not the full bipolar baseline trained on all windows.}""")
rep(r"""\paragraph{DB5} The LOSO""", r"""\rev{\subsubsection{NinaPro DB5}} The LOSO""")
rep(r"""using all outer-training windows and the $k = 16$ model as reference.""",
    r"""using all outer-training windows and the $k = 16$ model as reference. \rev{The plan classed DB5 as exploratory, so its primary decision is uncorrected; the Holm-adjusted result is also reported.}

\rev{\subsubsection{putEMG} The same procedure was applied to putEMG: LOSO over 44 participants; XGBoost with the headline configuration trained on all outer-training windows (at most \PutTrainWindowsMax, below the 200,000-window cap); cross-fitted ranking ($K = 5$, all four $\lambda$); and the $\lambda = 0$ sparse curve for $k = 1, \ldots, 24$ with the $k = 24$ model as reference. Non-inferiority used the same bootstrap, margins and $k^*$ rule, with Holm correction over the 23 tested $k$ also reported. Ten random subsets per participant at $k \in \{6, 12, 18\}$ were compared with the ranked subsets (Wilcoxon, Holm over 3). No hyperparameter or training-set size was calibrated on putEMG. Because the montage has 24 electrodes in three bands, $k$ values are not comparable with GRABMyo's.}""")
rep(r"""\paragraph{Fixed layout} In a post-hoc""", r"""\rev{\subsubsection{Fixed layout}} In a post-hoc""")
rep(r"""\paragraph{Feature redundancy} IEMG""", r"""\rev{\subsubsection{Feature redundancy}} IEMG""")

rep(r"""The following changes were made after results existed. None alters a prespecified decision rule.
\begin{enumerate}""", r"""The following changes were made after results existed. None alters a prespecified decision rule.
\begin{enumerate}
\item \rev{Holm correction within H1, required by the plan, was not implemented in the primary analysis. It was added post hoc and gives the same $k^*$ at all three margins (Supplementary Table~\ref{tab:h1_holm}). A fixed-sequence analysis (testing $k = 15, 14, \ldots$ and stopping at the first failure) is reported only as a post-hoc sensitivity analysis.}
\item \rev{Training-set sizes were calibrated on held-out folds 1 and 7 before the confirmatory runs.}
\item \rev{The leave-one-out check of the count-feature thresholds was added post hoc.}""")
rep(r"""\item The window-length sensitivity and the 17-class task, both listed as exploratory in the plan, were not run.""",
    r"""\item The window-length sensitivity and the 17-class task, both listed as exploratory in the plan, were not run.
\item \rev{The putEMG replication was not in the plan and was added after all other results existed.}""")

p.write_text(s, encoding="utf-8")
print("methods revised")
