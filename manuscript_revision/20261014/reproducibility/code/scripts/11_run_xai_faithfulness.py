import sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
"""
Script 11: XAI Faithfulness Deletion Experiments.
Compares deletion curves when removing:
1. Top-important channels first
2. Random matched channels
3. Bottom-important channels first
Validates whether explainability attributions are faithful (Performance_top < Performance_rand < Performance_bottom).
Saves results to artifacts/metrics/faithfulness_deletion_metrics.csv.
"""

import os
import sys
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.metrics import f1_score, accuracy_score

from src.semg_sparse.preprocessing.filters import StandardChannelScaler
from src.semg_sparse.models.classifiers import build_xgboost_model
from src.semg_sparse.features.handcrafted import get_feature_mapping

def run_faithfulness_experiments():
    print("=" * 70, flush=True)
    print("PHASE 11: XAI FAITHFULNESS DELETION EXPERIMENTS", flush=True)
    print("=" * 70, flush=True)

    feat_path = Path("data/features/grabmyo_features.parquet")
    rank_dir = Path("artifacts/rankings")

    if not feat_path.exists():
        print("  [ERROR] Feature file missing.", flush=True)
        return

    df = pd.read_parquet(feat_path)
    df_primary = df[df['gesture_id'] <= 16].copy()

    participants = sorted(df_primary['participant_id'].unique())
    meta_cols = ['dataset', 'participant_id', 'session_id', 'gesture_id', 'trial_id', 'window_idx', 'start_sample', 'end_sample']
    feature_cols = [c for c in df_primary.columns if c not in meta_cols]

    _, channel_indices, _ = get_feature_mapping(16)
    channel_indices = np.array(channel_indices)

    X_all = df_primary[feature_cols].values.astype(np.float32)
    y_all = (df_primary['gesture_id'].values - 1).astype(np.int64)
    subs_all = df_primary['participant_id'].values

    # Number of channels to remove m = 1..15
    eval_m = [1, 2, 4, 6, 8, 10, 12, 14]
    results = []

    for test_pid in participants:
        rank_p = rank_dir / f"outer_subject_{test_pid:03d}.csv"
        shap_ranking = list(pd.read_csv(rank_p)['channel_id'].values) if rank_p.exists() else list(range(16))

        train_idx = (subs_all != test_pid)
        test_idx = (subs_all == test_pid)

        X_tr_full, y_tr = X_all[train_idx], y_all[train_idx]
        X_te_full, y_te = X_all[test_idx], y_all[test_idx]

        for m_rem in eval_m:
            # 1. Top Removal: Remove top m_rem channels
            ch_remove_top = shap_ranking[:m_rem]
            ch_keep_top = [c for c in range(16) if c not in ch_remove_top]
            mask_top = np.isin(channel_indices, ch_keep_top)

            scaler = StandardChannelScaler()
            X_tr_top = scaler.fit_transform(X_tr_full[:, mask_top])
            X_te_top = scaler.transform(X_te_full[:, mask_top])
            m = build_xgboost_model()
            m.fit(X_tr_top, y_tr)
            p_top = m.predict(X_te_top)
            results.append({
                "participant_id": test_pid,
                "removal_strategy": "Top_Removal",
                "m_removed": m_rem,
                "channels_remaining": len(ch_keep_top),
                "macro_f1": f1_score(y_te, p_top, average='macro'),
                "accuracy": accuracy_score(y_te, p_top)
            })

            # 2. Bottom Removal: Remove bottom m_rem channels (keep top 16 - m_rem)
            ch_keep_bottom = shap_ranking[:16 - m_rem]
            mask_bot = np.isin(channel_indices, ch_keep_bottom)

            scaler = StandardChannelScaler()
            X_tr_bot = scaler.fit_transform(X_tr_full[:, mask_bot])
            X_te_bot = scaler.transform(X_te_full[:, mask_bot])
            m = build_xgboost_model()
            m.fit(X_tr_bot, y_tr)
            p_bot = m.predict(X_te_bot)
            results.append({
                "participant_id": test_pid,
                "removal_strategy": "Bottom_Removal",
                "m_removed": m_rem,
                "channels_remaining": len(ch_keep_bottom),
                "macro_f1": f1_score(y_te, p_bot, average='macro'),
                "accuracy": accuracy_score(y_te, p_bot)
            })

            # 3. Random Removal: Remove random m_rem channels (averaged over 10 random draws)
            rng = np.random.default_rng(20260728 + test_pid * 100 + m_rem)
            rand_f1s = []
            for _ in range(10):
                ch_rem_rand = rng.choice(16, size=m_rem, replace=False)
                ch_keep_rand = [c for c in range(16) if c not in ch_rem_rand]
                mask_rand = np.isin(channel_indices, ch_keep_rand)

                scaler = StandardChannelScaler()
                X_tr_r = scaler.fit_transform(X_tr_full[:, mask_rand])
                X_te_r = scaler.transform(X_te_full[:, mask_rand])
                m = build_xgboost_model()
                m.fit(X_tr_r, y_tr)
                p_rand = m.predict(X_te_r)
                rand_f1s.append(f1_score(y_te, p_rand, average='macro'))

            results.append({
                "participant_id": test_pid,
                "removal_strategy": "Random_Removal",
                "m_removed": m_rem,
                "channels_remaining": 16 - m_rem,
                "macro_f1": float(np.mean(rand_f1s)),
                "accuracy": 0.0
            })

        print(f"  [OK] Completed Faithfulness Deletion for Participant {test_pid:02d}", flush=True)

    out_dir = Path("artifacts/metrics")
    out_dir.mkdir(parents=True, exist_ok=True)
    df_res = pd.DataFrame(results)
    df_res.to_csv(out_dir / "faithfulness_deletion_metrics.csv", index=False)

    summary = df_res.groupby(['removal_strategy', 'm_removed']).agg(
        mean_macro_f1=('macro_f1', 'mean'),
        std_macro_f1=('macro_f1', 'std')
    ).reset_index()
    summary.to_csv(out_dir / "faithfulness_summary.csv", index=False)

    print("\nFaithfulness Deletion Summary:")
    print(summary.to_string(index=False), flush=True)

if __name__ == "__main__":
    run_faithfulness_experiments()
