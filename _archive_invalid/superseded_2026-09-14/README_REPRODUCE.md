# Reproduction Guide: Stability and Generalization of Explainability-Guided Sensor Selection in Subject-Independent sEMG Gesture Recognition

This guide provides complete, step-by-step instructions to reproduce all empirical findings, statistical tables, publication figures, and compiled LaTeX manuscripts from raw data.

---

## 1. System Requirements & Environment Setup

### 1.1 Hardware Specifications
- **Operating System**: Windows 11 / Linux (Ubuntu 22.04 LTS recommended)
- **CPU**: Multi-core processor (16+ logical cores recommended for LOSO multiprocessing)
- **RAM**: 32 GB minimum (64 GB recommended for out-of-fold feature arrays)
- **GPU**: NVIDIA CUDA-enabled GPU (RTX 3080/4090 or A100, 8+ GB VRAM) for GPU-accelerated XGBoost (`tree_method='hist'`, `device='cuda'`) and fast TreeSHAP attribution.

### 1.2 Python Environment
Create and activate a conda environment with Python 3.10:

```bash
conda create -n srcfa_semg python=3.10 -y
conda activate srcfa_semg
```

Install core dependencies:
```bash
pip install numpy==1.26.4 scipy==1.13.1 pandas==2.2.2 scikit-learn==1.4.2 \
            xgboost==3.2.0 shap==0.49.1 matplotlib==3.8.4 seaborn==0.13.2 \
            pyyaml==6.0.1 tqdm==4.66.4 h5py==3.11.0
```

Verify LaTeX installation for manuscript compilation:
```bash
pdflatex --version
bibtex --version
```

---

## 2. Dataset Acquisition and Integrity Verification

### 2.1 Primary Benchmark: GRABMyo v1.1.0
Download the GRABMyo dataset from PhysioNet:
- URL: `https://physionet.org/content/grabmyo/1.1.0/`
- Target Directory: `data/raw/grabmyo/`
- Contains recordings from 43 healthy participants across 3 sessions separated by $\ge 7$ days (15,351 records).

### 2.2 Replication Benchmark: NinaPro DB5
Download Dataset 5 (DB5) from the NinaPro repository:
- URL: `http://ninapro.hevs.ch/`
- Target Directory: `data/raw/ninapro_db5/`
- Contains recordings from 10 intact participants performing Exercise 1 with dual Thalmic Myo armbands (200 Hz).

### 2.3 Checksum Verification
Run the integrity verification script to ensure byte-level identity against upstream repository checksums:
```bash
python scripts/00_verify_checksums.py
```
Expected output:
```
[PASS] 30,715 files verified matching SHA256SUMS (0 corrupted, 0 missing).
```

---

## 3. End-to-End Pipeline Execution

All pipeline steps adhere strictly to the **Zero Data Leakage** principle: test participants in outer LOSO folds remain entirely untouched during filtering, feature scaling, model training, and channel ranking.

### Stage 1: Signal Preprocessing and Feature Extraction
Extract 10 time-domain and spectral features per channel using $250\text{ ms}$ sliding windows with $50\%$ overlap ($125\text{ ms}$ stride):
```bash
# Process GRABMyo (598,689 total windows, 563,472 active windows)
python scripts/01_extract_features_grabmyo.py

# Process NinaPro DB5 (86,400 windows)
python scripts/02_extract_features_db5.py
```

### Stage 2: Full-Channel Subject-Independent Baselines
Train and evaluate full 16-channel Leave-One-Subject-Out (LOSO) baselines across XGBoost, RBF-SVM, and Random Forest:
```bash
# Full-cohort XGBoost (300 estimators, ~550k training windows per fold)
python scripts/04_run_loso_xgboost.py

# RBF-SVM (40k subsample budget) and Random Forest (200k subsample budget)
python scripts/05_run_loso_svm_rf.py
```
*Outputs*: `artifacts/metrics/loso_full_channel_subject_metrics_xgb.csv`, `loso_full_channel_subject_metrics_svmrf.csv`

### Stage 3: SR-CFA TreeSHAP Attribution and Stability Ablation
Compute cross-fitted TreeSHAP within $K_{\text{in}} = 5$ inner folds and evaluate the dispersion penalty $\lambda \in \{0.0, 0.25, 0.50, 1.00\}$:
```bash
# Compute inner-fold out-of-fold TreeSHAP attributions
python scripts/06_run_treeshap_srcfa.py

# Evaluate stability metrics and ranking dispersion
python scripts/07_run_stability_ablation.py
```
*Outputs*: `artifacts/rankings/cross_fitted_rankings.csv`, `artifacts/stability/stability_summary.csv`

### Stage 4: Sparse Sensor Selection Curves
Sweep channel counts $k \in \{1, \dots, 16\}$ under the primary configuration ($\lambda = 0.50$):
```bash
python scripts/08_run_sparse_selection_curves.py
```
*Outputs*: `artifacts/metrics/sparse_curve_subject_metrics.csv`

### Stage 5: Participant-Level Non-Inferiority Bootstrap
Evaluate the pre-specified non-inferiority margin ($\delta = 0.02$ Macro-F1) using $10{,}000$ participant cluster bootstrap resamples to identify $k^*$:
```bash
python scripts/09_run_noninferiority_bootstrap.py
```
*Outputs*: `artifacts/statistics/non_inferiority_by_k.csv`, `master_statistics.csv`

### Stage 6: Matched Baseline Selection Sweeps
Benchmark SR-CFA against unregularized SHAP ($\lambda=0$), Permutation Importance, Mutual Information, Geometric sampling, and Random subsets:
```bash
python scripts/10_run_selection_baselines.py
```
*Outputs*: `artifacts/selection_baselines/selection_baseline_metrics.csv`

### Stage 7: Longitudinal Cross-Session Robustness (CS1 & CS2)
Quantify cross-session degradation and multi-day training recovery:
```bash
python scripts/11_run_longitudinal_evaluation.py
```
*Outputs*: `artifacts/cross_session/cross_session_metrics.csv`

### Stage 8: RemOve And Retrain (ROAR) Faithfulness Verification
Evaluate attribution faithfulness by comparing top, bottom, and random channel removal:
```bash
python scripts/12_run_faithfulness_roar.py
```
*Outputs*: `artifacts/faithfulness/deletion_curves.csv`

### Stage 9: Derived Bipolar Montage Sensitivity Analysis
Evaluate the 8 longitudinal differential pairs ($F_j - F_{j+8}$):
```bash
python scripts/13_run_bipolar_evaluation.py
```
*Outputs*: `artifacts/bipolar/bipolar_sparse_curve.csv`

### Stage 10: External Replication on NinaPro DB5
Replicate the selection algorithm on NinaPro DB5 ($N=10$):
```bash
python scripts/14_run_db5_replication.py
```
*Outputs*: `artifacts/db5/db5_sparse_curve.csv`

### Stage 11: Fixed Population Layout Generalization
Evaluate the frozen consensus 12-channel layout on completely held-out test participants:
```bash
python scripts/audit_fixed_population_layout.py
```
*Outputs*: `results/fixed_layout_experiment.csv`, `results/fixed_layout_summary.json`

### Stage 12: Feature Multicollinearity Sensitivity
Assess robustness when removing collinear IEMG ($512 \cdot \text{MAV}$):
```bash
python scripts/audit_feature_redundancy.py
```
*Outputs*: `results/feature_sensitivity.csv`

---

## 4. Verification and Automated Number Traceability

Run the strict repository publication gate. This validates the entire results graph and generates the canonical LaTeX macros with complete provenance:
```bash
python scripts/16_verify_results.py
```
Expected output:
```
wrote 88 macros to manuscript/generated/results_macros.tex
[PASS] strict result verification and macro provenance completed
```

Every numerical claim in the manuscript is backed by `manuscript/generated/macro_provenance.csv`.

---

## 5. Camera-Ready Figure Generation

Generate all publication vector figures (PDF) and high-resolution raster assets (300 DPI PNG):
```bash
python scripts/generate_camera_ready_figures.py
```
*Generated Figures in `figures_final/` and `manuscript/figures/`*:
- `figure1.pdf` / `.png`: End-to-end SR-CFA methodological workflow
- `figure2.pdf` / `.png`: System architecture and XAI pipeline
- `figure3.pdf` / `.png`: Full-channel baseline distributions and paired differences
- `figure4.pdf` / `.png`: Sparse sensor curves and non-inferiority bootstrap bounds ($k^*=12$)
- `figure5.pdf` / `.png`: Attribution stability distributions across subjects and muscle hubs
- `supplementary_psd.pdf` / `.png`: Power spectral density and filtering verification
- `supplementary_fixed_layout.pdf` / `.png`: Fixed population-level 12-channel generalization
- `supplementary_roar.pdf` / `.png`: RemOve And Retrain (ROAR) deletion curves

---

## 6. Manuscript and Supplementary Material Compilation

Compile the double-column Elsevier manuscript:
```bash
cd manuscript
pdflatex -interaction=nonstopmode main_elsevier.tex
bibtex main_elsevier
pdflatex -interaction=nonstopmode main_elsevier.tex
pdflatex -interaction=nonstopmode main_elsevier.tex
```

Compile the standard preprint manuscript:
```bash
pdflatex -interaction=nonstopmode main.tex
bibtex main
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex
```

Compile the Supplementary Material:
```bash
pdflatex -interaction=nonstopmode supplementary_material.tex
bibtex supplementary_material
pdflatex -interaction=nonstopmode supplementary_material.tex
pdflatex -interaction=nonstopmode supplementary_material.tex
```

Final compiled deliverables are automatically synchronized to:
- `FINAL_DELIVERY/manuscript_elsevier_double_column.pdf`
- `FINAL_DELIVERY/manuscript_preprint.pdf`
- `FINAL_DELIVERY/supplementary_material.pdf`
- `manuscript/revised_manuscript.pdf`

---

## 7. Compute Time and Resource Footprint

| Pipeline Stage | Processing Mode | Hardware Target | Approximate Runtime |
| :--- | :--- | :--- | :--- |
| Feature Extraction (GRABMyo) | 16-core CPU | Multi-threaded | $\sim 25\text{ min}$ |
| Full-Channel XGBoost ($N=43$) | GPU (`hist`) | 1x RTX 4090 | $\sim 12\text{ min}$ |
| Full-Channel SVM ($N=43, 40\text{k}$) | 16-core CPU | Multi-threaded | $\sim 45\text{ min}$ |
| Inner-Fold TreeSHAP ($N=43 \times 5$) | GPU / CPU | CUDA TreeSHAP | $\sim 35\text{ min}$ |
| Sparse Curve Sweeps ($k=1\dots 16$) | GPU (`hist`) | 1x RTX 4090 | $\sim 40\text{ min}$ |
| Non-Inferiority Bootstrap ($B=10{,}000$) | 16-core CPU | Vectorized NumPy | $\sim 2\text{ min}$ |
| Baseline Selectors (500 Random Draws) | GPU (`hist`) | 1x RTX 4090 | $\sim 1.5\text{ hours}$ |
| ROAR Deletion Retraining | GPU (`hist`) | 1x RTX 4090 | $\sim 30\text{ min}$ |
| Complete End-to-End Pipeline | GPU + CPU | Workstation | $\sim 4.5\text{ hours}$ |
