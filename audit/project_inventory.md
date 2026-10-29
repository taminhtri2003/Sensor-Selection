# Comprehensive Project Inventory & Artifact Provenance

**Audit Date:** 2026-09-14  
**Project:** Stability and Generalization of Explainability-Guided Sensor Selection in Subject-Independent sEMG Gesture Recognition  
**Primary Dataset:** GRABMyo v1.1.0 ($N=43$, 3 sessions, 16 active gestures, 563,472 windows)  
**External Dataset:** NinaPro DB5 ($N=10$, dual Myo armbands, 12 classes, 200 Hz)  
**Analysis Plan:** Frozen pre-specified plan in `configs/statistics/frozen_analysis_plan.yaml` (Date: 2026-08-12, Seed: 20260728)  

---

## 1. Directory Structure Overview

| Directory / File | Type | Description / Role |
| :--- | :--- | :--- |
| `configs/` | Directory | Pre-specified protocol and configuration files (`frozen_analysis_plan.yaml`). |
| `data/raw/` | Directory | Downloaded public data for GRABMyo and NinaPro DB5. |
| `data/manifests/` | Directory | SHA-256 file manifests (`grabmyo_integrity.csv`, `db5_manifest.csv`). |
| `data/metadata/` | Directory | Subject demographics, class mappings, recording metadata. |
| `data/features/` | Directory | Extracted 10 time-frequency features in Parquet format + extraction QC logs. |
| `data/cache/` | Directory | Fast memory-mapped arrays (`loso_X.npy`, `loso_y.npy`, `loso_subj.npy`, `loso_sess.npy`, `loso_features.json`). |
| `scripts/` | Directory | Master end-to-end Python pipeline scripts (numbered 05 to 43). |
| `artifacts/` | Directory | Output metrics, model checkpoints, TreeSHAP values, bootstrap tables, figures. |
| `reports/` | Directory | Study progress reports, decision logs, data integrity reports. |
| `manuscript/` | Directory | LaTeX manuscript sources (`main_elsevier.tex`, `main.tex`, sections, tables, figures). |
| `FINAL_DELIVERY/` | Directory | Compiled camera-ready PDFs and slide decks. |
| `slides/` | Directory | LaTeX Beamer and interactive HTML5 presentations. |
| `audit/` | Directory | Audit logs, numerical traces, leakage reports, citation checks. |
| `results/` | Directory | Single source of truth canonical CSV and JSON data tables. |
| `figures_final/` | Directory | Redesigned camera-ready vector figures. |

---

## 2. Script Inventory & Pipeline Dependencies

```
[Raw Data] 
    │
    ▼
20_extract_features_full.py ──► data/features/grabmyo_features_full.parquet
    │
    ▼
data/cache/ (loso_X.npy, loso_y.npy, loso_subj.npy, loso_sess.npy)
    │
    ├─► 21_full_channel_loso.py ──► artifacts/metrics/full_channel_loso_metrics.csv
    │
    ├─► 25_cross_fitted_ranking.py ──► artifacts/rankings/ (checkpoints outer_01..43.json)
    │                                  artifacts/rankings/cross_fitted_rankings.csv
    │                                  artifacts/rankings/per_subject_attribution.csv
    │
    ├─► 26_sparse_sensor_curve.py (P3 Headline: 300 trees, full 550k) ──► artifacts/metrics/sparse_curve_subject_metrics.csv
    │                                                                   artifacts/tables/table3_sparse_performance.csv
    │
    ├─► 27_selection_baselines.py (Exploratory: 50 trees, 150k sub) ──► artifacts/selection_baselines/selection_baseline_metrics.csv
    │                                                                  artifacts/selection_baselines/selection_baseline_summary.csv
    │
    ├─► 29_stability.py ──► artifacts/stability/stability_summary.csv, per_subject_agreement.csv
    │
    ├─► 30_cross_session.py ──► artifacts/cross_session/cross_session_metrics.csv
    │
    ├─► 31_faithfulness.py ──► artifacts/faithfulness/deletion_curves.csv, faithfulness_summary.csv
    │
    ├─► 33_db5_features.py & 34_db5_replication.py ──► artifacts/db5/db5_sparse_curve.csv, db5_summary.csv
    │
    ├─► 35_extract_bipolar_features.py & 36_bipolar_sensitivity.py ──► artifacts/bipolar/bipolar_sparse_curve.csv
    │
    ├─► 28_statistics.py ──► artifacts/statistics/master_statistics.csv
    │
    └─► 16_verify_results.py & 40_generate_macros.py ──► manuscript/generated/results_macros.tex
```

---

## 3. Artifact Provenance: Manuscript Tables & Figures

| Manuscript Item | Displayed Content | Generating Script | Input Artifacts |
| :--- | :--- | :--- | :--- |
| **Table 1** | Prior literature comparison | Manual LaTeX | `manuscript/sections/02_related_work.tex` |
| **Table 2** | Feature extraction definitions | Manual LaTeX | `manuscript/sections/03_methods.tex` |
| **Table 3** | Full-channel baseline models | `scripts/28_statistics.py` | `artifacts/statistics/master_statistics.csv` |
| **Table 4** | Sparse sensor curve ($k=1..16$) & non-inferiority | `scripts/26_sparse_sensor_curve.py` + `28_statistics.py` | `artifacts/tables/table3_sparse_performance.csv` |
| **Table 5** | Selection baseline comparisons | `scripts/27_selection_baselines.py` | `artifacts/selection_baselines/selection_baseline_summary.csv` |
| **Table 6** | Attribution stability metrics | `scripts/29_stability.py` | `artifacts/stability/stability_summary.csv` |
| **Figure 1** | Study overview & experimental design | `scripts/generate_rich_figure1.py` | Vector layout + Panel C SR-CFA formulation card |
| **Figure 2** | Model cell & TreeSHAP aggregation architecture | `scripts/generate_transformer_figure2.py` | PyTorch/XGBoost feature tensor schematic |
| **Figure 3** | Full-channel baseline distributions | `scripts/14_generate_figures.py` | `artifacts/statistics/master_statistics.csv` |
| **Figure 4** | Primary sparse curve & paired differences | `scripts/14_generate_figures.py` | `artifacts/tables/table3_sparse_performance.csv` |
| **Figure 5/6**| Attribution stability profiles & hubs | `scripts/14_generate_figures.py` | `artifacts/stability/` |

---

## 4. Stale Folders, Duplicate Results & Version Drift Identified

1. **Table 4 vs Table 5 Protocol Divergence:**
   - `artifacts/tables/table3_sparse_performance.csv` (used in Table 4) is from the primary headline model: XGBoost with 300 trees trained on the full fold training set ($\sim 550{,}368$ windows).
   - `artifacts/selection_baselines/selection_baseline_summary.csv` (used in Table 5) is from a matched-budget exploratory benchmark: XGBoost with 50 trees and 150,000 subsampled training windows.
   - *Status:* Both exist and are mathematically valid within their own protocols, but Table 5 was presented without clarifying the lighter comparison budget!

2. **Abstract LCB Value Inconsistency:**
   - Abstract in `manuscript/main_elsevier.tex` hardcoded `-0.0152` from an earlier draft, whereas Table 4 and `\OptimalKLCB` report `-0.0160`.
   - *Resolution:* Align to `-0.0160` (canonical bootstrap value).

3. **ROAR Monotonicity Violation:**
   - Text claimed $\text{F1}_{\text{remove-top}} \le \text{F1}_{\text{remove-random}} \le \text{F1}_{\text{remove-bottom}}$ for all $k$.
   - At $k=12$ (4 channels removed), empirical data show $\text{F1}_{\text{remove-top}} = 0.488 > \text{F1}_{\text{remove-random}} = 0.478$.
   - *Status:* Data show partial faithfulness at coarse deletion ($k=4, 12$) and strict ordering at moderate deletion ($k=6, 8$). Must be honestly reported.

4. **Bipolar Non-Inferiority Claim:**
   - Previous discussion asserted $k^*=6$ pairs are non-inferior.
   - Empirical audit proves $k=6$ pairs has $\Delta = -0.0373$ and $\text{LCB} = -0.0453 \le -0.020$ (FAILS non-inferiority).
   - The minimal non-inferior bipolar subset is $k^* = 7$ pairs ($\text{LCB} = -0.0191 > -0.020$).
   - *Status:* Correct $k^*$ for bipolar from 6 to 7 pairs.

5. **NinaPro DB5 Boundary:**
   - At $k=12$, unrounded bootstrap LCB is $-0.020254 \le -0.020000$.
   - *Status:* Technically fails the strict $\delta=0.0200$ threshold; must be described with 4-5 decimals as a boundary result.
