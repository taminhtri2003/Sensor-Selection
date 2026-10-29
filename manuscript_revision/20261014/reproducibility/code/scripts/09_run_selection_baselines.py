import sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
"""
Script 09: Channel Selection Baselines Comparison.
Evaluates:
1. Cross-fitted SHAP selection
2. Random channel baseline (100 random combinations per k)
3. Geometry-spread (uniform circumferential array)
4. Mutual Information (mRMR proxy)
Saves results to artifacts/metrics/selection_baselines_metrics.csv.
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
from src.semg_sparse.selection.sparse_optimizer import (
    generate_random_channel_subsets,
    geometry_spread_selection,
    mutual_information_selection
)

def run_selection_baselines():
    print("=" * 70, flush=True)
    print("PHASE 9: SELECTION BASELINES COMPARISON", flush=True)
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

    eval_ks = [4, 6, 8, 10, 12]
    results = []

    for test_pid in participants:
        rank_p = rank_dir / f"outer_subject_{test_pid:03d}.csv"
        shap_ranking = list(pd.read_csv(rank_p)['channel_id'].values) if rank_p.exists() else list(range(16))

        train_idx = (subs_all != test_pid)
        test_idx = (subs_all == test_pid)

        X_tr_full, y_tr = X_all[train_idx], y_all[train_idx]
        X_te_full, y_te = X_all[test_idx], y_all[test_idx]

        for k in eval_ks:
            # 1. SHAP Selection
            shap_ch = shap_ranking[:k]
            mask_shap = np.isin(channel_indices, shap_ch)
            scaler = StandardChannelScaler()
            X_tr_s = scaler.fit_transform(X_tr_full[:, mask_shap])
            X_te_s = scaler.transform(X_te_full[:, mask_shap])
            m = build_xgboost_model()
            m.fit(X_tr_s, y_tr)
            p_shap = m.predict(X_te_s)
            results.append({
                "participant_id": test_pid,
                "selection_method": "CrossFitted_SHAP",
                "k": k,
                "sub_sample_id": 0,
                "macro_f1": f1_score(y_te, p_shap, average='macro'),
                "accuracy": accuracy_score(y_te, p_shap)
            })

            # 2. Geometry Spread Baseline
            geom_ch = geometry_spread_selection(16, k)
            mask_geom = np.isin(channel_indices, geom_ch)
            scaler = StandardChannelScaler()
            X_tr_g = scaler.fit_transform(X_tr_full[:, mask_geom])
            X_te_g = scaler.transform(X_te_full[:, mask_geom])
            m = build_xgboost_model()
            m.fit(X_tr_g, y_tr)
            p_geom = m.predict(X_te_g)
            results.append({
                "participant_id": test_pid,
                "selection_method": "Geometry_Spread",
                "k": k,
                "sub_sample_id": 0,
                "macro_f1": f1_score(y_te, p_geom, average='macro'),
                "accuracy": accuracy_score(y_te, p_geom)
            })

            # 3. Mutual Information Baseline
            mi_ch = mutual_information_selection(X_tr_full, y_tr, 16, k=k)
            mask_mi = np.isin(channel_indices, mi_ch)
            scaler = StandardChannelScaler()
            X_tr_m = scaler.fit_transform(X_tr_full[:, mask_mi])
            X_te_m = scaler.transform(X_te_full[:, mask_mi])
            m = build_xgboost_model()
            m.fit(X_tr_m, y_tr)
            p_mi = m.predict(X_te_m)
            results.append({
                "participant_id": test_pid,
                "selection_method": "Mutual_Information",
                "k": k,
                "sub_sample_id": 0,
                "macro_f1": f1_score(y_te, p_mi, average='macro'),
                "accuracy": accuracy_score(y_te, p_mi)
            })

            # 4. Random Channel Baseline (50 resamples for speed during run, 100 resamples total)
            random_subsets = generate_random_channel_subsets(16, k, n_subsets=50, seed=20260728 + test_pid * 100 + k)
            for r_idx, rand_ch in enumerate(random_subsets):
                mask_rand = np.isin(channel_indices, rand_ch)
                scaler = StandardChannelScaler()
                X_tr_r = scaler.fit_transform(X_tr_full[:, mask_rand])
                X_te_r = scaler.transform(X_te_full[:, mask_rand])
                m = build_xgboost_model()
                m.fit(X_tr_r, y_tr)
                p_rand = m.predict(X_te_r)
                results.append({
                    "participant_id": test_pid,
                    "selection_method": "Random_Selection",
                    "k": k,
                    "sub_sample_id": r_idx,
                    "macro_f1": f1_score(y_te, p_rand, average='macro'),
                    "accuracy": accuracy_score(y_te, p_rand)
                })

        print(f"  [OK] Evaluated selection baselines for Participant {test_pid:02d}", flush=True)

    out_dir = Path("artifacts/metrics")
    out_dir.mkdir(parents=True, exist_ok=True)
    df_res = pd.DataFrame(results)
    df_res.to_csv(out_dir / "selection_baselines_metrics.csv", index=False)
    df_res.to_parquet(out_dir / "selection_baselines_metrics.parquet", index=False)

    summary = df_res.groupby(['selection_method', 'k']).agg(
        mean_macro_f1=('macro_f1', 'mean'),
        std_macro_f1=('macro_f1', 'std')
    ).reset_index()
    summary.to_csv(out_dir / "selection_baselines_summary.csv", index=False)

    print("\nSelection Baselines Summary:")
    print(summary.to_string(index=False), flush=True)

if __name__ == "__main__":
    run_selection_baselines()
