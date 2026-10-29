# STATUS

**Overall state: COMPLETE. Manuscript built from verified artifacts; `bash scripts/build_manuscript.sh`
passes end to end.** Last updated: 2026-09-21. Deliverables: `FINAL_PACKAGE/`, `FINAL_STUDY_REPORT.md`.

The 2026-08-14/15 orchestrated run and the 2026-09-14 manuscript were audited on 2026-09-21.
Two analyses were invalid and have been recomputed. The previous manuscript contained numbers
matching no artifact, a macro generator with literal values, and 14 bad citations. All are
documented in `reports/decision_log.md` (Decisions 11–16) and archived under `_archive_invalid/`.

## Experiments

| Phase | State | Evidence |
|---|---|---|
| P1 full-channel LOSO (XGB/SVM/RF) | complete, 43/43 | `artifacts/metrics/loso_full_channel_*` |
| P2 cross-fitted attribution | complete, 43/43 | `artifacts/rankings/` |
| P3 sparse curve k = 1..16 × 4 λ | complete, 2,752 fits | `artifacts/metrics/sparse_curve_subject_metrics.csv` |
| P4 selection baselines (H2) | complete, 43/43 | `artifacts/selection_baselines/` |
| P5 non-inferiority (H1) | complete: k* = 12 (δ 0.02), 14 (0.01), 11 (0.03), identical for all λ | `artifacts/statistics/` |
| H2 / H3 / H4 statistics | complete | `artifacts/statistics/h2_*`, `h3_*`, `h4_*` |
| P6 ranking stability | complete | `artifacts/stability/` |
| P7 cross-session | complete (exploratory) | `artifacts/cross_session/`, `statistics/cross_session_tests.csv` |
| P8 faithfulness | **recomputed 2026-09-21** under one protocol; order holds at every k | `artifacts/faithfulness/` |
| P9 DB5 | complete (exploratory); k = 12 on the margin, fragile | `artifacts/db5/`, `statistics/db5_*` |
| P10 CNN / cross-model attribution | **not run** (disclosed) | — |
| P11 bipolar | **recomputed 2026-09-21** (exploratory): no pair removable at δ 0.02; k* = 7 at δ 0.03 | `artifacts/bipolar/`, `statistics/bipolar_*` |
| Feature redundancy (IEMG) | **complete, 43 folds**: Δ −0.0005, channel-rank ρ 0.994 | `artifacts/sensitivity/` |
| Fixed layout (post hoc) | complete, one split | `artifacts/fixed_layout/` |

## Manuscript
- `manuscript/main_elsevier.tex` + `sections/`: rewritten 2026-09-21.
- Numbers: `scripts/40_generate_macros.py` (hard-fails on missing input), tables:
  `scripts/42_generate_tables.py`, figures: `scripts/44_figures.py`, number checker:
  `scripts/45_check_manuscript_numbers.py`.
- Bibliography: `scripts/build_verified_bib.py` (35 registry-verified entries).
- Audits: `reports/reviewer2_audit.md`, `reports/physiology_reviewer_audit.md`.

## Headline findings (confirmatory)
- H1 supported: 12 of 16 electrodes non-inferior at δ = 0.02; 11 not.
- H2 supported vs random; exploratory: the geometric and permutation baselines match attribution at most k.
- H3 not supported: the stability penalty changes almost no rankings.
- H4 supported: deletion ordering top < random < bottom at every k.
