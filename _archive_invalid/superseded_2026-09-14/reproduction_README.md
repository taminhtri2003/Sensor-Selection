# Reproducibility Guide

This repository contains the complete, reproducible codebase for the study:
> **Explainability-Guided Sparse sEMG Sensor Selection for Subject-Independent Hand-Gesture Recognition**

---

## 1. Prerequisites
- **Python**: 3.10+
- **GPU**: Recommended (CUDA PyTorch)
- **Dependencies**: `pip install -r requirements.txt` or `conda env create -f environment.yml`

Core Python libraries required:
- `numpy`, `scipy`, `pandas`, `scikit-learn`, `xgboost`, `torch`, `shap`, `wfdb`, `matplotlib`, `seaborn`, `statsmodels`, `boto3`, `awscli`.

---

## 2. Quick Start - One Command Reproducibility

### Windows (PowerShell / Command Prompt)
```cmd
reproduce.bat
```

### Linux / macOS
```bash
make reproduce
```

---

## 3. Step-by-Step Pipeline Execution

```bash
# Phase 0: Environment Audit
python scripts/00_audit_environment.py

# Phase 1: Download Datasets (GRABMyo & NinaPro DB5) & Manifests
python scripts/01_download_data.py

# Phase 2: Quality & Integrity Audit
python scripts/02_audit_datasets.py

# Phase 3: Metadata Catalog Building
python scripts/03_build_metadata.py

# Phase 4: Signal Preprocessing & Windowing
python scripts/04_preprocess.py

# Phase 4: Feature Extraction & Parquet Caching
python scripts/05_extract_features.py

# Phase 6: Full-Channel Baselines (LOSO)
python scripts/06_run_full_channel_baselines.py

# Phase 7: Cross-Fitted SHAP Channel Ranking
python scripts/07_run_xai_selection.py

# Phase 8: Sparse Model Optimization (k = 1..16)
python scripts/08_run_sparse_models.py

# Phase 9: Selection Baselines Comparison
python scripts/09_run_selection_baselines.py

# Phase 12: Cross-Session Robustness Experiments
python scripts/10_run_cross_session.py

# Phase 11: XAI Faithfulness Deletion Experiments
python scripts/11_run_xai_faithfulness.py

# Phase 14: NinaPro DB5 External Replication
python scripts/12_run_db5_replication.py

# Phase 16: Master Statistical Analysis & Non-Inferiority
python scripts/13_run_statistics.py

# Phase 18: Figure & Table Generation
python scripts/14_generate_figures.py
python scripts/15_generate_tables.py

# Phase 21: Result Verification Gate
python scripts/16_verify_results.py

# Phase 22: Manuscript & Supplement LaTeX PDF Compilation
python scripts/17_build_manuscript.py
```

---

## 4. Output Deliverables
Upon completion, compiled deliverables are populated in `FINAL_DELIVERY/`:
- `manuscript_two_column.pdf`: Two-column review manuscript
- `manuscript_two_column.tex`: Manuscript LaTeX source
- `supplementary_material.pdf`: Supplementary Information
- `FINAL_RESEARCH_REPORT.md`: Comprehensive study summary report
