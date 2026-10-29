import sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
"""
Script 08: Sparse-Channel Model Optimization & Evaluation.
Evaluates XGBoost across k = 1..16 channels selected by cross-fitted SHAP ranking Rp.
Evaluates confirmatory models (SVM, RF) at k in {4, 6, 8, 10, 12, 16}.
Saves participant-level sparse performance metrics to artifacts/metrics/sparse_models_subject_metrics.csv.
"""

import os
import sys
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.metrics import f1_score, accuracy_score, balanced_accuracy_score

from src.semg_sparse.preprocessing.filters import StandardChannelScaler
from src.semg_sparse.models.classifiers import build_svm_model, build_rf_model, build_xgboost_model
from src.semg_sparse.features.handcrafted import get_feature_mapping

def run_sparse_models():
    print("=" * 70, flush=True)
    print("PHASE 8: SPARSE-CHANNEL MODEL OPTIMIZATION (k = 1..16)", flush=True)
    print("=" * 70, flush=True)

    feat_path = Path("data/features/grabmyo_features.parquet")
    rank_dir = Path("artifacts/rankings")

    if not feat_path.exists() or not rank_dir.exists():
        print("  [ERROR] Required feature file or rankings missing.", flush=True)
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

    results = []

    for test_pid in participants:
        rank_p = rank_dir / f"outer_subject_{test_pid:03d}.csv"
        if not rank_p.exists():
            continue
        df_rank = pd.read_csv(rank_p)
        ranking = df_rank['channel_id'].values # 0-indexed

        train_idx = (subs_all != test_pid)
        test_idx = (subs_all == test_pid)

        X_tr_full, y_tr = X_all[train_idx], y_all[train_idx]
        X_te_full, y_te = X_all[test_idx], y_all[test_idx]

        # Primary XGBoost evaluation across all k=1..16
        for k in range(1, 17):
            top_k_channels = ranking[:k]
            # Select features corresponding to top-k channels
            feat_mask = np.isin(channel_indices, top_k_channels)

            X_tr_k = X_tr_full[:, feat_mask]
            X_te_k = X_te_full[:, feat_mask]

            scaler = StandardChannelScaler()
            X_tr_k_scaled = scaler.fit_transform(X_tr_k)
            X_te_k_scaled = scaler.transform(X_te_k)

            model = build_xgboost_model()
            model.fit(X_tr_k_scaled, y_tr)
            preds = model.predict(X_te_k_scaled)

            macro_f1 = f1_score(y_te, preds, average='macro')
            bal_acc = balanced_accuracy_score(y_te, preds)
            acc = accuracy_score(y_te, preds)

            results.append({
                "participant_id": test_pid,
                "model": "M3_XGBoost",
                "selection_method": "CrossFitted_SHAP",
                "k": k,
                "macro_f1": macro_f1,
                "balanced_accuracy": bal_acc,
                "accuracy": acc
            })

        # Confirmatory models (SVM, RF) at k in {4, 6, 8, 10, 12, 16}
        conf_models = {"M1_SVM": build_svm_model, "M2_RF": build_rf_model}
        for k in [4, 6, 8, 10, 12, 16]:
            top_k_channels = ranking[:k]
            feat_mask = np.isin(channel_indices, top_k_channels)

            X_tr_k = X_tr_full[:, feat_mask]
            X_te_k = X_te_full[:, feat_mask]

            scaler = StandardChannelScaler()
            X_tr_k_scaled = scaler.fit_transform(X_tr_k)
            X_te_k_scaled = scaler.transform(X_te_k)

            for m_name, m_builder in conf_models.items():
                model = m_builder()
                model.fit(X_tr_k_scaled, y_tr)
                preds = model.predict(X_te_k_scaled)

                macro_f1 = f1_score(y_te, preds, average='macro')
                bal_acc = balanced_accuracy_score(y_te, preds)
                acc = accuracy_score(y_te, preds)

                results.append({
                    "participant_id": test_pid,
                    "model": m_name,
                    "selection_method": "CrossFitted_SHAP",
                    "k": k,
                    "macro_f1": macro_f1,
                    "balanced_accuracy": bal_acc,
                    "accuracy": acc
                })

        print(f"  [OK] Completed sparse evaluation for Participant {test_pid:02d}", flush=True)

    out_dir = Path("artifacts/metrics")
    out_dir.mkdir(parents=True, exist_ok=True)
    df_res = pd.DataFrame(results)
    df_res.to_csv(out_dir / "sparse_models_subject_metrics.csv", index=False)
    df_res.to_parquet(out_dir / "sparse_models_subject_metrics.parquet", index=False)

    # Summary
    summary = df_res.groupby(['model', 'selection_method', 'k']).agg(
        mean_macro_f1=('macro_f1', 'mean'),
        std_macro_f1=('macro_f1', 'std')
    ).reset_index()
    summary.to_csv(out_dir / "sparse_models_summary.csv", index=False)

    print("\nSparse Models XGBoost Curve Summary:")
    print(summary[summary['model'] == 'M3_XGBoost'].to_string(index=False), flush=True)

if __name__ == "__main__":
    run_sparse_models()
