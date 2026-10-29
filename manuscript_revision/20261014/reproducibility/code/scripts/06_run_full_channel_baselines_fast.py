import sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

"""
Script 06 (Fast Parallel): Full-Channel Baselines under Strict Subject-Independent LOSO.
Multi-process fold execution across 12 CPU workers.
"""

import os
import sys
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.metrics import f1_score, accuracy_score, balanced_accuracy_score
from concurrent.futures import ProcessPoolExecutor, as_completed

from src.semg_sparse.preprocessing.filters import StandardChannelScaler
from src.semg_sparse.models.classifiers import build_svm_model, build_rf_model, build_xgboost_model

def evaluate_single_participant_fold(test_pid, X_all, y_all, subs_all):
    train_idx = (subs_all != test_pid)
    test_idx = (subs_all == test_pid)

    X_tr, y_tr = X_all[train_idx], y_all[train_idx]
    X_te, y_te = X_all[test_idx], y_all[test_idx]

    scaler = StandardChannelScaler()
    X_tr_scaled = scaler.fit_transform(X_tr)
    X_te_scaled = scaler.transform(X_te)

    models = {
        "M1_SVM": build_svm_model,
        "M2_RF": build_rf_model,
        "M3_XGBoost": build_xgboost_model
    }

    fold_results = []
    for m_name, m_builder in models.items():
        model = m_builder()
        model.fit(X_tr_scaled, y_tr)
        preds = model.predict(X_te_scaled)

        macro_f1 = f1_score(y_te, preds, average='macro')
        bal_acc = balanced_accuracy_score(y_te, preds)
        acc = accuracy_score(y_te, preds)
        weighted_f1 = f1_score(y_te, preds, average='weighted')

        fold_results.append({
            "participant_id": test_pid,
            "model": m_name,
            "channels_k": 16,
            "macro_f1": macro_f1,
            "balanced_accuracy": bal_acc,
            "accuracy": acc,
            "weighted_f1": weighted_f1
        })
    return fold_results

def run_full_channel_baselines_fast():
    print("=" * 70, flush=True)
    print("PHASE 6 (FAST PARALLEL): FULL-CHANNEL BASELINE EVALUATION", flush=True)
    print("=" * 70, flush=True)

    feat_path = Path("data/features/grabmyo_features.parquet")
    if not feat_path.exists():
        print("  [ERROR] Feature file not found.", flush=True)
        return

    df = pd.read_parquet(feat_path)
    df_primary = df[df['gesture_id'] <= 16].copy()
    participants = sorted(df_primary['participant_id'].unique())
    print(f"  Total participants: {len(participants)}", flush=True)

    meta_cols = ['dataset', 'participant_id', 'session_id', 'gesture_id', 'trial_id', 'window_idx', 'start_sample', 'end_sample']
    feature_cols = [c for c in df_primary.columns if c not in meta_cols]

    X_all = df_primary[feature_cols].values.astype(np.float32)
    y_all = (df_primary['gesture_id'].values - 1).astype(np.int64)
    subs_all = df_primary['participant_id'].values

    results = []
    with ProcessPoolExecutor(max_workers=12) as executor:
        futures = [executor.submit(evaluate_single_participant_fold, pid, X_all, y_all, subs_all) for pid in participants]
        for future in as_completed(futures):
            res = future.result()
            results.extend(res)
            print(f"  [OK] Completed Fold for Participant {res[0]['participant_id']:02d}", flush=True)

    out_dir = Path("artifacts/metrics")
    out_dir.mkdir(parents=True, exist_ok=True)
    df_res = pd.DataFrame(results)
    df_res.to_csv(out_dir / "full_channel_subject_metrics.csv", index=False)
    df_res.to_parquet(out_dir / "full_channel_subject_metrics.parquet", index=False)

    summary = df_res.groupby('model').agg(
        mean_macro_f1=('macro_f1', 'mean'),
        std_macro_f1=('macro_f1', 'std'),
        mean_accuracy=('accuracy', 'mean')
    ).reset_index()
    summary.to_csv(out_dir / "full_channel_summary.csv", index=False)

    print("\nFull-Channel LOSO Summary:")
    print(summary.to_string(index=False), flush=True)

if __name__ == "__main__":
    run_full_channel_baselines_fast()
