"""Fixed population layout experiment:
Derives ONE consensus 12-channel layout on a development cohort (e.g. 21 participants),
freezes this physical layout, and evaluates on 22 completely unseen held-out participants.
Tests whether ONE physically fixed sparse hardware montage works on unseen users without per-fold channel customization.
"""

import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import f1_score
import xgboost as xgb

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.semg_sparse.xai.cross_fitted import compute_cross_fitted_attribution

SEED = 20260728
N_CHANNELS = 16
N_FPC = 10

def channel_columns(channels_1based):
    cols = []
    for c in channels_1based:
        start = (c - 1) * N_FPC
        cols.extend(range(start, start + N_FPC))
    return np.array(sorted(cols), dtype=np.int64)

def run_fixed_layout_experiment():
    print("Loading data...")
    X = np.load(ROOT / "data" / "cache" / "loso_X.npy", mmap_mode="r")
    y = np.load(ROOT / "data" / "cache" / "loso_y.npy", mmap_mode="r")
    subj = np.load(ROOT / "data" / "cache" / "loso_subj.npy", mmap_mode="r")
    with open(ROOT / "data" / "cache" / "loso_features.json") as f:
        fcols = json.load(f)

    # Split 43 participants: Dev (odd pids: 1, 3, 5... 22 subjects), Test (even pids: 2, 4, 6... 21 subjects)
    dev_pids = np.array([p for p in range(1, 44) if p % 2 != 0])
    test_pids = np.array([p for p in range(1, 44) if p % 2 == 0])
    print(f"Dev participants ({len(dev_pids)}): {dev_pids}")
    print(f"Test participants ({len(test_pids)}): {test_pids}")

    dev_mask = np.isin(subj, dev_pids)
    test_mask = np.isin(subj, test_pids)

    X_dev, y_dev, subj_dev = np.asarray(X[dev_mask], dtype=np.float32), np.asarray(y[dev_mask]), np.asarray(subj[dev_mask])
    
    # 1. Derive consensus ranking on Dev cohort ONLY using inner cross-fitting
    print("Computing consensus SR-CFA ranking on development cohort...")
    res = compute_cross_fitted_attribution(
        X_dev, y_dev, subj_dev, fcols,
        n_channels=N_CHANNELS, n_features_per_channel=N_FPC,
        n_inner_folds=5, device="cuda", max_attrib_samples=20000,
        max_train_samples=None, seed=SEED
    )
    
    # Consensus ranking with lambda = 0.50
    consensus_rank_0indexed = res.ranking(lam=0.50)
    consensus_channels_1based = [c + 1 for c in consensus_rank_0indexed]
    fixed_k12_channels = consensus_channels_1based[:12]
    print(f"\nFrozen Consensus 12-Channel Hardware Layout: {fixed_k12_channels}")
    print(f"Dropped Channels: {consensus_channels_1based[12:]}")

    # 2. Evaluate the fixed layout on the held-out TEST participants (Leave-One-Subject-Out among test subjects or trained on Dev)
    # Under the true clinical scenario: train on Dev, evaluate on each held-out Test subject
    cols_12 = channel_columns(fixed_k12_channels)
    
    # Standardize Dev
    mu_16 = X_dev.mean(axis=0)
    sd_16 = X_dev.std(axis=0) + 1e-8
    
    X_dev_16_scaled = (X_dev - mu_16) / sd_16
    X_dev_12_scaled = (X_dev[:, cols_12] - mu_16[cols_12]) / sd_16[cols_12]

    XGB_PARAMS = dict(n_estimators=300, max_depth=6, learning_rate=0.1, subsample=0.8,
                      colsample_bytree=0.8, tree_method="hist", device="cuda", random_state=SEED, verbosity=0)

    print("\nTraining models on development cohort...")
    # Train full 16 model
    m16 = xgb.XGBClassifier(**XGB_PARAMS)
    m16.fit(X_dev_16_scaled, y_dev)

    # Train fixed 12 model
    m12 = xgb.XGBClassifier(**XGB_PARAMS)
    m12.fit(X_dev_12_scaled, y_dev)

    print("Evaluating on held-out test participants...")
    per_subject_results = []
    for pid in test_pids:
        p_mask = (subj == pid)
        X_p = np.asarray(X[p_mask], dtype=np.float32)
        y_p = np.asarray(y[p_mask])

        X_p_16 = (X_p - mu_16) / sd_16
        X_p_12 = (X_p[:, cols_12] - mu_16[cols_12]) / sd_16[cols_12]

        pred16 = m16.predict(X_p_16)
        pred12 = m12.predict(X_p_12)

        f1_16 = f1_score(y_p, pred16, average="macro")
        f1_12 = f1_score(y_p, pred12, average="macro")
        diff = f1_12 - f1_16

        per_subject_results.append({
            "test_participant": pid,
            "macro_f1_full16": f1_16,
            "macro_f1_fixed12": f1_12,
            "diff_12_minus_16": diff
        })

    df_test = pd.DataFrame(per_subject_results)
    
    mean_16 = df_test["macro_f1_full16"].mean()
    sd_16_val = df_test["macro_f1_full16"].std(ddof=1)
    mean_12 = df_test["macro_f1_fixed12"].mean()
    sd_12_val = df_test["macro_f1_fixed12"].std(ddof=1)
    mean_diff = df_test["diff_12_minus_16"].mean()

    # Bootstrap CI
    rng = np.random.default_rng(SEED)
    diffs = df_test["diff_12_minus_16"].values
    b_diffs = np.array([np.mean(rng.choice(diffs, size=len(diffs), replace=True)) for _ in range(10000)])
    lcb = np.percentile(b_diffs, 2.5)
    ucb = np.percentile(b_diffs, 97.5)

    print(f"\n--- FIXED POPULATION HARDWARE LAYOUT RESULTS (N={len(test_pids)} Unseen Test Subjects) ---")
    print(f"Full 16-channel: Macro-F1 = {mean_16:.4f} +/- {sd_16_val:.4f}")
    print(f"Fixed 12-channel: Macro-F1 = {mean_12:.4f} +/- {sd_12_val:.4f}")
    print(f"Paired Difference (12 - 16): {mean_diff:+.4f} (95% CI [{lcb:+.4f}, {ucb:+.4f}])")
    print(f"Non-Inferiority Criterion (LCB > -0.020): {lcb > -0.020} (LCB = {lcb:+.4f})")

    out_csv = ROOT / "artifacts" / "fixed_layout" / "fixed_layout_experiment.csv"
    df_test.to_csv(out_csv, index=False)
    print(f"Saved results to {out_csv}")

    summary = {
        "dev_subjects_count": int(len(dev_pids)),
        "test_subjects_count": int(len(test_pids)),
        "frozen_consensus_channels": [int(x) for x in fixed_k12_channels],
        "dropped_channels": [int(x) for x in consensus_channels_1based[12:]],
        "mean_macro_f1_full16": float(mean_16),
        "sd_macro_f1_full16": float(sd_16_val),
        "mean_macro_f1_fixed12": float(mean_12),
        "sd_macro_f1_fixed12": float(sd_12_val),
        "paired_difference_mean": float(mean_diff),
        "bootstrap_95_lcb": float(lcb),
        "bootstrap_95_ucb": float(ucb),
        "non_inferior_at_delta_02": bool(lcb > -0.020)
    }
    with open(ROOT / "artifacts" / "fixed_layout" / "fixed_layout_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    print("Successfully saved artifacts/fixed_layout/fixed_layout_summary.json")

if __name__ == "__main__":
    run_fixed_layout_experiment()
