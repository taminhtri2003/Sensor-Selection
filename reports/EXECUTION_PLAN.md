# Execution plan — sparse sEMG sensor selection study

Version 1, 2026-08-12. Supersedes nothing: the prior study package is invalid and quarantined in
`_archive_invalid/`. This plan governs the rebuild.

**Governing rule:** no manuscript sentence is written before the number it cites exists in a
result file. Every phase below names the artefact it must produce; a phase that produces no
artefact has not happened, regardless of what any summary says.

---

## 0. Where things stand

### Verified and done

| Item | Evidence |
|---|---|
| GRABMyo raw integrity — 30,715/30,715 files match official SHA256SUMS | `reports/grabmyo_integrity.md` |
| Feature extraction, complete cohort — 15,351/15,351 records, 598,689 windows, 0 failures | `reports/feature_extraction_report.md` |
| Mains frequency = 50 Hz, measured not assumed (10.35 vs 0.62 band-power ratio) | `reports/signal_properties_audit.md` |
| Electrode montage = 2 rings × 8; 16 monopolar = 8 bipolar pairs | `reports/grabmyo_electrode_geometry.md` |
| WAMP saturation defect found and fixed (median 509/511 → 312/511) | `src/semg_sparse/features/handcrafted.py` |
| DB5 acquired — 10/10 archives md5-verified, 30 .mat files structurally OK | `reports/db5_integrity.md` |
| DB5 cohort derived from data — 10 subjects, 8M/2F, age 28.0 ± 4.0 | `reports/db5_task_audit.md` |
| Prior package audited — 28 claims, 21 CRITICAL failures | `reports/current_manuscript_claim_audit.csv` |

### In flight

- Full-channel LOSO, XGB + SVM, 43 folds, 4 workers → `runs/loso_xgb_svm.log`
- RF cost/accuracy calibration on a fixed fold (decides RF config)

---

## 1. Frozen protocol

These are fixed now and may not be changed after seeing results. Any later change must be logged
in `reports/decision_log.md` with its justification and the results re-run.

| Element | Value | Basis |
|---|---|---|
| Primary dataset | GRABMyo v1.1.0, 43 participants × 3 sessions | brief |
| Channels | 16 monopolar forearm (F1–F16) | brief; parity with DB5 |
| Primary task | 16 active gestures, Rest (17) excluded | rest dominates and inflates accuracy |
| Secondary task | 17 classes incl. Rest | reported separately |
| Filtering | 20–450 Hz Butterworth order 4, zero-phase; 50 Hz notch Q=30 | measured PSD |
| Window | 250 ms, 50% overlap, never crossing trial boundaries | brief; standard latency budget |
| Features | 10/channel: MAV, RMS, VAR, WL, ZC, SSC, IEMG, WAMP, MNF, MDF | thresholds set from measured amplitude |
| Outer validation | LOSO by participant, 43 folds | participant is the statistical unit |
| Inner validation | 5-fold GroupKFold by participant, within outer-training only | leakage control |
| Primary metric | Macro-F1 | class balance; accuracy reported secondarily |
| Primary model | XGBoost (GPU) | fast enough for the combinatorial sweeps |
| Seed | 20260728 | — |
| Non-inferiority margin | δ = 0.02 Macro-F1, sensitivity at 0.01 / 0.03 | engineering tolerance, **not** clinical |
| Bootstrap | participant-level cluster bootstrap, 10,000 resamples | never window-level |

**Pre-registration discipline:** δ is fixed *before* the sensor curve is seen. If no k meets it,
that is the finding — the margin does not get loosened afterwards.

---

## 2. Phases

Compute estimates assume RTX 5060 Ti + 12 cores, and are wall-clock with fold parallelism.

### P1 — Full-channel baseline `[in flight]`

- **Script:** `scripts/24_full_channel_loso_parallel.py`
- **Models:** XGBoost, SVM (40k stratified subsample — RBF is O(n²), documented as a compute
  constraint), Random Forest (config pending calibration)
- **Out:** `artifacts/metrics/loso_full_channel_{subject_metrics,summary}.csv`,
  `artifacts/predictions/loso_full_channel_predictions.parquet`
- **Estimate:** ~45 min (XGB+SVM), +1–2 h (RF)
- **Gate:** every model must cover all 43 participants or the run fails loudly.

### P2 — Cross-fitted attribution + SR-CFA ranking

- **Script:** `scripts/25_cross_fitted_ranking.py` *(written, queued)*
- 43 outer folds × 5 inner folds; attribution computed only on inner-held-out subjects via
  XGBoost native `pred_contribs` on GPU
- **Out:** `cross_fitted_importance_long.csv` (per outer fold × inner fold × channel),
  `cross_fitted_scores.csv` (A_c, U_c, Q_c(λ)), `cross_fitted_rankings.csv`
- **Estimate:** ~2–3 h
- **Gate:** outer participant absent from every inner fold's attributed subjects (asserted in code).

### P3 — Sparse sensor curve

- **Script:** `scripts/26_sparse_sensor_curve.py` *(to write)*
- For each outer fold p and each k ∈ 1…16: take top-k of R₋ₚ, **retrain from scratch**, evaluate on p
- Primary model XGBoost for all k; confirmatory k ∈ {4,6,8,10,12,16} for SVM/RF
- Cost falls with k (k channels → 10k features), so this is cheaper than 16× the baseline
- **Out:** `artifacts/metrics/sparse_curve_subject_metrics.csv`
- **Estimate:** ~3–4 h
- **Gate:** the channel subset for fold p must be derivable from R₋ₚ alone.

### P4 — Selection baselines

- **Script:** `scripts/27_selection_baselines.py` *(to write)*
- Compared against SR-CFA at matched k:
  - B1 mean SHAP magnitude (λ=0) — the ablation that decides whether stability regularisation earns its place
  - B2 permutation importance
  - B3 mutual information
  - B4 mRMR (if a reliable implementation is available; otherwise reported as omitted)
  - B5 random subsets — ≥100 per k, 500 at k\*
  - B6 geometric/equispaced — algorithmic farthest-point over the 2×8 montage, never hand-picked
- **Out:** `artifacts/selection_baselines/*.csv`
- **Estimate:** ~4–6 h (random baseline dominates)
- **This phase can sink the headline.** If random subsets match SR-CFA, the XAI framing is dead and
  the paper becomes a negative result about attribution-guided selection.

### P5 — Non-inferiority and statistics

- **Script:** `scripts/28_statistics.py` *(to write)*
- Δ_{p,k} = F1_{p,k} − F1_{p,16}; participant-level cluster bootstrap, 10,000 resamples
- k\* = min{k : LCB₉₅(Δ_k) > −δ}; sensitivity at δ ∈ {0.01, 0.02, 0.03}
- Paired model comparisons with Holm correction; confirmatory vs exploratory families separated
- **Out:** `artifacts/statistics/master_statistics.csv`, bootstrap distributions
- **Estimate:** <30 min
- **Prerequisite:** `configs/statistics/frozen_analysis_plan.yaml` committed *before* this runs.

### P6 — Stability analysis

- **Script:** `scripts/29_stability.py` *(to write)*
- Cross-subject: Spearman ρ, Kendall τ, Jaccard@k, selection frequency, rank MAD across the 43 R₋ₚ
- Cross-session: rankings derived separately from session 1, 2, 3 training data; compared
- **Out:** `artifacts/stability/*.csv`
- **Estimate:** ~1 h (reuses P2 attributions) + ~2 h for session-specific rankings

### P7 — Cross-session generalisation

- **Script:** `scripts/30_cross_session.py` *(to write)*
- CS1: train on session 1 → test held-out participant on sessions 1, 2, 3
- CS2: train on sessions 1+2 → test on session 3
- CS3: per-session ranking comparison (feeds P6)
- **Out:** `artifacts/cross_session/*.csv`
- **Estimate:** ~2–3 h
- Language discipline: "cross-session stability", never "test–retest reliability".

### P8 — XAI faithfulness

- **Script:** `scripts/31_faithfulness.py` *(to write)*
- Deletion curves: remove top-ranked / random / bottom-ranked channels first, retrain, evaluate
- Faithful attribution requires P_top-removed < P_random < P_bottom-removed, with CIs
- **Out:** `artifacts/faithfulness/*.csv`
- **Estimate:** ~3 h

### P9 — DB5 external replication

- **Scripts:** `scripts/32_db5_features.py`, `scripts/33_db5_replication.py` *(to write)*
- DB5-appropriate preprocessing: fs = 200 Hz, so the 20–450 Hz band is impossible — Nyquist is
  100 Hz. Use a DB5-specific band (≈10–90 Hz), stated as a difference, never copied from GRABMyo.
- Task: E1, 12 movements, `restimulus`/`rerepetition` labels; rest excluded from primary
- Same conceptual pipeline: LOSO over 10 subjects → cross-fitted ranking → k = 1…16 curve →
  non-inferiority → random + geometric baselines
- **Out:** `artifacts/db5/*.csv`
- **Estimate:** ~2–3 h (dataset is far smaller)
- **Claim discipline:** methodological replication only. No channel-location transfer between
  datasets — different hardware, different montage, different movement set.

### P10 — Compact 1D CNN + Integrated Gradients *(conditional)*

- Raw channel × time tensors, **no pseudo-RGB conversion**
- IG-based channel attribution compared against XGBoost SHAP ranking (cross-model agreement)
- **Estimate:** ~6–10 h on CUDA torch
- **Condition:** run only if P1–P9 land cleanly with time remaining. If cut, say so explicitly
  rather than implying it was done.

### P11 — Bipolar sensitivity analysis

- Derive 8 bipolar channels (F_j − F_{j+8}), repeat P1/P3 at reduced dimensionality
- Required before any deployment-flavoured claim (see electrode geometry report)
- **Estimate:** ~2 h

### P12 — Literature and novelty freeze

- Target 60–100 relevant papers in `literature/literature_matrix.csv`; 15–25 deep mini-reviews
- `reports/novelty_review.md` decides the framing **before** the abstract is drafted
- Early signal already found: prior EMG work reports *no consistent channel selection across
  subjects*, which may support an instability framing rather than a "k channels suffice" one.

### P13 — Figures, tables, manuscript

- Figures redesigned from scratch (Nature-style, vector PDF/SVG, colour-blind safe, no rainbow
  colormaps, no pseudo-3D); framework figure in TikZ
- All numbers via generated LaTeX macros; `scripts/verify_manuscript_numbers.py` rewritten so a
  **missing result file is a hard failure** — never a defaulted constant, which is precisely how
  the previous manuscript came to contain invented numbers
- Two builds: Elsevier two-column, and target-journal format
- `results/RESULTS_FROZEN` written before abstract/discussion drafting

### P14 — Adversarial audits

- `reports/reviewer2_audit.md` — hostile methodological review
- `reports/physiology_reviewer_audit.md` — measurement/physiology review
- `reports/claim_evidence_matrix.csv` — rebuilt honestly; abstract and conclusion may contain
  only `SUPPORTED` claims

---

## 3. Decision gates

| Gate | Test | If it fails |
|---|---|---|
| G1 | Full-channel Macro-F1 meaningfully above chance (0.0625) | Investigate features/protocol before proceeding |
| G2 | SR-CFA (λ>0) beats mean-SHAP (λ=0) in the P4 ablation | Drop SR-CFA from the title; reposition as an evaluation study |
| G3 | SHAP-guided selection beats random subsets | Headline becomes a negative result — report it |
| G4 | Some k < 16 is non-inferior at δ = 0.02 | Report that reduction fails within the prespecified tolerance |
| G5 | Rankings stable across subjects and sessions | Reframe around instability limiting fixed sparse layouts |
| G6 | DB5 replicates methodologically | Report as an external boundary of generalisability |

None of these gates is allowed to be resolved by adjusting the criterion after seeing the result.

---

## 4. Contingency framings

The paper has a defensible form under every outcome. Chosen by evidence, not preference:

1. **Everything works** → "Stability-Regularized Cross-Fitted Attribution for Sparse
   Subject-Independent sEMG Gesture Recognition"
2. **SR-CFA ≈ mean SHAP** → drop the acronym; "Stability and Generalisation of
   Explainability-Guided Sensor Selection in sEMG"
3. **XAI ≈ random** → negative result: attribution-guided selection offers no advantage over
   random or geometric placement at matched sensor count
4. **No non-inferior k** → importance is concentrated but reduction does not preserve
   subject-independent performance within tolerance
5. **Rankings drift across sessions** → attribution instability limits fixed sparse electrode
   layouts; uniform placement may be the more robust engineering choice

---

## 5. Risk register

| Risk | Mitigation |
|---|---|
| Compute overrun on P4 random baselines | Cost scales with k; cap at 100 subsets/k, 500 at k\*, and **log what was capped** |
| GPU contention between concurrent phases | Serialise GPU-bound phases; CPU phases may overlap |
| SVM subsampling asymmetry vs tree models | State explicitly; if SVM wins, note it was trained on less data |
| Silent stage failure (the original defect) | Every script asserts realised cohort vs expected and exits non-zero |
| Numbers drifting between artefacts and manuscript | Single macro generator, hard-fail on missing inputs |
| Monopolar/bipolar ambiguity in claims | P11 sensitivity analysis; unit named in every claim |
| Over-reach on physiology | No muscle attribution; conservative spatial language only |

---

## 6. Definition of done

The study is publication-ready only when all of the following hold, each with a named artefact:
raw integrity PASS · leakage tests PASS · full-channel baseline · nested sensor selection ·
selection baselines incl. random and geometric · non-inferiority with prespecified δ · stability
(subject + session) · faithfulness · DB5 replication · frozen statistics · literature matrix ·
novelty review · redesigned figures · TikZ framework · both LaTeX builds · verified references ·
numerical consistency check · Reviewer #2 audit · physiology audit · final PDF visual audit.

Anything short of that stays labelled **DRAFT — NOT PUBLICATION READY**.
