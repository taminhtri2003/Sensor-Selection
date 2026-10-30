"""Full-channel subject-independent LOSO — parallel across outer folds.

Same protocol and same leakage controls as scripts/21_full_channel_loso.py; only the execution
strategy differs. Folds are independent by construction (each holds out one participant), so
running them concurrently changes nothing statistically.

Memory: the feature matrix is written once to .npy and memory-mapped by every worker, so the
~360 MB matrix is paged once by the OS rather than copied per process.

Leakage controls (unchanged):
  - held-out participant contributes to nothing: not fitting, not the standardiser
  - standardiser statistics come from outer-training windows only

Outputs:
  artifacts/metrics/loso_full_channel_subject_metrics.csv
  artifacts/metrics/loso_full_channel_summary.csv
  artifacts/predictions/loso_full_channel_predictions.parquet
"""

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score
from sklearn.model_selection import StratifiedShuffleSplit
from sklearn.svm import SVC
import xgboost as xgb

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src.semg_sparse.checkpoints import atomic_csv, ensure_protocol, sha256
FEATURES = ROOT / "data" / "features" / "grabmyo_features_full.parquet"
CACHE = ROOT / "data" / "cache"
OUT_METRICS = ROOT / "artifacts" / "metrics"
OUT_PRED = ROOT / "artifacts" / "predictions"

META_COLS = ["dataset", "participant_id", "session_id", "gesture_id", "trial_id",
             "window_idx", "start_sample", "end_sample"]
N_ACTIVE_CLASSES = 16
SEED = 20260728

# Training-window budgets per model, set from measured cost/accuracy on a fixed fold
# (see reports/decision_log.md, Decision 6). Neither is a hyperparameter change: model settings
# are identical to the full-data configuration, only the number of training windows differs.
#
#   RF  550k -> 287.4 s, Macro-F1 0.5304
#   RF  200k ->  97.2 s, Macro-F1 0.5309   <- 3x faster, no accuracy cost
#   SVM  20k ->  75.4 s, Macro-F1 0.5554
#   SVM  40k -> 376.2 s, Macro-F1 0.5911   <- SVM still gains from data; do NOT reduce further
SVM_SUBSAMPLE = 40000
RF_SUBSAMPLE = 200000

XGB_PARAMS = dict(n_estimators=300, max_depth=6, learning_rate=0.1, subsample=0.8,
                  colsample_bytree=0.8, tree_method="hist", random_state=SEED, verbosity=0)
RF_PARAMS = dict(n_estimators=200, max_depth=None, min_samples_leaf=2, random_state=SEED)
SVM_PARAMS = dict(C=1.0, kernel="rbf", gamma="scale", random_state=SEED)
MODEL_LABELS = {'XGB': 'M_XGBoost', 'SVM': 'M_SVM', 'RF': 'M_RandomForest'}


def checkpoint_protocol(paths, feature_names, want, device, rf_jobs):
    """The fit inputs and settings must agree before any completed fold is reused."""
    return {
        'version': 1, 'models': sorted(want), 'device': device, 'rf_jobs': rf_jobs,
        'seed': SEED, 'n_classes': N_ACTIVE_CLASSES, 'feature_names': list(feature_names),
        'svm_subsample': SVM_SUBSAMPLE, 'rf_subsample': RF_SUBSAMPLE,
        'xgb': XGB_PARAMS, 'rf': RF_PARAMS, 'svm': SVM_PARAMS,
        'cache': {Path(path).name: sha256(path) for path in paths},
        'sources': {name: sha256(ROOT / name) for name in (
            'scripts/24_full_channel_loso_parallel.py', 'src/semg_sparse/checkpoints.py')},
        'python': platform.python_version(),
        'versions': {name: importlib.metadata.version(name) for name in (
            'numpy', 'pandas', 'scipy', 'scikit-learn', 'xgboost')},
    }


def write_fold_checkpoint(path, results, row_index, protocol_hash):
    """Publish predictions and metrics together, so a partial fold cannot be resumed."""
    path = Path(path)
    arrays = {'row_index': np.asarray(row_index, dtype=np.int64)}
    metadata = []
    for i, row in enumerate(results):
        metadata.append({key: value.item() if isinstance(value, np.generic) else value
                         for key, value in row.items() if not key.startswith('_')})
        for key in ('_pred', '_true', '_sess'):
            arrays[f'{i}{key}'] = np.asarray(row[key])
    arrays['metadata'] = np.array(json.dumps({'protocol_hash': protocol_hash, 'rows': metadata}))
    temp = path.with_suffix('.npz.tmp')
    try:
        with temp.open('wb') as handle:
            np.savez_compressed(handle, **arrays)
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)


def validate_fold_results(results, pid, want, y_true, sessions, n_train):
    expected = {MODEL_LABELS[name] for name in want}
    if len(results) != len(expected) or {row.get('model') for row in results} != expected:
        raise ValueError('checkpoint does not contain exactly the requested model grid')
    metrics = {'macro_f1': lambda a, b: f1_score(a, b, average='macro'),
               'accuracy': accuracy_score, 'balanced_accuracy': balanced_accuracy_score,
               'weighted_f1': lambda a, b: f1_score(a, b, average='weighted')}
    for row in results:
        if row.get('participant_id') != pid or row.get('channels_k') != 16:
            raise ValueError('checkpoint participant or channel identity mismatch')
        budget = {'M_XGBoost': n_train, 'M_SVM': min(n_train, SVM_SUBSAMPLE),
                  'M_RandomForest': min(n_train, RF_SUBSAMPLE)}[row['model']]
        if row.get('n_train_windows') != budget or row.get('n_test_windows') != len(y_true):
            raise ValueError('checkpoint training/test window count mismatch')
        if not np.isfinite(row.get('fit_seconds', np.nan)) or row['fit_seconds'] < 0:
            raise ValueError('checkpoint fit time is invalid')
        for key, expected_values in (('_true', y_true), ('_sess', sessions)):
            if not np.array_equal(row.get(key), expected_values):
                raise ValueError('checkpoint test labels or session/window alignment mismatch')
        pred = np.asarray(row.get('_pred'))
        if (pred.shape != np.asarray(y_true).shape or not np.issubdtype(pred.dtype, np.integer)
                or (pred < 0).any() or (pred >= N_ACTIVE_CLASSES).any()):
            raise ValueError('checkpoint predictions have invalid labels or shape')
        for key, metric in metrics.items():
            value = row.get(key, np.nan)
            if not np.isfinite(value) or not np.isclose(value, metric(y_true, pred), atol=1e-12, rtol=0):
                raise ValueError('checkpoint metric differs from its saved predictions')
    return results


def load_fold_checkpoint(path, pid, want, row_index, y_true, sessions, n_train, protocol_hash):
    try:
        with np.load(path, allow_pickle=False) as saved:
            meta = json.loads(str(saved['metadata'].item()))
            if meta['protocol_hash'] != protocol_hash:
                raise ValueError('checkpoint protocol differs from the current fit')
            if not np.array_equal(saved['row_index'], row_index):
                raise ValueError('checkpoint cache window order differs')
            results = meta['rows']
            for i, row in enumerate(results):
                for key in ('_pred', '_true', '_sess'):
                    row[key] = saved[f'{i}{key}'].copy()
        return validate_fold_results(results, pid, want, y_true, sessions, n_train)
    except Exception as exc:
        raise ValueError(f'invalid or incomplete fold checkpoint {path}: {exc}') from exc


def build_cache():
    CACHE.mkdir(parents=True, exist_ok=True)
    xp, yp, sp, ep = (CACHE / f"loso_{n}.npy" for n in ("X", "y", "subj", "sess"))
    fj = CACHE / "loso_features.json"
    if all(p.exists() for p in (xp, yp, sp, ep, fj)):
        return xp, yp, sp, ep, json.loads(fj.read_text())

    df = pd.read_parquet(FEATURES)
    fcols = [c for c in df.columns if c not in META_COLS]
    d = df[df.gesture_id <= N_ACTIVE_CLASSES]
    np.save(xp, d[fcols].to_numpy(np.float32))
    np.save(yp, (d.gesture_id.to_numpy() - 1).astype(np.int64))
    np.save(sp, d.participant_id.to_numpy().astype(np.int32))
    np.save(ep, d.session_id.to_numpy().astype(np.int32))
    fj.write_text(json.dumps(fcols))
    return xp, yp, sp, ep, fcols


def run_fold(job):
    pid, paths, want, device, rf_jobs = job
    xp, yp, sp, ep = paths
    X = np.load(xp, mmap_mode="r")
    y = np.load(yp, mmap_mode="r")
    subj = np.load(sp, mmap_mode="r")
    sess = np.load(ep, mmap_mode="r")

    te = np.asarray(subj) == pid
    tr = ~te
    Xtr = np.asarray(X[tr], dtype=np.float32)
    Xte = np.asarray(X[te], dtype=np.float32)
    ytr, yte = np.asarray(y[tr]), np.asarray(y[te])
    sess_te = np.asarray(sess[te])

    mu = Xtr.mean(axis=0)
    sd = Xtr.std(axis=0) + 1e-8
    Xtr = (Xtr - mu) / sd
    Xte = (Xte - mu) / sd

    out = []
    for name in want:
        t = time.time()
        if name == "XGB":
            m = xgb.XGBClassifier(device=device, **XGB_PARAMS)
            m.fit(Xtr, ytr)
            yp_ = m.predict(Xte)
            n_used = len(ytr)
            label = "M_XGBoost"
        elif name == "SVM":
            n_sub = min(SVM_SUBSAMPLE, len(ytr))
            sss = StratifiedShuffleSplit(n_splits=1, train_size=n_sub, random_state=SEED)
            idx, _ = next(sss.split(Xtr, ytr))
            m = SVC(**SVM_PARAMS)
            m.fit(Xtr[idx], ytr[idx])
            yp_ = m.predict(Xte)
            n_used = n_sub
            label = "M_SVM"
        elif name == "RF":
            n_sub = min(RF_SUBSAMPLE, len(ytr))
            if n_sub < len(ytr):
                sss = StratifiedShuffleSplit(n_splits=1, train_size=n_sub, random_state=SEED)
                idx, _ = next(sss.split(Xtr, ytr))
            else:
                idx = np.arange(len(ytr))
            m = RandomForestClassifier(n_jobs=rf_jobs, **RF_PARAMS)
            m.fit(Xtr[idx], ytr[idx])
            yp_ = m.predict(Xte)
            n_used = n_sub
            label = "M_RandomForest"
        else:
            continue
        out.append({
            "participant_id": int(pid), "model": label, "channels_k": 16,
            "macro_f1": f1_score(yte, yp_, average="macro"),
            "balanced_accuracy": balanced_accuracy_score(yte, yp_),
            "accuracy": accuracy_score(yte, yp_),
            "weighted_f1": f1_score(yte, yp_, average="weighted"),
            "n_train_windows": int(n_used), "n_test_windows": int(len(yte)),
            "fit_seconds": round(time.time() - t, 2),
            "_pred": yp_.astype(np.int16), "_true": yte.astype(np.int16),
            "_sess": sess_te.astype(np.int16),
        })
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default="XGB,SVM,RF")
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--workers", type=int, default=5)
    ap.add_argument("--rf-jobs", type=int, default=2)
    ap.add_argument("--tag", default="",
                    help="suffix for output files so concurrent runs do not collide")
    ap.add_argument('--resume', action='store_true',
                    help='reuse validated complete per-participant prediction checkpoints')
    args = ap.parse_args()
    want = [m.strip().upper() for m in args.models.split(",") if m.strip()]
    if not want or len(want) != len(set(want)) or set(want) - set(MODEL_LABELS):
        raise ValueError('models must be a unique nonempty subset of XGB,SVM,RF')

    OUT_METRICS.mkdir(parents=True, exist_ok=True)
    OUT_PRED.mkdir(parents=True, exist_ok=True)

    xp, yp, sp, ep, fcols = build_cache()
    subj = np.load(sp, mmap_mode="r")
    participants = sorted(np.unique(np.asarray(subj)).tolist())
    paths = (xp, yp, sp, ep)
    y = np.load(yp, mmap_mode='r')
    sessions = np.load(ep, mmap_mode='r')
    if len(y) != len(subj) or len(sessions) != len(subj):
        raise ValueError('cache labels, participants and sessions have incompatible window counts')
    checkpoint_dir = OUT_PRED / f'loso_full_channel_checkpoints{args.tag}'
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    protocol = checkpoint_protocol(paths, fcols, want, args.device, args.rf_jobs)
    protocol_path = checkpoint_dir / 'folds.npz'
    if args.resume and any(checkpoint_dir.glob('outer_*.npz')) and not protocol_path.with_suffix('.protocol.json').exists():
        raise ValueError('fold checkpoints have no protocol fingerprint; use a new --tag')
    ensure_protocol(protocol_path, protocol, args.resume)
    protocol_hash = hashlib.sha256(json.dumps(protocol, sort_keys=True).encode()).hexdigest()
    completed = {}
    if args.resume:
        expected_paths = {checkpoint_dir / f'outer_{int(pid):02d}.npz' for pid in participants}
        if set(checkpoint_dir.glob('outer_*.npz')) - expected_paths:
            raise ValueError('checkpoint directory contains unexpected participants')
        for pid in participants:
            path = checkpoint_dir / f'outer_{int(pid):02d}.npz'
            if path.exists():
                idx = np.flatnonzero(np.asarray(subj) == pid)
                completed[pid] = load_fold_checkpoint(path, pid, want, idx, y[idx], sessions[idx],
                                                      len(subj) - len(idx), protocol_hash)
        print(f'resuming {len(completed)}/{len(participants)} complete participant folds', flush=True)
    print(f"participants={len(participants)} features={len(fcols)} "
          f"workers={args.workers} models={want}", flush=True)

    (OUT_METRICS / f"loso_full_channel_provenance{args.tag}.json").write_text(json.dumps({
        "seed": SEED, "n_classes": N_ACTIVE_CLASSES,
        "svm_subsample": SVM_SUBSAMPLE, "rf_subsample": RF_SUBSAMPLE,
        "xgb": XGB_PARAMS, "rf": RF_PARAMS, "svm": SVM_PARAMS,
        "n_features": len(fcols), "python": platform.python_version(),
        "xgboost": xgb.__version__, "device": args.device, "workers": args.workers,
        "feature_file": str(FEATURES.relative_to(ROOT)).replace("\\", "/"),
    }, indent=2))

    jobs = [(p, (str(xp), str(yp), str(sp), str(ep)), want, args.device, args.rf_jobs)
            for p in participants if p not in completed]

    rows, preds = [], []
    def collect(res):
        for row in res:
            preds.append(pd.DataFrame({
                'participant_id': row['participant_id'], 'model': row['model'],
                'session_id': row['_sess'], 'y_true': row['_true'], 'y_pred': row['_pred'],
            }))
            rows.append({key: value for key, value in row.items() if not key.startswith('_')})

    for res in completed.values():
        collect(res)
    t0 = time.time()
    done = 0
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        futs = [ex.submit(run_fold, j) for j in jobs]
        for fut in as_completed(futs):
            res = fut.result()
            done += 1
            pid = res[0]['participant_id'] if res else None
            if pid not in participants or pid in completed:
                raise ValueError('worker returned an unexpected or repeated participant')
            idx = np.flatnonzero(np.asarray(subj) == pid)
            validate_fold_results(res, pid, want, y[idx], sessions[idx], len(subj) - len(idx))
            write_fold_checkpoint(checkpoint_dir / f'outer_{int(pid):02d}.npz', res, idx, protocol_hash)
            completed[pid] = res
            collect(res)
            atomic_csv(pd.DataFrame(rows), OUT_METRICS / f"loso_full_channel_subject_metrics{args.tag}.csv")
            pid = res[0]["participant_id"] if res else "?"
            got = {r["model"].replace("M_", ""): round(r["macro_f1"], 4) for r in res}
            el = time.time() - t0
            eta = el / done * (len(jobs) - done)
            print(f"[{done}/{len(jobs)}] participant {pid:02d} {got}  "
                  f"elapsed={el/60:.1f}m eta={eta/60:.1f}m", flush=True)

    df_rows = pd.DataFrame(rows)
    atomic_csv(df_rows, OUT_METRICS / f"loso_full_channel_subject_metrics{args.tag}.csv")
    prediction_path = OUT_PRED / f"loso_full_channel_predictions{args.tag}.parquet"
    prediction_temp = prediction_path.with_suffix('.parquet.tmp')
    try:
        pd.concat(preds, ignore_index=True).to_parquet(prediction_temp, index=False)
        prediction_temp.replace(prediction_path)
    finally:
        prediction_temp.unlink(missing_ok=True)

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
    atomic_csv(summary, OUT_METRICS / f"loso_full_channel_summary{args.tag}.csv")
    print("\n" + summary.to_string(index=False), flush=True)

    bad = df_rows.groupby("model")["participant_id"].nunique().ne(len(participants))
    if bad.any():
        print(f"COHORT ASSERTION FAILED: {bad[bad].index.tolist()}")
        return 1
    print(f"\nCOHORT ASSERTION PASSED: {len(participants)} participants x {len(want)} models")
    print(f"wall clock: {(time.time()-t0)/60:.1f} min")
    return 0


if __name__ == "__main__":
    sys.exit(main())
