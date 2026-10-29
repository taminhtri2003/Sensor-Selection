import sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
"""
Script 12: NinaPro DB5 External Methodological Replication.
Performs strict subject-independent LOSO cross-validation on NinaPro DB5 (10 subjects, 200 Hz).
Computes cross-fitted TreeSHAP channel rankings and tests full-to-sparse performance retention.
Saves replication metrics to artifacts/metrics/db5_replication_metrics.csv.
"""

import os
import sys
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.metrics import f1_score, accuracy_score, balanced_accuracy_score

from src.semg_sparse.preprocessing.filters import StandardChannelScaler
from src.semg_sparse.models.classifiers import build_xgboost_model
from src.semg_sparse.features.handcrafted import get_feature_mapping
from src.semg_sparse.xai.shap_attributions import compute_cross_fitted_shap
from src.semg_sparse.selection.sparse_optimizer import geometry_spread_selection, mutual_information_selection

def run_db5_replication():
    print("=" * 70, flush=True)
    print("PHASE 14: NINAPRO DB5 EXTERNAL METHODOLOGICAL REPLICATION", flush=True)
    print("=" * 70, flush=True)

    feat_path = Path("data/features/db5_features.parquet")
    if not feat_path.exists():
        print("  [ERROR] DB5 feature file missing.", flush=True)
        return

    df_db5 = pd.read_parquet(feat_path)
    subjects = sorted(df_db5['participant_id'].unique())
    print(f"  DB5 Subjects Found: {len(subjects)}", flush=True)

    meta_cols = ['dataset', 'participant_id', 'session_id', 'exercise_id', 'gesture_id', 'repetition_id', 'window_idx', 'start_sample', 'end_sample']
    feature_cols = [c for c in df_db5.columns if c not in meta_cols]

    _, channel_indices, _ = get_feature_mapping(16)
    channel_indices = np.array(channel_indices)

    X_all = df_db5[feature_cols].values.astype(np.float32)
    y_all = (df_db5['gesture_id'].values - 1).astype(np.int64) # 0-indexed
    subs_all = df_db5['participant_id'].values

    results = []

    for test_sub in subjects:
        train_idx = (subs_all != test_sub)
        test_idx = (subs_all == test_sub)

        X_tr, y_tr = X_all[train_idx], y_all[train_idx]
        subs_tr = subs_all[train_idx]
        X_te, y_te = X_all[test_idx], y_all[test_idx]

        scaler = StandardChannelScaler()
        X_tr_scaled = scaler.fit_transform(X_tr)
        X_te_scaled = scaler.transform(X_te)

        # Cross-fitted SHAP ranking on DB5 training subjects
        channel_imp, shap_ranking = compute_cross_fitted_shap(
            X_train=X_tr_scaled,
            y_train=y_tr,
            subjects_train=subs_tr,
            n_channels=16,
            n_features_per_channel=10,
            n_inner_folds=4
        )

        # Full channel evaluation (k=16)
        m_full = build_xgboost_model()
        m_full.fit(X_tr_scaled, y_tr)
        p_full = m_full.predict(X_te_scaled)

        results.append({
            "participant_id": test_sub,
            "dataset": "NinaPro_DB5",
            "selection_method": "Full_Array",
            "k": 16,
            "channel_fraction": 1.0,
            "macro_f1": f1_score(y_te, p_full, average='macro'),
            "accuracy": accuracy_score(y_te, p_full)
        })

        # Sparse channel evaluations k in {1, 2, 4, 6, 8, 10, 12, 14}
        for k in [1, 2, 4, 6, 8, 10, 12, 14]:
            top_k_ch = shap_ranking[:k]
            mask_k = np.isin(channel_indices, top_k_ch)

            scaler_k = StandardChannelScaler()
            X_tr_k = scaler_k.fit_transform(X_tr[:, mask_k])
            X_te_k = scaler_k.transform(X_te[:, mask_k])

            m_k = build_xgboost_model()
            m_k.fit(X_tr_k, y_tr)
            p_k = m_k.predict(X_te_k)

            results.append({
                "participant_id": test_sub,
                "dataset": "NinaPro_DB5",
                "selection_method": "CrossFitted_SHAP",
                "k": k,
                "channel_fraction": k / 16.0,
                "macro_f1": f1_score(y_te, p_k, average='macro'),
                "accuracy": accuracy_score(y_te, p_k)
            })

            # Geometry spread comparison
            geom_ch = geometry_spread_selection(16, k)
            mask_geom = np.isin(channel_indices, geom_ch)
            scaler_g = StandardChannelScaler()
            X_tr_g = scaler_g.fit_transform(X_tr[:, mask_geom])
            X_te_g = scaler_g.transform(X_te[:, mask_geom])
            m_g = build_xgboost_model()
            m_g.fit(X_tr_g, y_tr)
            p_g = m_g.predict(X_te_g)

            results.append({
                "participant_id": test_sub,
                "dataset": "NinaPro_DB5",
                "selection_method": "Geometry_Spread",
                "k": k,
                "channel_fraction": k / 16.0,
                "macro_f1": f1_score(y_te, p_g, average='macro'),
                "accuracy": accuracy_score(y_te, p_g)
            })

        print(f"  [OK] Completed DB5 External Replication for Subject {test_sub:02d}", flush=True)

    out_dir = Path("artifacts/metrics")
    out_dir.mkdir(parents=True, exist_ok=True)
    df_res = pd.DataFrame(results)
    df_res.to_csv(out_dir / "db5_replication_metrics.csv", index=False)

    summary = df_res.groupby(['selection_method', 'k']).agg(
        mean_macro_f1=('macro_f1', 'mean'),
        std_macro_f1=('macro_f1', 'std')
    ).reset_index()
    summary.to_csv(out_dir / "db5_summary.csv", index=False)

    print("\nNinaPro DB5 External Replication Summary:")
    print(summary.to_string(index=False), flush=True)

if __name__ == "__main__":
    run_db5_replication()
