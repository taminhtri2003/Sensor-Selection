"""Full-channel subject-independent LOSO baseline over the complete GRABMyo cohort.

Primary task: 16 active gestures (gesture 17 = Rest excluded; see MotionSequence.txt).
Statistical unit: participant. 43 outer folds, one per held-out participant.

Leakage controls:
  - the held-out participant contributes to nothing: not model fitting, not the scaler.
  - the standardiser is fitted on outer-training windows only and applied to the test fold.

Compute protocol (documented, not hidden):
  - XGBoost and Random Forest are fitted on all outer-training windows (~550k).
  - RBF SVM is O(n^2)-O(n^3) in sample count and cannot be fitted on 550k windows. It is fitted
    on a stratified random subsample of SVM_SUBSAMPLE training windows with a fixed seed,
    identically for every fold. This is a compute constraint and is reported as such.

Results are appended per fold so the run is resumable and partial progress is inspectable.

Outputs:
  artifacts/metrics/loso_full_channel_subject_metrics.csv
  artifacts/metrics/loso_full_channel_summary.csv
  artifacts/predictions/loso_full_channel_predictions.parquet
"""

import argparse
import json
import platform
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score
from sklearn.model_selection import StratifiedShuffleSplit
from sklearn.svm import SVC
import xgboost as xgb

ROOT = Path(__file__).resolve().parent.parent
FEATURES = ROOT / "data" / "features" / "grabmyo_features_full.parquet"
OUT_METRICS = ROOT / "artifacts" / "metrics"
OUT_PRED = ROOT / "artifacts" / "predictions"

META_COLS = ["dataset", "participant_id", "session_id", "gesture_id", "trial_id",
             "window_idx", "start_sample", "end_sample"]
N_ACTIVE_CLASSES = 16
SEED = 20260728
SVM_SUBSAMPLE = 40000

XGB_PARAMS = dict(n_estimators=300, max_depth=6, learning_rate=0.1, subsample=0.8,
                  colsample_bytree=0.8, tree_method="hist", random_state=SEED, verbosity=0)
RF_PARAMS = dict(n_estimators=200, max_depth=None, min_samples_leaf=2,
                 n_jobs=-1, random_state=SEED)
SVM_PARAMS = dict(C=1.0, kernel="rbf", gamma="scale", random_state=SEED)


def load_primary():
    df = pd.read_parquet(FEATURES)
    fcols = [c for c in df.columns if c not in META_COLS]
    d = df[df.gesture_id <= N_ACTIVE_CLASSES]
    X = d[fcols].to_numpy(np.float32)
    y = (d.gesture_id.to_numpy() - 1).astype(np.int64)
    subj = d.participant_id.to_numpy()
    sess = d.session_id.to_numpy()
    return X, y, subj, sess, fcols


def metrics_row(pid, model, k, y_true, y_pred, fit_s, n_tr):
    return {
        "participant_id": int(pid), "model": model, "channels_k": k,
        "macro_f1": f1_score(y_true, y_pred, average="macro"),
        "balanced_accuracy": balanced_accuracy_score(y_true, y_pred),
        "accuracy": accuracy_score(y_true, y_pred),
        "weighted_f1": f1_score(y_true, y_pred, average="weighted"),
        "n_train_windows": int(n_tr), "n_test_windows": int(len(y_true)),
        "fit_seconds": round(fit_s, 2),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default="XGB,SVM,RF")
    ap.add_argument("--device", default="cuda")
    args = ap.parse_args()
    want = [m.strip().upper() for m in args.models.split(",") if m.strip()]

    OUT_METRICS.mkdir(parents=True, exist_ok=True)
    OUT_PRED.mkdir(parents=True, exist_ok=True)

    X, y, subj, sess, fcols = load_primary()
    participants = sorted(np.unique(subj))
    print(f"windows={X.shape[0]} features={X.shape[1]} classes={len(np.unique(y))} "
          f"participants={len(participants)}", flush=True)

    prov = {
        "seed": SEED, "n_classes": N_ACTIVE_CLASSES, "svm_subsample": SVM_SUBSAMPLE,
        "xgb": XGB_PARAMS, "rf": RF_PARAMS, "svm": SVM_PARAMS,
        "features": fcols, "python": platform.python_version(),
        "xgboost": xgb.__version__, "device": args.device,
        "feature_file": str(FEATURES.relative_to(ROOT)).replace("\\", "/"),
    }
    (OUT_METRICS / "loso_full_channel_provenance.json").write_text(json.dumps(prov, indent=2))

    rows, preds = [], []
    metrics_path = OUT_METRICS / "loso_full_channel_subject_metrics.csv"

    for i, pid in enumerate(participants, 1):
        te = subj == pid
        tr = ~te
        mu = X[tr].mean(axis=0)
        sd = X[tr].std(axis=0) + 1e-8
        Xtr, Xte = (X[tr] - mu) / sd, (X[te] - mu) / sd
        ytr, yte = y[tr], y[te]

        fold = {}
        if "XGB" in want:
            t = time.time()
            m = xgb.XGBClassifier(device=args.device, **XGB_PARAMS)
            m.fit(Xtr, ytr)
            fold["M_XGBoost"] = (m.predict(Xte), time.time() - t, len(ytr))

        if "SVM" in want:
            n_sub = min(SVM_SUBSAMPLE, len(ytr))
            sss = StratifiedShuffleSplit(n_splits=1, train_size=n_sub, random_state=SEED)
            sub_idx, _ = next(sss.split(Xtr, ytr))
            t = time.time()
            m = SVC(**SVM_PARAMS)
            m.fit(Xtr[sub_idx], ytr[sub_idx])
            fold["M_SVM"] = (m.predict(Xte), time.time() - t, n_sub)

        if "RF" in want:
            t = time.time()
            m = RandomForestClassifier(**RF_PARAMS)
            m.fit(Xtr, ytr)
            fold["M_RandomForest"] = (m.predict(Xte), time.time() - t, len(ytr))

        for name, (yp, secs, n_tr) in fold.items():
            rows.append(metrics_row(pid, name, 16, yte, yp, secs, n_tr))
            preds.append(pd.DataFrame({
                "participant_id": pid, "model": name,
                "session_id": sess[te], "y_true": yte, "y_pred": yp,
            }))

        pd.DataFrame(rows).to_csv(metrics_path, index=False)
        got = {r["model"]: round(r["macro_f1"], 4) for r in rows if r["participant_id"] == pid}
        print(f"[{i}/{len(participants)}] participant {pid:02d}  {got}", flush=True)

    df_rows = pd.DataFrame(rows)
    pd.concat(preds, ignore_index=True).to_parquet(
        OUT_PRED / "loso_full_channel_predictions.parquet", index=False)

    summary = (df_rows.groupby("model")
               .agg(n_participants=("participant_id", "nunique"),
                    mean_macro_f1=("macro_f1", "mean"),
                    sd_macro_f1=("macro_f1", "std"),
                    median_macro_f1=("macro_f1", "median"),
                    min_macro_f1=("macro_f1", "min"),
                    max_macro_f1=("macro_f1", "max"),
                    mean_balanced_accuracy=("balanced_accuracy", "mean"),
                    mean_accuracy=("accuracy", "mean"),
                    mean_weighted_f1=("weighted_f1", "mean"),
                    total_fit_seconds=("fit_seconds", "sum"))
               .reset_index().sort_values("mean_macro_f1", ascending=False))
    summary.to_csv(OUT_METRICS / "loso_full_channel_summary.csv", index=False)

    print("\n" + summary.to_string(index=False), flush=True)
    n_bad = df_rows.groupby("model")["participant_id"].nunique().ne(len(participants)).sum()
    if n_bad:
        print("COHORT ASSERTION FAILED: not every model covers every participant")
        return 1
    print(f"\nCOHORT ASSERTION PASSED: {len(participants)} participants x {len(want)} models")
    return 0


if __name__ == "__main__":
    sys.exit(main())
