import sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
"""
Script 07: Cross-Fitted SHAP Channel Ranking Generation.
Computes leak-free out-of-fold TreeSHAP attributions per outer LOSO fold.
Generates fold-specific channel rankings Rp for every participant fold and saves to artifacts/rankings/.
"""

import os
import sys
import numpy as np
import pandas as pd
from pathlib import Path

from src.semg_sparse.preprocessing.filters import StandardChannelScaler
from src.semg_sparse.xai.shap_attributions import compute_cross_fitted_shap

def run_xai_channel_ranking():
    print("=" * 70, flush=True)
    print("PHASE 7: CROSS-FITTED SHAP CHANNEL RANKING GENERATION", flush=True)
    print("=" * 70, flush=True)

    feat_path = Path("data/features/grabmyo_features.parquet")
    if not feat_path.exists():
        print("  [ERROR] Feature file missing.", flush=True)
        return

    df = pd.read_parquet(feat_path)
    df_primary = df[df['gesture_id'] <= 16].copy()

    participants = sorted(df_primary['participant_id'].unique())
    meta_cols = ['dataset', 'participant_id', 'session_id', 'gesture_id', 'trial_id', 'window_idx', 'start_sample', 'end_sample']
    feature_cols = [c for c in df_primary.columns if c not in meta_cols]

    X_all = df_primary[feature_cols].values.astype(np.float32)
    y_all = (df_primary['gesture_id'].values - 1).astype(np.int64)
    subs_all = df_primary['participant_id'].values

    out_rank_dir = Path("artifacts/rankings")
    out_rank_dir.mkdir(parents=True, exist_ok=True)

    all_rankings = []
    all_importances = []

    for test_pid in participants:
        train_idx = (subs_all != test_pid)
        X_tr, y_tr = X_all[train_idx], y_all[train_idx]
        subs_tr = subs_all[train_idx]

        scaler = StandardChannelScaler()
        X_tr_scaled = scaler.fit_transform(X_tr)

        channel_imp, ranking = compute_cross_fitted_shap(
            X_train=X_tr_scaled,
            y_train=y_tr,
            subjects_train=subs_tr,
            n_channels=16,
            n_features_per_channel=10,
            n_inner_folds=5
        )

        # Save fold ranking
        df_fold = pd.DataFrame({
            "rank_order": np.arange(1, 17),
            "channel_id": ranking,
            "shap_importance": channel_imp[ranking]
        })
        df_fold.to_csv(out_rank_dir / f"outer_subject_{test_pid:03d}.csv", index=False)

        all_rankings.append(ranking)
        all_importances.append(channel_imp)

        print(f"  [OK] Generated cross-fitted SHAP ranking for Fold {test_pid:02d}. Top 4 channels: {ranking[:4]}", flush=True)

    # Save summary of rankings across all outer folds
    df_rank_summary = pd.DataFrame(all_rankings, columns=[f"rank_{i+1}" for i in range(16)])
    df_rank_summary.insert(0, "test_participant_id", participants)
    df_rank_summary.to_csv(out_rank_dir / "all_outer_fold_rankings.csv", index=False)

    df_imp_summary = pd.DataFrame(all_importances, columns=[f"ch_{i+1}" for i in range(16)])
    df_imp_summary.insert(0, "test_participant_id", participants)
    df_imp_summary.to_csv(out_rank_dir / "all_outer_fold_importances.csv", index=False)

    print(f"\n  [OK] Saved all fold rankings to {out_rank_dir}", flush=True)

if __name__ == "__main__":
    run_xai_channel_ranking()
