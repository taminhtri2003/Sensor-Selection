# Reproducing the study

Everything in the manuscript is regenerated from result files by one command. The experiments
that produce those files are listed below in dependency order.

## Environment (as actually used)
- Conda env `graph_gpu`: Python 3.10.20, numpy 1.26.4, pandas 2.3.3, scikit-learn 1.7.2,
  scipy 1.15.2, xgboost 3.2.0, matplotlib 3.9.1. The full lock file (229 packages) is
  `reproducibility/requirements-lock-graph_gpu.txt`, and the environment record is
  `reproducibility/environment_graph_gpu.json`.
- `wfdb` is needed only by the GRABMyo readers (scripts 20 and 35). It was run with system Python 3.14.
- GPU: RTX 5060 Ti 16 GB (XGBoost `device="cuda"`). CPU: 12 cores, 32 GB RAM.
- LaTeX: TeX Live 2026 (pdfTeX 1.40.29), `elsarticle`.
- Seed: 20260728 everywhere.

## Data
- GRABMyo v1.1.0 (PhysioNet) in `Session1/`, `Session2/`, `Session3/`. Verify with
  `scripts/audit_grabmyo_integrity.py` (all 30,715 files against `SHA256SUMS.txt`).
- NinaPro DB5: `scripts/22_acquire_db5.py` (download with md5 check), then
  `scripts/23_audit_db5_task.py` and `scripts/32_audit_db5_signal.py`.

## Experiments (dependency order; approximate GPU wall-clock)
| Step | Script | Output | Time |
|---|---|---|---|
| Features | `20_extract_features_full.py`, `33_db5_features.py`, `35_extract_bipolar_features.py` | `data/features/` | ~1 h CPU |
| P1 full-channel LOSO | `24_full_channel_loso_parallel.py` (`--models xgb`, then `svm,rf`) | `artifacts/metrics/loso_full_channel_*` | ~3 h |
| P2 cross-fitted attribution | `25_cross_fitted_ranking.py` | `artifacts/rankings/` | ~2 h |
| P3 sparse curve | `26_sparse_sensor_curve.py` | `artifacts/metrics/sparse_curve_*` | ~1.5 h |
| P4 selection baselines | `27_selection_baselines.py --k-values 4,6,8,12 --n-random 100 --n-random-at-k-star 500 --k-star 12 --srcfa-lambda 0.5` | `artifacts/selection_baselines/` | ~4.5 h |
| P6 stability | `29_stability.py` | `artifacts/stability/` | minutes |
| P7 cross-session | `30_cross_session.py` | `artifacts/cross_session/` | ~45 min |
| P8 faithfulness | `31_faithfulness.py` (requires P4) | `artifacts/faithfulness/` | ~30 min |
| P9 DB5 | `34_db5_replication.py` | `artifacts/db5/` | not recorded |
| P11 bipolar | `36_bipolar_sensitivity.py` | `artifacts/bipolar/` | ~3 h |
| Redundancy | `38_feature_redundancy.py` | `artifacts/sensitivity/` | ~8 min |
| Fixed layout (post hoc) | `audit_fixed_population_layout.py` | `artifacts/fixed_layout/` | not recorded |

Run GPU steps one at a time; concurrent CUDA processes starve each other.

## Statistics, numbers, figures, PDF
```bash
bash scripts/build_manuscript.sh
```
This runs the tests, the completeness audit, `28_statistics.py` (frozen plan), and
`37_secondary_statistics.py` (H2–H4 and the exploratory analyses). It then runs the macro
generator (hard-fails on missing input), the table and figure generators, the manuscript number
checker, the claim–evidence matrix, and pdflatex/bibtex.

## Governance files
- `configs/statistics/frozen_analysis_plan.yaml`: decision rules frozen 2026-08-12.
- `reports/decision_log.md`: every deviation and correction (Decisions 1–16).
- `reports/claim_evidence_matrix.csv`, `manuscript/generated/macro_provenance.csv`: numbers mapped to files.
