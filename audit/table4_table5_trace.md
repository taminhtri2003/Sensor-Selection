# Audit & Trace: Table 4 vs Table 5 Numerical Divergence

**Audit Date:** 2026-09-14  
**Investigated Discrepancy:**
The manuscript previously reported two different sets of performance numbers for SR-CFA ($\lambda=0.50$):

| Channel Count ($k$) | Table 4 (Primary Sparse Curve) | Table 5 (Baseline Comparisons) | Absolute Difference ($\Delta$) |
| :---: | :---: | :---: | :---: |
| $k = 4$ | $0.397 \pm 0.071$ | $0.378 \pm 0.073$ | $+0.019$ |
| $k = 6$ | $0.480 \pm 0.084$ | $0.448 \pm 0.080$ | $+0.032$ |
| $k = 8$ | $0.505 \pm 0.085$ | $0.466 \pm 0.082$ | $+0.039$ |
| $k = 12$ | $0.528 \pm 0.084$ | $0.481 \pm 0.081$ | $+0.047$ |

---

## 1. Trace of Code Paths & Result Artifacts

### Origin of Table 4 Numbers:
- **Script:** `scripts/26_sparse_sensor_curve.py`
- **Output Artifacts:** `artifacts/metrics/sparse_curve_subject_metrics.csv`, `artifacts/tables/table3_sparse_performance.csv`
- **Model Architecture:** XGBoost (`XGBClassifier`)
- **Hyperparameters:** `n_estimators = 300`, `max_depth = 6`, `learning_rate = 0.1`, `subsample = 0.8`, `colsample_bytree = 0.8`, `tree_method = "hist"`, `seed = 20260728`
- **Training Budget:** Full fold training set ($\sim 550{,}368$ active windows across 42 participants, 0 subsampling).
- **Selection Source:** Top-$k$ channels from outer-fold specific ranking $R_{-p}$ derived via inner cross-fitted TreeSHAP.
- **Evaluation:** Retrained from scratch on the selected $k$ channels per outer fold, tested on held-out participant $p$ (all 3 sessions, $13{,}104$ windows).

### Origin of Table 5 Numbers:
- **Script:** `scripts/27_selection_baselines.py`
- **Output Artifacts:** `artifacts/selection_baselines/selection_baseline_metrics.csv`, `artifacts/selection_baselines/selection_baseline_summary.csv`
- **Metadata Document:** `artifacts/selection_baselines/compute_budget.json`
- **Model Architecture:** XGBoost (`XGBClassifier`)
- **Hyperparameters:** `n_estimators = 50` (Deliberately reduced from 300), `max_depth = 6`, `learning_rate = 0.1`, `subsample = 0.8`, `colsample_bytree = 0.8`, `tree_method = "hist"`, `seed = 20260728`
- **Training Budget:** Subsampled to $150{,}000$ windows per outer fold (`CMP_TRAIN_SUBSAMPLE = 150000`).
- **Rationale from Codebase:** Line 51--58 of `scripts/27_selection_baselines.py`:
  > *"Shared comparison configuration. Deliberately lighter than the headline model: the question here is the relative merit of channel subsets, and a lighter model lets the random baseline be sampled densely enough to characterise its distribution (100 draws for k=4,6,8; 500 draws for k=12). Applied identically to every method, so no method is advantaged. The absolute numbers are therefore not comparable to the P1/P3 headline figures and must never be quoted as such."*

---

## 2. Scientific Diagnosis & Reconciliation

1. **Are they different experiments?**  
   **YES.** They represent two methodologically distinct experimental questions:
   - **Primary Sparse Evaluation (Table 4):** Evaluates the full capacity of a deployable XGBoost classifier (300 trees, full $\sim 550\text{k}$ training data) under the proposed SR-CFA ranking.
   - **Relative Selector Benchmark (Table 5):** Evaluates whether SR-CFA outperforms competing selectors (SHAP $\lambda=0$, Permutation, Mutual Information, Geometric, and Random distributions) under a controlled, matched computational budget (50 trees, 150k samples).

2. **Why the Contradiction Occurred in the Manuscript:**  
   The previous manuscript text failed to explicitly state that Table 5 used a matched-budget exploratory comparison protocol (50 trees, 150k samples). As a result, a reader comparing Table 4 and Table 5 saw two conflicting Macro-F1 values for "SR-CFA $\lambda=0.50$" at the same $k$ without explanation.

3. **Required Manuscript & Canonical Resolution:**
   - **Table 4** remains the **Primary Sparse Curve** ($300$ trees, full training budget, $k^*=12 \to 0.528$).
   - **Table 5** must be titled and described explicitly as:  
     *"Comparative channel selection benchmark under matched training budget (50 trees, 150,000 samples per fold, $N=43$)."*
   - In Table 5, explicitly label the SR-CFA column as:  
     `SR-CFA (Matched Budget, 50 trees)`  
     and add an explanatory footnote/caption:  
     *"Note: All methods in this benchmark were evaluated using an identical 50-tree model with 150,000 training samples per fold to make 500 random draws per fold computationally tractable. Absolute scores are lower than the 300-tree primary headline curve in Table 4, but relative rankings among selectors are directly comparable."*
   - Furthermore, we can evaluate whether the full-budget model at $k=12$ can be run for the primary baselines or clearly document the budget difference.
