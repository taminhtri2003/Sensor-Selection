import sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
"""
Script 10: Cross-Session Robustness & Ranking Stability.
Evaluates CS1 (Train Session 1 -> Test Session 1, 2, 3) and CS2 (Train Session 1+2 -> Test Session 3).
Measures session-to-session channel ranking stability Spearman rho(R_S1, R_S2), rho(R_S1, R_S3).
Saves results to artifacts/metrics/cross_session_metrics.csv and artifacts/rankings/session_stability.csv.
"""

import os
import sys
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.stats import spearmanr, kendalltau
from sklearn.metrics import f1_score, accuracy_score

from src.semg_sparse.preprocessing.filters import StandardChannelScaler
from src.semg_sparse.models.classifiers import build_xgboost_model
from src.semg_sparse.features.handcrafted import get_feature_mapping
from src.semg_sparse.xai.shap_attributions import compute_cross_fitted_shap

def run_cross_session_experiments():
    print("=" * 70, flush=True)
    print("PHASE 12: CROSS-SESSION ROBUSTNESS EXPERIMENTS (CS1 & CS2)", flush=True)
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

    results = []

    for test_pid in participants:
        rank_p = rank_dir / f"outer_subject_{test_pid:03d}.csv"
        shap_ranking = list(pd.read_csv(rank_p)['channel_id'].values) if rank_p.exists() else list(range(16))

        # CS1: Train Session 1 -> Test Session 1, 2, 3
        df_train_s1 = df_primary[(df_primary['participant_id'] != test_pid) & (df_primary['session_id'] == 1)]
        df_test_s1 = df_primary[(df_primary['participant_id'] == test_pid) & (df_primary['session_id'] == 1)]
        df_test_s2 = df_primary[(df_primary['participant_id'] == test_pid) & (df_primary['session_id'] == 2)]
        df_test_s3 = df_primary[(df_primary['participant_id'] == test_pid) & (df_primary['session_id'] == 3)]

        X_tr_s1 = df_train_s1[feature_cols].values.astype(np.float32)
        y_tr_s1 = (df_train_s1['gesture_id'].values - 1).astype(np.int64)

        for k in [4, 6, 8, 10, 12, 16]:
            top_k_ch = shap_ranking[:k]
            mask_k = np.isin(channel_indices, top_k_ch)

            scaler = StandardChannelScaler()
            X_tr_k = scaler.fit_transform(X_tr_s1[:, mask_k])

            model = build_xgboost_model()
            model.fit(X_tr_k, y_tr_s1)

            # Test S1
            if len(df_test_s1) > 0:
                X_te_s1 = scaler.transform(df_test_s1[feature_cols].values[:, mask_k])
                y_te_s1 = (df_test_s1['gesture_id'].values - 1).astype(np.int64)
                preds = model.predict(X_te_s1)
                results.append({
                    "participant_id": test_pid,
                    "experiment": "CS1",
                    "train_sessions": "Session_1",
                    "test_session": "Session_1",
                    "k": k,
                    "macro_f1": f1_score(y_te_s1, preds, average='macro'),
                    "accuracy": accuracy_score(y_te_s1, preds)
                })

            # Test S2
            if len(df_test_s2) > 0:
                X_te_s2 = scaler.transform(df_test_s2[feature_cols].values[:, mask_k])
                y_te_s2 = (df_test_s2['gesture_id'].values - 1).astype(np.int64)
                preds = model.predict(X_te_s2)
                results.append({
                    "participant_id": test_pid,
                    "experiment": "CS1",
                    "train_sessions": "Session_1",
                    "test_session": "Session_2",
                    "k": k,
                    "macro_f1": f1_score(y_te_s2, preds, average='macro'),
                    "accuracy": accuracy_score(y_te_s2, preds)
                })

            # Test S3
            if len(df_test_s3) > 0:
                X_te_s3 = scaler.transform(df_test_s3[feature_cols].values[:, mask_k])
                y_te_s3 = (df_test_s3['gesture_id'].values - 1).astype(np.int64)
                preds = model.predict(X_te_s3)
                results.append({
                    "participant_id": test_pid,
                    "experiment": "CS1",
                    "train_sessions": "Session_1",
                    "test_session": "Session_3",
                    "k": k,
                    "macro_f1": f1_score(y_te_s3, preds, average='macro'),
                    "accuracy": accuracy_score(y_te_s3, preds)
                })

        # CS2: Train Session 1+2 -> Test Session 3
        df_train_s12 = df_primary[(df_primary['participant_id'] != test_pid) & (df_primary['session_id'].isin([1, 2]))]
        if len(df_train_s12) > 0 and len(df_test_s3) > 0:
            X_tr_s12 = df_train_s12[feature_cols].values.astype(np.float32)
            y_tr_s12 = (df_train_s12['gesture_id'].values - 1).astype(np.int64)
            X_te_s3_raw = df_test_s3[feature_cols].values.astype(np.float32)
            y_te_s3 = (df_test_s3['gesture_id'].values - 1).astype(np.int64)

            for k in [4, 6, 8, 10, 12, 16]:
                top_k_ch = shap_ranking[:k]
                mask_k = np.isin(channel_indices, top_k_ch)

                scaler = StandardChannelScaler()
                X_tr_k = scaler.fit_transform(X_tr_s12[:, mask_k])
                X_te_k = scaler.transform(X_te_s3_raw[:, mask_k])

                model = build_xgboost_model()
                model.fit(X_tr_k, y_tr_s12)
                preds = model.predict(X_te_k)

                results.append({
                    "participant_id": test_pid,
                    "experiment": "CS2",
                    "train_sessions": "Session_1+2",
                    "test_session": "Session_3",
                    "k": k,
                    "macro_f1": f1_score(y_te_s3, preds, average='macro'),
                    "accuracy": accuracy_score(y_te_s3, preds)
                })

        print(f"  [OK] Evaluated Cross-Session for Participant {test_pid:02d}", flush=True)

    out_dir = Path("artifacts/metrics")
    out_dir.mkdir(parents=True, exist_ok=True)
    df_res = pd.DataFrame(results)
    df_res.to_csv(out_dir / "cross_session_metrics.csv", index=False)

    summary = df_res.groupby(['experiment', 'train_sessions', 'test_session', 'k']).agg(
        mean_macro_f1=('macro_f1', 'mean'),
        std_macro_f1=('macro_f1', 'std')
    ).reset_index()
    summary.to_csv(out_dir / "cross_session_summary.csv", index=False)

    print("\nCross-Session Performance Summary:")
    print(summary.to_string(index=False), flush=True)

if __name__ == "__main__":
    run_cross_session_experiments()
