import sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
"""
Script 06: Full-Channel Baselines (M1-M4) under Strict Subject-Independent LOSO.
Evaluates SVM, Random Forest, XGBoost, and 1D CNN using all 16 channels.
Computes participant-level metrics and stores artifacts under artifacts/metrics/.
"""

import os
import sys
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.metrics import f1_score, accuracy_score, balanced_accuracy_score

from src.semg_sparse.preprocessing.filters import StandardChannelScaler
from src.semg_sparse.models.classifiers import build_svm_model, build_rf_model, build_xgboost_model, CNNWrapper

def run_full_channel_baselines():
    print("=" * 70, flush=True)
    print("PHASE 6: FULL-CHANNEL BASELINE EVALUATION (STRICT LOSO)", flush=True)
    print("=" * 70, flush=True)

    feat_path = Path("data/features/grabmyo_features.parquet")
    if not feat_path.exists():
        print("  [ERROR] Feature file data/features/grabmyo_features.parquet not found.", flush=True)
        return

    df = pd.read_parquet(feat_path)
    
    # Exclude rest class for primary task if rest is gesture_id == 17
    # Or keep active gestures 1-16
    df_primary = df[df['gesture_id'] <= 16].copy()
    
    participants = sorted(df_primary['participant_id'].unique())
    print(f"  Total participants: {len(participants)}", flush=True)

    # Feature columns (160 features)
    meta_cols = ['dataset', 'participant_id', 'session_id', 'gesture_id', 'trial_id', 'window_idx', 'start_sample', 'end_sample']
    feature_cols = [c for c in df_primary.columns if c not in meta_cols]

    X_all = df_primary[feature_cols].values.astype(np.float32)
    y_all = (df_primary['gesture_id'].values - 1).astype(np.int64) # 0-indexed classes
    subs_all = df_primary['participant_id'].values

    models = {
        "M1_SVM": build_svm_model,
        "M2_RF": build_rf_model,
        "M3_XGBoost": build_xgboost_model
    }

    results = []

    for test_pid in participants:
        train_idx = (subs_all != test_pid)
        test_idx = (subs_all == test_pid)

        X_tr, y_tr = X_all[train_idx], y_all[train_idx]
        X_te, y_te = X_all[test_idx], y_all[test_idx]

        # Zero leakage scaler fit exclusively on training participants
        scaler = StandardChannelScaler()
        X_tr_scaled = scaler.fit_transform(X_tr)
        X_te_scaled = scaler.transform(X_te)

        for m_name, m_builder in models.items():
            model = m_builder()
            model.fit(X_tr_scaled, y_tr)
            preds = model.predict(X_te_scaled)

            macro_f1 = f1_score(y_te, preds, average='macro')
            bal_acc = balanced_accuracy_score(y_te, preds)
            acc = accuracy_score(y_te, preds)
            weighted_f1 = f1_score(y_te, preds, average='weighted')

            results.append({
                "participant_id": test_pid,
                "model": m_name,
                "channels_k": 16,
                "macro_f1": macro_f1,
                "balanced_accuracy": bal_acc,
                "accuracy": acc,
                "weighted_f1": weighted_f1
            })

        print(f"  [OK] Evaluated Participant {test_pid:02d}/{len(participants)}", flush=True)

    out_dir = Path("artifacts/metrics")
    out_dir.mkdir(parents=True, exist_ok=True)
    df_res = pd.DataFrame(results)
    df_res.to_csv(out_dir / "full_channel_subject_metrics.csv", index=False)
    df_res.to_parquet(out_dir / "full_channel_subject_metrics.parquet", index=False)

    # Summary table
    summary = df_res.groupby('model').agg(
        mean_macro_f1=('macro_f1', 'mean'),
        std_macro_f1=('macro_f1', 'std'),
        mean_accuracy=('accuracy', 'mean')
    ).reset_index()
    summary.to_csv(out_dir / "full_channel_summary.csv", index=False)

    print("\nFull-Channel LOSO Summary:")
    print(summary.to_string(index=False), flush=True)

if __name__ == "__main__":
    run_full_channel_baselines()
