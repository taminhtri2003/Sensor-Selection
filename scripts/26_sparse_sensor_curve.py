"""Sparse sensor curve: retrain from scratch on the top-k channels of each outer fold's ranking.

The critical control: for held-out participant p, the channel subset comes from R_{-p}, the
ranking derived in P2 from the other 42 participants only. Participant p never influenced the
selection of the channels it is then evaluated on. A pipeline that ranks channels once on the
pooled dataset and reuses that ranking for every fold would leak, and would inflate every sparse
result; that is the single most common flaw in this literature.

Models are retrained from scratch at each k rather than masking features of a 16-channel model,
because a deployed k-sensor device would be trained on k sensors.

Outputs:
  artifacts/metrics/sparse_curve_subject_metrics.csv
  artifacts/metrics/sparse_curve_summary.csv
"""

import argparse
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score
from sklearn.model_selection import StratifiedShuffleSplit
from sklearn.svm import SVC
import xgboost as xgb

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "data" / "cache"
RANKINGS = ROOT / "artifacts" / "rankings" / "cross_fitted_rankings.csv"
OUT = ROOT / "artifacts" / "metrics"

SEED = 20260728
N_CHANNELS = 16
N_FPC = 10
XGB_PARAMS = dict(n_estimators=300, max_depth=6, learning_rate=0.1, subsample=0.8,
                  colsample_bytree=0.8, tree_method="hist", random_state=SEED, verbosity=0)
RF_PARAMS = dict(n_estimators=200, max_depth=None, min_samples_leaf=2, random_state=SEED)
SVM_PARAMS = dict(C=1.0, kernel="rbf", gamma="scale", random_state=SEED)
SVM_SUBSAMPLE = 40000
RF_SUBSAMPLE = 200000


def channel_columns(channels_1based):
    """Map 1-based channel ids to their feature-column indices (layout is channel-major)."""
    cols = []
    for c in channels_1based:
        start = (c - 1) * N_FPC
        cols.extend(range(start, start + N_FPC))
    return np.array(sorted(cols), dtype=np.int64)


def subsample(Xtr, ytr, n):
    if n is None or n >= len(ytr):
        return np.arange(len(ytr))
    sss = StratifiedShuffleSplit(n_splits=1, train_size=n, random_state=SEED)
    return next(sss.split(Xtr, ytr))[0]


def run_job(job):
    pid, lam, ranking, ks, paths, model, device, train_sub, rf_jobs, k_workers = job
    xp, yp, sp = paths
    X = np.load(xp, mmap_mode="r")
    y = np.load(yp, mmap_mode="r")
    subj = np.load(sp, mmap_mode="r")

    te = np.asarray(subj) == pid
    tr = ~te
    Xtr_full = np.asarray(X[tr], dtype=np.float32)
    Xte_full = np.asarray(X[te], dtype=np.float32)
    ytr, yte = np.asarray(y[tr]), np.asarray(y[te])

    if train_sub and train_sub < len(ytr):
        idx = subsample(Xtr_full, ytr, train_sub)
        Xtr_full, ytr = Xtr_full[idx], ytr[idx]

    def fit_one(k):
        chans = ranking[:k]
        cols = channel_columns(chans)
        Xtr, Xte = Xtr_full[:, cols], Xte_full[:, cols]

        mu = Xtr.mean(axis=0)
        sd = Xtr.std(axis=0) + 1e-8
        Xtr = (Xtr - mu) / sd
        Xte = (Xte - mu) / sd

        t = time.time()
        if model == "XGB":
            m = xgb.XGBClassifier(device=device, **XGB_PARAMS)
            m.fit(Xtr, ytr)
            n_used = len(ytr)
        elif model == "SVM":
            s = subsample(Xtr, ytr, SVM_SUBSAMPLE)
            m = SVC(**SVM_PARAMS)
            m.fit(Xtr[s], ytr[s])
            n_used = len(s)
        elif model == "RF":
            s = subsample(Xtr, ytr, RF_SUBSAMPLE)
            m = RandomForestClassifier(n_jobs=rf_jobs, **RF_PARAMS)
            m.fit(Xtr[s], ytr[s])
            n_used = len(s)
        else:
            raise ValueError(model)

        yp_ = m.predict(Xte)
        return {
            "participant_id": int(pid), "model": f"M_{model}", "lambda": lam,
            "channels_k": int(k), "channels": ";".join(map(str, chans)),
            "macro_f1": f1_score(yte, yp_, average="macro"),
            "balanced_accuracy": balanced_accuracy_score(yte, yp_),
            "accuracy": accuracy_score(yte, yp_),
            "weighted_f1": f1_score(yte, yp_, average="weighted"),
            "n_train_windows": int(n_used), "n_test_windows": int(len(yte)),
            "fit_seconds": round(time.time() - t, 2),
        }

    if model == "XGB" and k_workers > 1:
        with ThreadPoolExecutor(max_workers=k_workers) as tex:
            rows = list(tex.map(fit_one, ks))
    else:
        rows = [fit_one(k) for k in ks]
    return rows


def run_group(job):
    """Run all pending lambda rankings for one participant with shared fold data.

    A channel set is a sufficient key for the fitted model: channel_columns sorts the selected
    ids, and the per-feature scaler is identical regardless of the lambda that produced the
    ordering.  Reusing an evaluation when two lambda rankings yield the same top-k set is therefore
    exact, not an approximation, and is especially useful for the k=16 row (which is always all
    16 channels).
    """
    pid, lambda_jobs, ks, paths, model, device, train_sub, rf_jobs, k_workers = job
    if model != "XGB":
        raise ValueError("--group-lambdas is currently supported for XGB only")
    xp, yp, sp = paths
    X = np.load(xp, mmap_mode="r")
    y = np.load(yp, mmap_mode="r")
    subj = np.load(sp, mmap_mode="r")

    te = np.asarray(subj) == pid
    tr = ~te
    Xtr_full = np.asarray(X[tr], dtype=np.float32)
    Xte_full = np.asarray(X[te], dtype=np.float32)
    ytr, yte = np.asarray(y[tr]), np.asarray(y[te])
    if train_sub and train_sub < len(ytr):
        idx = subsample(Xtr_full, ytr, train_sub)
        Xtr_full, ytr = Xtr_full[idx], ytr[idx]

    unique = {}
    for lam, ranking in lambda_jobs:
        for k in ks:
            chans = ranking[:k]
            key = tuple(sorted(chans))
            unique.setdefault(key, chans)

    def fit_key(item):
        key, chans = item
        cols = channel_columns(chans)
        Xtr = Xtr_full[:, cols]
        Xte = Xte_full[:, cols]
        mu = Xtr.mean(axis=0)
        sd = Xtr.std(axis=0) + 1e-8
        t = time.time()
        model_obj = xgb.XGBClassifier(device=device, **XGB_PARAMS)
        model_obj.fit((Xtr - mu) / sd, ytr)
        yp_ = model_obj.predict((Xte - mu) / sd)
        return key, {
            "macro_f1": f1_score(yte, yp_, average="macro"),
            "balanced_accuracy": balanced_accuracy_score(yte, yp_),
            "accuracy": accuracy_score(yte, yp_),
            "weighted_f1": f1_score(yte, yp_, average="weighted"),
            "fit_seconds": round(time.time() - t, 2),
        }

    items = list(unique.items())
    if k_workers > 1 and len(items) > 1:
        with ThreadPoolExecutor(max_workers=k_workers) as tex:
            fitted = list(tex.map(fit_key, items))
    else:
        fitted = [fit_key(item) for item in items]
    cache = dict(fitted)

    rows = []
    seen = set()
    for lam, ranking in lambda_jobs:
        for k in ks:
            chans = ranking[:k]
            key = tuple(sorted(chans))
            metrics = cache[key]
            reused = key in seen
            seen.add(key)
            rows.append({
                "participant_id": int(pid), "model": "M_XGB", "lambda": lam,
                "channels_k": int(k), "channels": ";".join(map(str, chans)),
                **metrics, "fit_seconds": 0.0 if reused else metrics["fit_seconds"],
                "fit_reused": bool(reused),
                "n_train_windows": int(len(ytr)), "n_test_windows": int(len(yte)),
            })
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="XGB", choices=["XGB", "SVM", "RF"])
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--rf-jobs", type=int, default=2)
    ap.add_argument("--lambdas", default="0.0")
    ap.add_argument("--k-values", default="1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16")
    ap.add_argument("--train-subsample", type=int, default=0)
    ap.add_argument("--k-workers", type=int, default=1,
                    help="parallel XGBoost fits within one participant/lambda job")
    ap.add_argument("--group-lambdas", action="store_true",
                    help="share fold data and exact duplicate channel-set fits across lambdas")
    ap.add_argument("--participant-ids", default="",
                    help="comma-separated participant ids; empty means all")
    ap.add_argument("--tag", default="")
    ap.add_argument("--resume", action="store_true",
                    help="reuse complete participant/lambda jobs in the existing output")
    ap.add_argument("--cache-dir", type=Path, default=CACHE,
                    help="feature cache (decision 24b/c: 17-class or other window lengths)")
    ap.add_argument("--rankings", type=Path, default=RANKINGS,
                    help="outer-fold rankings; completion analyses reuse the primary rankings")
    ap.add_argument("--out-dir", type=Path, default=OUT,
                    help="isolated output directory for non-primary analyses")
    args = ap.parse_args()
    out_dir = args.out_dir.resolve()

    if not args.rankings.exists():
        print(f"FATAL: {args.rankings} missing — run scripts/25_cross_fitted_ranking.py first")
        return 2

    lams = [float(x) for x in args.lambdas.split(",")]
    ks = [int(x) for x in args.k_values.split(",")]
    out_dir.mkdir(parents=True, exist_ok=True)

    rank_df = pd.read_csv(args.rankings)
    cache = args.cache_dir.resolve()
    xp, yp, sp = cache / "loso_X.npy", cache / "loso_y.npy", cache / "loso_subj.npy"
    subj = np.load(sp, mmap_mode="r")
    participants = sorted(np.unique(np.asarray(subj)).tolist())
    if args.participant_ids.strip():
        wanted = {int(x) for x in args.participant_ids.split(",") if x.strip()}
        participants = [p for p in participants if int(p) in wanted]
        if not participants:
            print("FATAL: --participant-ids did not match any participant", flush=True)
            return 2

    jobs = []
    for pid in participants:
        for lam in lams:
            sel = rank_df[(rank_df.outer_participant == pid) &
                          (np.isclose(rank_df["lambda"], lam))]
            if sel.empty:
                print(f"FATAL: no ranking for participant {pid}, lambda {lam}")
                return 2
            ranking = [int(c) for c in sel.iloc[0]["ranking"].split(";")]
            if sorted(ranking) != list(range(1, N_CHANNELS + 1)):
                print(f"FATAL: ranking for participant {pid} is not a permutation of 1..16")
                return 2
            jobs.append((pid, lam, ranking, ks, (str(xp), str(yp), str(sp)),
                         args.model, args.device, args.train_subsample or None, args.rf_jobs,
                         args.k_workers))

    result_path = out_dir / f"sparse_curve_subject_metrics{args.tag}.csv"
    rows = []
    completed = set()
    if args.resume and result_path.exists():
        previous = pd.read_csv(result_path)
        expected_k = set(ks)
        for key, g in previous.groupby(["participant_id", "lambda"]):
            if set(g.channels_k.astype(int)) == expected_k:
                completed.add((int(key[0]), float(key[1])))
        rows = previous.to_dict("records")
        jobs = [j for j in jobs if (int(j[0]), float(j[1])) not in completed]
        print(f"resuming {len(completed)} completed participant/lambda jobs from {result_path}",
              flush=True)

    if args.group_lambdas:
        if args.model != "XGB":
            print("FATAL: --group-lambdas currently requires --model XGB", flush=True)
            return 2
        grouped = {}
        for j in jobs:
            pid, lam, ranking = int(j[0]), float(j[1]), j[2]
            grouped.setdefault(pid, []).append((lam, ranking))
        jobs = [
            (pid, sorted(lams_pending), ks, (j[4][0], j[4][1], j[4][2]),
             j[5], j[6], j[7], j[8], j[9])
            for pid, lams_pending in sorted(grouped.items())
            for j in [next(job for job in jobs if int(job[0]) == pid)]
        ]
        print(f"grouped pending lambda jobs into {len(jobs)} participant jobs", flush=True)

    print(f"model={args.model} participants={len(participants)} lambdas={lams} "
          f"k={ks} jobs={len(jobs)} workers={args.workers}", flush=True)

    t0, done = time.time(), 0
    worker_fn = run_group if args.group_lambdas else run_job
    def record(result):
        nonlocal rows, done
        rows.extend(result)
        done += 1
        el = time.time() - t0
        df = pd.DataFrame(rows)
        df.to_csv(result_path, index=False)
        last = rows[-1]
        print(f"[{done}/{len(jobs)}] participant {last['participant_id']:02d} "
              f"lam={last['lambda']} k16={df[(df.participant_id==last['participant_id'])&(df.channels_k==16)].macro_f1.max():.4f} "
              f"elapsed={el/60:.1f}m eta={el/done*(len(jobs)-done)/60:.1f}m", flush=True)

    if args.group_lambdas and args.workers == 1:
        # XGBoost/CUDA can retain allocator state across many large fits.  A
        # fresh worker per participant bounds that state and makes --resume
        # reliable on long runs; each completed participant is checkpointed
        # before the next worker is created.
        for job in jobs:
            with ProcessPoolExecutor(max_workers=1) as ex:
                record(ex.submit(worker_fn, job).result())
    else:
        with ProcessPoolExecutor(max_workers=args.workers) as ex:
            futs = [ex.submit(worker_fn, j) for j in jobs]
            for fut in as_completed(futs):
                record(fut.result())

    df = pd.DataFrame(rows)
    summary = (df.groupby(["model", "lambda", "channels_k"])
               .agg(n_participants=("participant_id", "nunique"),
                    mean_macro_f1=("macro_f1", "mean"),
                    sd_macro_f1=("macro_f1", "std"),
                    mean_accuracy=("accuracy", "mean"))
               .reset_index())
    summary.to_csv(out_dir / f"sparse_curve_summary{args.tag}.csv", index=False)
    print("\n" + summary.to_string(index=False), flush=True)

    bad = df.groupby(["lambda", "channels_k"]).participant_id.nunique().ne(len(participants))
    if bad.any():
        print(f"ASSERTION FAILED: incomplete cells: {bad[bad].index.tolist()[:5]}")
        return 1
    print(f"\nASSERTION PASSED: {len(participants)} participants x {len(ks)} k x {len(lams)} lambda")
    print(f"wall clock: {(time.time()-t0)/60:.1f} min")
    return 0


if __name__ == "__main__":
    sys.exit(main())
