# Research Methodological Decision Log

This log documents all major scientific, methodological, and data-processing decisions made during the study, including alternatives considered, justification, date, and affected pipeline components.

---

## Decision 1: Primary Task Definition & Rest Class Handling
- **Decision**: Define the primary gesture recognition task using active hand gestures (16 classes for GRABMyo, 12 classes for DB5), excluding rest from the primary metric calculation.
- **Alternatives Considered**: Including rest as a class in the primary metric; evaluated separately as a secondary task.
- **Reason**: Rest periods typically occur with high frequency and are baseline static signals with near 100% accuracy. Including rest inflates weighted F1 and accuracy, masking potential performance degradation on active movement pairs.
- **Date**: 2026-08-12
- **Affected Pipeline Modules**: `src/semg_sparse/segmentation/windowing.py`, `scripts/04_preprocess.py`, `scripts/06_run_full_channel_baselines.py`.

---

## Decision 2: Zero-Leakage Cross-Fitted SHAP Aggregation
- **Decision**: Calculate Out-Of-Fold (OOF) TreeSHAP attributions across inner subject-grouped folds on training participants only ($R_p$). Zero data or statistics from outer held-out test participant $p$ are used during ranking generation.
- **Alternatives Considered**: Calculating SHAP values on a single model trained on all training subjects; calculating SHAP values across the entire dataset.
- **Reason**: Calculating SHAP on the same samples used to fit the model risks overfitting attribution to training noise. Computing OOF attributions across grouped folds ensures feature importance is evaluated on unseen training subjects, maximizing subject-independent stability.
- **Date**: 2026-08-12
- **Affected Pipeline Modules**: `src/semg_sparse/xai/shap_attributions.py`, `scripts/07_run_xai_selection.py`.

---

## Decision 3: Statistical Non-Inferiority Margin ($\delta = 0.02$)
- **Decision**: Prespecify $\delta = 0.02$ Macro-F1 as the primary non-inferiority margin for sparse channel selection ($k^* = \min_k \{ LCB_{95\%}(\Delta_k) > -\delta \}$). Perform sensitivity analysis at $\delta = 0.01$ and $\delta = 0.03$.
- **Alternatives Considered**: Arbitrary visual thresholding at performance plateaus; standard null-hypothesis significance testing ($p < 0.05$).
- **Reason**: Standard significance testing cannot prove equivalence or non-inferiority (failure to reject $H_0$ is not evidence of absence). A formal non-inferiority framework with participant-level bootstrap CIs provides a rigorous, objective criterion for sensor reduction.
- **Date**: 2026-08-12
- **Affected Pipeline Modules**: `src/semg_sparse/statistics/non_inferiority.py`, `scripts/13_run_statistics.py`.

---

## Decision 4: Window Duration and Overlap
- **Decision**: Set primary sliding window duration to 250 ms with 50% overlap (125 ms stride). Evaluate sensitivity at 150 ms and 500 ms.
- **Alternatives Considered**: 100 ms, 500 ms non-overlapping windows.
- **Reason**: 250 ms is widely accepted in upper-limb prosthetics as balancing feature extraction stability with real-time controller latency constraints ($<300$ ms delay).
- **Date**: 2026-08-12
- **Affected Pipeline Modules**: `src/semg_sparse/preprocessing/filters.py`, `scripts/04_preprocess.py`.

---

## Decision 6: Per-model training-window budgets (compute constraint)
- **Decision**: Fit Random Forest on a stratified random subsample of **200,000** outer-training
  windows and RBF SVM on **40,000**, with model hyperparameters left identical to the full-data
  configuration. XGBoost uses all ~550,000 training windows. Subsamples are drawn with a fixed
  seed (20260728), identically for every outer fold.
- **Alternatives considered**: (a) full training data for all models; (b) cheaper RF
  hyperparameters (depth cap, fewer trees); (c) demoting RF to a confirmatory role.
- **Evidence** (single fixed fold, held-out participant 1, measured 2026-08-12):

  | configuration | fit time | Macro-F1 |
  |---|---|---|
  | RF 200 trees, depth=None, 550k windows | 287.4 s | 0.5304 |
  | RF 200 trees, depth=25, leaf=5, 550k   | 234.8 s | 0.5294 |
  | RF 150 trees, depth=20, leaf=10, 550k  | 162.4 s | 0.5250 |
  | **RF 200 trees, depth=None, 200k**     | **97.2 s** | **0.5309** |
  | RF 200 trees, depth=25, leaf=5, 200k   | 104.3 s | 0.5291 |
  | SVM 20k                                 | 75.4 s  | 0.5554 |
  | **SVM 40k**                             | 376.2 s | **0.5911** |

- **Reason**: Random Forest gains nothing from windows beyond ~200k — cutting the training set by
  64% changed Macro-F1 by +0.0005 (0.5304 -> 0.5309, i.e. within fold-level noise) while cutting
  fit time roughly threefold. Reducing capacity via hyperparameters was *worse*: depth-capping cost
  accuracy (0.5250-0.5294) for a smaller speedup. Subsampling is therefore preferred to
  hyperparameter reduction, and leaves the model specification comparable to the full-data setting.
- **Important asymmetry**: SVM behaves oppositely — halving its subsample from 40k to 20k cost
  0.036 Macro-F1 (0.5911 -> 0.5554). SVM has *not* saturated, so its reported performance is
  **limited by the compute constraint and is a lower bound**; its full-data performance would
  likely be higher. This must be stated wherever SVM is compared with the tree models, especially
  if SVM is the strongest model, because the constraint handicaps it rather than favouring it.
- **Caveat**: measured on one outer fold. The direction (no RF degradation) is unambiguous, but the
  estimate is not a mean over folds. If the completed 43-fold RF run diverges materially from the
  full-data expectation, this decision must be revisited.
- **Date**: 2026-08-12
- **Affected**: `scripts/24_full_channel_loso_parallel.py` (RF_SUBSAMPLE, SVM_SUBSAMPLE).

---

## Decision 7: Statistical analysis plan frozen before results
- **Decision**: Commit `configs/statistics/frozen_analysis_plan.yaml` fixing the primary endpoint,
  statistical unit, non-inferiority margin, bootstrap procedure, multiplicity correction, lambda
  selection rule, exclusion policy, and reporting precision.
- **Attestation of state at freeze time** (2026-08-12):
  - SHA256 of the plan: `734f889ae4afdf2440585b41d19f204e2a0f9cd68d263b2ea1fe411287b4459f`
  - Results existing: full-channel LOSO baselines only, and still in progress
    (`artifacts/metrics/loso_full_channel_subject_metrics_xgb.csv`)
  - Results NOT existing: sparse sensor curve, selection baselines, non-inferiority statistics,
    stability, faithfulness, cross-session, DB5 replication. `artifacts/statistics/` was empty.
- **Reason**: The decisions most vulnerable to hindsight are exactly the ones that determine
  whether the headline is positive: the margin delta, which k counts as "optimal", which
  comparisons are confirmatory rather than exploratory, and whether difficult participants stay in
  the analysis. Fixing them while the answers are unknown is the only structural defence. The prior
  version of this study reported delta = 0.02, k* = 6, and p < 0.001 without ever computing them;
  care at writing time did not prevent that, and would not have.
- **Binding consequences**: the margin may not be loosened after seeing the curve; lambda may not
  be selected on outer-test performance; exploratory findings may not be promoted into the abstract;
  no participant may be dropped for scoring poorly.
- **Date**: 2026-08-12
- **Affected**: `scripts/28_statistics.py` (to be written), all downstream reporting.

---

## Decision 8: XGBoost training-window budget for the combinatorial phases
- **Decision**: For the sensor-curve phases (P3 sparse curve, P4 selection baselines, P8
  faithfulness), fit XGBoost on a stratified random subsample of **200,000** outer-training
  windows. Hyperparameters unchanged. The P1 headline baseline keeps the full ~550,000 windows.
- **Evidence** (two fixed folds, chosen to avoid one unusual participant driving the decision):

  | train windows | participant 1 Macro-F1 | participant 7 Macro-F1 |
  |---|---|---|
  | 100,000 | 0.5665 | 0.6126 |
  | 200,000 | 0.5700 | 0.6150 |
  | 350,000 | 0.5637 | 0.6140 |
  | 550,368 (all) | 0.5635 | 0.6204 |

- **Reason**: XGBoost has saturated by ~100-200k windows; the spread across budgets is +/-0.005,
  within fold-level noise, and at 200k it is marginally *higher* than full data on participant 1.
  The combinatorial phases involve thousands of fits (16 k-values x 43 folds, plus random subsets),
  so this is the difference between a tractable run and an intractable one.
- **Consistency requirement**: because the curve phases use a different training budget from P1,
  the k=16 reference point for non-inferiority must be taken from the **sparse curve itself**, not
  from the P1 headline. `scripts/28_statistics.py` already does this (it reads k=16 from the curve
  frame). Mixing the two would compare models trained on different amounts of data and bias the
  paired difference.
- **Caveat**: timings in `runs/xgb_trainsize.log` are unreliable because the SVM/RF job was
  competing for CPU during data preparation; only the accuracy comparison is used for this
  decision.
- **Date**: 2026-08-12
- **Affected**: `scripts/26`, `scripts/27`, `scripts/31`, `src/semg_sparse/xai/cross_fitted.py`.

---

## Decision 9: Primary model justified on compute, not performance
- **Context**: The superseded manuscript asserted XGBoost was the best full-channel model and built
  the entire sparse-selection chain on that basis. The completed 43-fold baseline does not support
  the premise.
- **Measured** (43 participants, 16 active gestures, participant cluster bootstrap, 10,000 resamples):

  | model | Macro-F1 | 95% CI |
  |---|---|---|
  | XGBoost | 0.542 | [0.517, 0.567] |
  | SVM | 0.538 | [0.513, 0.562] |
  | Random Forest | 0.502 | [0.475, 0.528] |

  Paired, Holm-corrected:

  | comparison | mean diff | 95% CI | p (Holm) | rank-biserial |
  |---|---|---|---|---|
  | RF vs SVM | -0.036 | [-0.044, -0.028] | < 0.001 | -0.97 |
  | RF vs XGBoost | -0.041 | [-0.048, -0.034] | < 0.001 | -0.98 |
  | **SVM vs XGBoost** | **-0.0045** | **[-0.011, +0.002]** | **0.154** | -0.25 |

- **Decision**: XGBoost remains the primary model for the sensor-selection phases, justified
  **solely on computational grounds** (48 s per GPU fit versus SVM's O(n^2) scaling, which makes the
  16-k-value x 43-fold sweep and the random-subset baselines tractable). The manuscript must not
  claim XGBoost is the best-performing model.
- **What may be claimed**: XGBoost and SVM are statistically indistinguishable at the full-channel
  baseline; Random Forest is inferior to both with near-total rank consistency across participants.
- **Compounding caveat**: SVM was fitted on 40,000 training windows against XGBoost's ~550,000, and
  Decision 6 established that SVM had **not** saturated at that budget (20k -> 40k gained 0.036
  Macro-F1). Its 0.538 is therefore a **lower bound**. Since the XGBoost-SVM gap is already
  non-significant, a fully-trained SVM could plausibly exceed XGBoost. This must be stated wherever
  the models are compared.
- **Date**: 2026-08-12
- **Affected**: model-selection rationale in Methods; Table 4; all sensor-selection phases.

---

## Decision 10: Compute-only configuration for the random selection baseline
- **Decision**: Keep the frozen random-subset counts (100 draws at k=4, 6, 8; 500 draws at the
  prespecified k-star), but use the explicitly exploratory comparison model with **50 XGBoost
  trees** rather than 150. All fixed and random selection methods use this identical configuration.
  Run two independent outer-fold workers concurrently; each fold still derives rankings and scaling
  from outer-training participants only.
- **Reason**: A graph_gpu dry run with the original 150-tree exploratory configuration projected
  multi-day runtime for the 43-fold, 800-plus-fit participant folds. It was stopped before any
  selection metric checkpoint was written. This is a compute deviation, not a result-driven change;
  the frozen random-subset coverage and participant-level comparisons are unchanged.
- **Reporting**: `artifacts/selection_baselines/compute_budget.json` records the actual model and
  counts. Selection-baseline absolute scores must not be compared with the P1/P3 headline scores;
  only the matched-method participant-level comparisons are used.
- **Date**: 2026-08-14
- **Affected**: `scripts/27_selection_baselines.py`, `scripts/43_run_remaining_study.py`, P4.

---

## Decision 11: Faithfulness (P8) re-run under a single training protocol
- **Finding (audit 2026-09-21)**: the P8 run of 2026-08-15 combined three arms trained under three
  different budgets: remove_top computed with 150 trees / 150k windows; remove_bottom read from
  the P3 curve (300 trees / 200k windows); remove_random read from P4 (50 trees / 150k windows).
  The bottom arm therefore had the strongest model, which biases the deletion ordering toward
  "faithful". Its verdicts and the manuscript paragraph built on them are invalid.
- **Decision**: both ranked arms are recomputed with the P4 configuration exactly (50 trees, same
  stratified 150k subsample, same seed); the random arm is read from P4 under the same protocol.
  A built-in check verifies that bottom-removal reproduces P4's SHAP_lam0 values at the shared k.
- **Archived**: `_archive_invalid/faithfulness_mixed_budget/`.
- **Date**: 2026-09-21

## Decision 12: Bipolar sensitivity (P11) invalid; features re-extracted
- **Finding**: `data/features/grabmyo_bipolar_features.parquet` used by the 2026-08-15 P11 run was
  the first extraction with the inherited monopolar count threshold (1e-2 mV, 2.3x the bipolar
  signal scale). The corrected re-extraction (5e-3 mV) had been interrupted and never completed.
  Measured on the file: SSC medians 0-6 per channel (suppressed). All P11 results and the
  bipolar manuscript paragraph/macros derived from them are invalid.
- **Decision**: re-extracted 15,351/15,351 records with 5e-3 mV (SSC medians now 17-69), re-ran
  P11. Compute-only change: each distinct channel subset is fitted once per participant and shared
  across lambdas that select it (identical inputs and seed give an identical model).
- **Archived**: `_archive_invalid/bipolar_threshold_1e-2/`.
- **Date**: 2026-09-21

## Decision 13: No lambda* selected; H2/H3/H4 families specified (post-hoc specification)
- **Finding**: the frozen plan requires lambda to be selected on outer-training data only but
  specifies no criterion, and no selection procedure was implemented. P4 and the fixed-layout
  experiment used lambda = 0.5 with no recorded rationale; the previous draft presented 0.5 as
  "the proposed method" and reported a lambda-ablation stability gain (Jaccard@6 0.941 -> 0.992)
  that corresponds to no computed artifact.
- **Decision**: no lambda* is selected. All four candidates are reported. This is possible without
  bias because the results are practically invariant to lambda: top-12 sets differ from lambda = 0
  for 0/43 (0.25), 0/43 (0.5), 1/43 (1.0) participants, and k* is identical under all lambdas and
  margins. H3 is tested as each lambda > 0 vs lambda = 0 at k in {4, 6, 8, 12} on the P3 curve
  (Holm over 12 tests). H2 is tested for both rankings that entered P4 (lambda = 0.5, lambda = 0)
  against the random mean at k in {4, 6, 8, 12} (Holm over 8). H4: top vs bottom at every k,
  top vs random and random vs bottom where random exists (Holm over the family).
- **Status**: these are specifications of items the frozen plan left open, written after the P3
  and P4 results existed. They are reported in the manuscript as post-hoc specifications.
- **Date**: 2026-09-21

## Decision 14: Previous manuscript draft contained numbers not traceable to artifacts
- **Finding** (2026-09-21 audit of `manuscript/sections/04_results.tex`, edited 2026-09-14):
  the baseline-comparison table values (e.g. SR-CFA k=4 0.378) match no artifact
  (`selection_baseline_summary.csv` gives 0.383); the lambda-ablation numbers have no source;
  cross-session W/p values differ from recomputation (W=55, p=1.35e-7 stated vs W=77 recomputed);
  the feature-redundancy result was stated for 43 participants but computed on 3; the stability
  caption names channels 1, 9, 5, 13 as stable hubs whereas the computed top-4 is {4, 6, 7, 14};
  and the DB5 paragraph equates DB5 channel numbers with GRABMyo channel numbers.
- **Decision**: the Results section is rewritten with every number emitted by
  `scripts/40_generate_macros.py` or a generated table; a checker fails the build on hand-typed
  decimals in Results. Feature redundancy re-run on all 43 folds (`scripts/38_feature_redundancy.py`).
- **Date**: 2026-09-21

## Decision 15: Bibliography rebuilt from registry records
- **Finding**: of 30 references cited in the 2026-09-14 draft, 10 had DOIs that do not exist in
  Crossref and 4 had DOIs resolving to unrelated papers (e.g. `liu2014emg` -> an X-ray calibration
  paper). The literature matrix had the same defect: 11 non-existent DOIs and 3 resolving to other
  works out of 93 rows (`reports/literature_doi_audit.csv`).
- **Decision**: `manuscript/references.bib` is generated by `scripts/build_verified_bib.py` from
  Crossref / arXiv records only (35 entries). Works whose intended identity could not be confirmed
  (`campbell2020differences`, `bi2019high`, `he2020spatial`) were removed together with the claims
  they supported (e.g. "25-35 percentage point" user-independent drop). The matrix carries a
  `doi_verification` column; rows flagged DOI_NOT_FOUND / TITLE_MISMATCH must not be cited.
- **Date**: 2026-09-21

## Decision 16: Superseded deliverables archived
- `FINAL_DELIVERY/`, `figures_final/`, `slides/`, `results/`, `FINAL_STUDY_COMPLETION_REPORT.md`
  and the 2026-09-14 audit reports moved to `_archive_invalid/superseded_2026-09-14/` (see its
  README). The fixed-layout outputs, which are valid, were moved to `artifacts/fixed_layout/`.
- **Date**: 2026-09-21

## Decision 17: Leave-one-participant-out check of the count-feature thresholds (post hoc)
- **Trigger**: pre-submission audit P0-1 (the manuscript claimed the held-out participant never
  influenced preprocessing, but the ZC/SSC/WAMP thresholds were set once from pooled records).
- **Analysis**: `scripts/39_loo_threshold_check.py` recomputes, for each outer fold, the median
  |first difference| without the held-out participant and applies the documented rule
  (1.15 x median, one significant figure). The GRABMyo monopolar threshold was derived from 54 probe
  records of only 6 participants (1, 7, 15, 23, 31, 43), so 37/43 folds are unaffected by
  construction.
- **Result**: GRABMyo monopolar 43/43 folds give 1e-2 mV (LOO median 8.52e-3 to 9.45e-3);
  DB5 10/10 folds give 7 ADC (LOO median 6 in every fold). Fold-wise derivation would therefore have
  produced identical features; no re-run is needed. Bipolar: the stated source median (4.35e-3 mV)
  cannot be reproduced; on the documented probes the rule gives 4e-3 mV, not the 5e-3 mV used.
  The value is constant across folds (LOO median 3.36e-3 to 3.55e-3), so it is not driven by any
  held-out participant, but its provenance is disclosed as a limitation of the exploratory
  bipolar analysis.
- **Also disclosed** (audit C4): training-set sizes (Decisions 6, 8) were calibrated on held-out
  folds 1 and 7 before the confirmatory runs.
- **Date**: 2026-09-21

## Decision 18: H1 Holm correction (plan requirement not implemented) added post hoc
- **Finding**: the frozen plan specifies Holm within each confirmatory family (H1-H4);
  `scripts/28_statistics.py` reported unadjusted per-k intervals for H1.
- **Decision**: add the plan-conformant analysis (one-sided cluster-bootstrap p for
  H0: mean Delta_k <= -delta, Holm over the 15 tested k, alpha = 0.025) in
  `scripts/37_secondary_statistics.py` step `h1holm`; report it as a deviation. k* is unchanged
  (14 / 12 / 11 at delta = 0.01 / 0.02 / 0.03). The fixed-sequence argument in the previous text
  was not prespecified and is reported only as a post-hoc sensitivity analysis.
- **Date**: 2026-09-21

## Decision 19: putEMG added as a second external replication (exploratory, not in the frozen plan)
- **Status**: added 2026-09-21 at the user's request, AFTER all GRABMyo and DB5 results existed.
  It is exploratory and reported as such; it cannot confirm or refute H1.
- **Design fixed before any putEMG model was fitted** (integrity audit only: reports/putemg_audit.md):
  - Data: all 264 gesture files (44 participants x 2 sessions x 3 trajectories), pooled over
    sessions and trajectories; participant is the unit; LOSO over 44.
  - Classes: the 7 active gestures (TRAJ_GT in {1,2,3,6,7,8,9}); idle (0) and rejected (-1)
    samples excluded, as rest was excluded for GRABMyo and DB5. Windows lie entirely inside one
    contiguous active label run.
  - Preprocessing: ADC -> mV (N x 5/4096 x 1000/200); 20-450 Hz 4th-order zero-phase band-pass;
    50 Hz notch (Q = 30; audit ratio 66.7 at 50 Hz vs 7.05 at 60 Hz); 250 ms windows (1280 samples
    at the nominal 5120 Hz), 50% overlap; the same 10 features per channel (240 features).
  - Count-feature threshold: same rule (1.15 x median |first difference|, one significant figure)
    but computed on the FILTERED signal, because raw putEMG differences are quantised at one ADC
    step (6.10e-3 mV), which is the raw median itself and carries no scale information. The rule
    is verified leave-one-participant-out before features are extracted; extraction aborts if any
    fold would give a different threshold.
  - Model: same XGBoost (300 trees, depth 6, lr 0.1, subsample/colsample 0.8, hist); training on all
    outer-training windows, or a stratified 200k subsample if there are more (same cap as the
    GRABMyo curve). No hyperparameter or budget calibration on putEMG.
  - Ranking: cross-fitted TreeSHAP, 5 participant-disjoint inner folds, lambda in {0,0.25,0.5,1};
    sparse curve on lambda = 0 for k = 1..24; reference = k = 24 of the same curve.
  - Non-inferiority: same bootstrap (10,000 participant resamples, seed 20260728), delta 0.02
    primary (0.01, 0.03 sensitivity), k* = min{k < 24: LCB > -delta}, plus Holm over the 23 k.
  - Random-subset comparison: 10 random subsets per participant at k in {6, 12, 18}
    (seed 20260728 + participant), Wilcoxon of ranked minus mean-random, Holm over 3.
  - Montage caveat: 24 electrodes in 3 rings of 8, so k values are not comparable with GRABMyo's 16;
    retained fractions are reported descriptively only.
- **Date**: 2026-09-21
- **Compute note (2026-09-21, before any putEMG result was inspected beyond one timing fold)**:
  one fold takes ~11 min on the GPU, so the 44 folds are run as 3 independent shards
  (`--shard i/3`, participants[i::3]) and merged (`--merge 3`). Each fold's computation is unchanged
  (same data, seed and parameters). The timing fold (participant 3) was discarded and recomputed
  inside its shard.

## Decision 20: Bipolar analysis re-run with the rule-derived count-feature threshold
- **Finding**: the bipolar threshold 5e-3 mV was stated as 1.15 x a median of 4.35e-3 mV that could
  not be reproduced. The documented rule on the documented probe records gives 1.15 x 3.40e-3 ->
  4e-3 mV (identical in all 43 leave-one-out folds; scripts/39_loo_threshold_check.py).
- **Decision**: bipolar features re-extracted with 4e-3 mV (scripts/35) and the exploratory bipolar
  analysis (scripts/36) re-run unchanged otherwise. The 5e-3 mV outputs are archived in
  `_archive_invalid/bipolar_threshold_5e-3/`. Results text for the bipolar analysis was written as
  outcome-branching templates before the re-run finished.
- **Date**: 2026-09-22

## Decision 21: XGBoost chronology stated precisely in the manuscript
- The analysis plan (committed 2026-08-12 20:48) designated XGBoost as the primary model before the
  full-cohort classifier comparison finished (XGBoost results 21:33, SVM/RF 23:08); a superseded
  15-participant partial run existed. The manuscript states the computational rationale (Decision 9)
  and no longer describes XGBoost as the highest-scoring model in Methods.
- **Date**: 2026-09-22

## Decision 22: Participant-level cross-fitted attribution extension
- Date: 2026-09-22; post hoc, after original H1-H4 outcomes existed.
- Fold pooling masks between-person variation. Add equal-person median and unscaled MAD of the
  saved normalised out-of-fold attribution vectors. Require every outer-training participant.
- Report all original lambda candidates and all k, without selecting by outer performance.
- The protocol is `configs/statistics/participant_attribution_extension.json`; isolated outputs
  are `artifacts/participant_attribution/`. This does not retrospectively replace frozen H3.
- Exact identical-subset evaluations may be reused only under the same fitting protocol.

## Decision 23: Completion and provenance defects
- Date: 2026-09-22. Corrected bipolar run was incomplete despite COMPLETE status. Resume it.
- Strengthen the publication gate to reconstruct rankings, check outer exclusion and match
  evaluated subsets to their own outer-training rankings; reject missing/duplicate/nonfinite cells.
- Reconstruct full-channel metrics from predictions and replace the hard-coded leakage audit.
- An outer participant had unequal scores for identical selected sets across lambdas. Recompute
  its entire curve with shared unique-subset fitting; retain the previous file in the archive.
- Remove stale six-electrode claims and use the current IOP manuscript build. Historical test-fold
  budget calibration remains disclosed and prevents an unconditional zero-leakage assertion.

## Decision 24: Completion analyses specified before execution (2026-09-30)
- Status: post hoc in timing (all primary H1-H4 outcomes were known), but every rule below was
  written BEFORE any of these three analyses was run. All outcomes are reported whatever they are.
  Outputs are isolated in `artifacts/completion_analyses/`; no primary artifact is replaced.
- (a) Fixed-layout check with the primary ranking. Re-run the existing single-split check
  (dev = odd-numbered, test = even-numbered participants; same code, seed, attribution settings
  and XGBoost configuration as `scripts/audit_fixed_population_layout.py`) and derive the
  12-electrode layout from lambda = 0 (primary). Also report lambda = 0.25, 0.5, 1 layouts, and the
  swapped split (dev = even, test = odd) as a second single-split check. Decision rule: 95%
  participant-bootstrap LCB of (12 - 16) > -0.02. The lambda = 0.5 dropped set {3, 9, 11, 12} must
  be reproduced from the rerun, otherwise the rerun is not comparable and is reported as such.
- (b) 17-class task including Rest (plan secondary endpoint). Same 250 ms features; labels 1-17.
  Electrode rankings are reused from the primary outer folds (lambda = 0; computed on the 16 active
  gestures from outer-training participants only), so the selected electrodes do not change.
  Performance-curve protocol unchanged (XGBoost 300 trees, stratified 200,000 training windows,
  per-fold standardisation), k = 1..16. k* = min{k < 16 : LCB95 > -delta} against the k = 16 model
  of the same task, delta = 0.02 primary, 0.01 and 0.03 sensitivity; Holm as in H1 also reported.
- (c) Window-length sensitivity (plan exploratory list): 150 ms and 500 ms, 50% overlap, identical
  filtering, features and count thresholds; re-extracted from the raw records. Rankings reused from
  the primary 250 ms analysis (lambda = 0), so this tests the sensitivity of the reduced-model
  comparison to window length, not the sensitivity of the ranking. Same curve protocol and k* rule.
- Not run: CNN/integrated gradients, mRMR (not part of the executed comparison set).

## Decision 25: Scientific manuscript revision, 2026-10-14
- New analyses are exploratory and are governed by `manuscript_revision/20261014/reproducibility/exploratory_protocol.json`.
- Preserve September sources and existing results. Obtain primary-budget predictions for participant and gesture degradation and evaluate geometric12 against the same full-array reference.
- Shared-model SHAP and grouped-electrode permutation comparison uses common participant-disjoint inner models and validation observations, reporting computational costs.
- Complete the previously planned 150-ms curve and missing 500-ms fold; retain the already-completed Rest17 curve. Full 150-ms coverage was chosen before its outcomes became available (protocol amendment01).
- Preserve original percentile inference and audit a null-centred studentised bootstrap sensitivity; never choose a seed or margin from outcomes.
- No independent same-montage cohort is available for prospective fixed-layout validation. Ethics remains unresolved by prior user instruction.
