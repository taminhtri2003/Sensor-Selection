"""Bipolar sensitivity analysis for the 8 derived channels.

The primary GRABMyo unit is a monopolar electrode.  This script repeats the LOSO baseline and
the cross-fitted sparse curve after deriving the eight bipolar pairs F_j - F_{j+8}.  It uses only
the active 16-gesture rows and keeps every ranking, scaler, and model inside the corresponding
outer-training fold.  The curve uses the same 200,000-window training budget as P3; the full
8-channel baseline uses all outer-training windows, matching P1.

Outputs:
  artifacts/bipolar/bipolar_full_channel_metrics.csv
  artifacts/bipolar/bipolar_rankings.csv
  artifacts/bipolar/bipolar_scores.csv
  artifacts/bipolar/bipolar_sparse_curve.csv
  artifacts/bipolar/bipolar_summary.csv
  artifacts/bipolar/bipolar_provenance.json
"""

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score
from sklearn.model_selection import StratifiedShuffleSplit
import xgboost as xgb

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.semg_sparse.xai.cross_fitted import (  # noqa: E402
    assert_channel_major,
    compute_cross_fitted_attribution,
)

FEATURES = ROOT / "data" / "features" / "grabmyo_bipolar_features.parquet"
OUT = ROOT / "artifacts" / "bipolar"

SEED = 20260728
N_CHANNELS = 8
N_FPC = 10
ACTIVE_GESTURES = 16
LAMBDAS = (0.0, 0.25, 0.5, 1.0)
CURVE_TRAIN_SUBSAMPLE = 200000
META_COLS = ["dataset", "participant_id", "session_id", "gesture_id", "trial_id", "window_idx"]
XGB_PARAMS = dict(n_estimators=300, max_depth=6, learning_rate=0.1, subsample=0.8,
                  colsample_bytree=0.8, tree_method="hist", random_state=SEED, verbosity=0)


def channel_columns(channels):
    cols = []
    for c in channels:
        cols.extend(range((c - 1) * N_FPC, (c - 1) * N_FPC + N_FPC))
    return np.asarray(sorted(cols), dtype=np.int64)


def stratified_indices(y, n):
    if n is None or n >= len(y):
        return np.arange(len(y))
    sss = StratifiedShuffleSplit(n_splits=1, train_size=n, random_state=SEED)
    return next(sss.split(np.zeros((len(y), 1)), y))[0]


def evaluate(Xtr, ytr, Xte, yte, device, cols=None):
    a = Xtr if cols is None else Xtr[:, cols]
    b = Xte if cols is None else Xte[:, cols]
    mu = a.mean(axis=0)
    sd = a.std(axis=0) + 1e-8
    model = xgb.XGBClassifier(device=device, **XGB_PARAMS)
    model.fit((a - mu) / sd, ytr)
    yp = model.predict((b - mu) / sd)
    return {
        "macro_f1": f1_score(yte, yp, average="macro"),
        "balanced_accuracy": balanced_accuracy_score(yte, yp),
        "accuracy": accuracy_score(yte, yp),
        "weighted_f1": f1_score(yte, yp, average="weighted"),
    }


def complete_participants(full, rankings, scores, curve, lambdas, ks):
    if full.empty or rankings.empty or scores.empty or curve.empty:
        return set()
    out = set()
    for pid in sorted(full.participant_id.unique()):
        r = rankings[rankings.outer_participant == pid]
        s = scores[scores.outer_participant == pid]
        c = curve[curve.participant_id == pid]
        if (len(full[full.participant_id == pid]) >= 1
                and set(np.round(r["lambda"].astype(float), 8)) == set(lambdas)
                and len(s) == N_CHANNELS
                and len(c) == len(lambdas) * len(ks)
                and set(np.round(c["lambda"].astype(float), 8)) == set(lambdas)
                and set(c.channels_k.astype(int)) == set(ks)):
            out.add(int(pid))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--inner-folds", type=int, default=5)
    ap.add_argument("--max-attrib", type=int, default=20000)
    ap.add_argument("--max-train", type=int, default=200000)
    ap.add_argument("--train-subsample", type=int, default=CURVE_TRAIN_SUBSAMPLE)
    ap.add_argument("--k-workers", type=int, default=1,
                    help="parallel bipolar k fits within each lambda")
    ap.add_argument("--lambdas", default="0.0,0.25,0.5,1.0")
    ap.add_argument("--k-values", default="1,2,3,4,5,6,7,8")
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()

    if not FEATURES.exists():
        print(f"FATAL: {FEATURES} missing", flush=True)
        return 2
    lambdas = tuple(float(x) for x in args.lambdas.split(","))
    ks = [int(x) for x in args.k_values.split(",")]
    if any(k < 1 or k > N_CHANNELS for k in ks):
        print(f"FATAL: k must be in 1..{N_CHANNELS}", flush=True)
        return 2
    OUT.mkdir(parents=True, exist_ok=True)

    df = pd.read_parquet(FEATURES)
    df = df[df.gesture_id <= ACTIVE_GESTURES].copy()
    fcols = [c for c in df.columns if c not in META_COLS]
    assert_channel_major(fcols, N_CHANNELS, N_FPC)
    X = df[fcols].to_numpy(np.float32)
    y = (df.gesture_id.to_numpy() - 1).astype(np.int64)
    subj = df.participant_id.to_numpy()
    participants = sorted(np.unique(subj).tolist())
    print(f"bipolar active data: {X.shape[0]} windows, {X.shape[1]} features, "
          f"{len(participants)} participants", flush=True)

    full_path = OUT / "bipolar_full_channel_metrics.csv"
    rank_path = OUT / "bipolar_rankings.csv"
    score_path = OUT / "bipolar_scores.csv"
    curve_path = OUT / "bipolar_sparse_curve.csv"

    def read(path):
        return pd.read_csv(path) if path.exists() else pd.DataFrame()

    full = read(full_path)
    rankings = read(rank_path)
    scores = read(score_path)
    curve = read(curve_path)
    finished = complete_participants(full, rankings, scores, curve, lambdas, ks) if args.resume else set()
    if args.resume:
        print(f"resuming {len(finished)} complete bipolar participants", flush=True)
        full = full[full.participant_id.isin(finished)] if not full.empty else full
        rankings = rankings[rankings.outer_participant.isin(finished)] if not rankings.empty else rankings
        scores = scores[scores.outer_participant.isin(finished)] if not scores.empty else scores
        curve = curve[curve.participant_id.isin(finished)] if not curve.empty else curve

    t0 = time.time()
    for i, pid in enumerate(participants, 1):
        if int(pid) in finished:
            continue
        te = subj == pid
        tr = ~te
        Xtr = X[tr]
        Xte = X[te]
        ytr, yte = y[tr], y[te]
        gtr = subj[tr]

        # P1-equivalent full bipolar baseline: all outer-training windows.
        started = time.time()
        res = evaluate(Xtr, ytr, Xte, yte, args.device)
        full = pd.concat([full, pd.DataFrame([{
            "participant_id": int(pid), "model": "M_XGBoost", "channels_k": N_CHANNELS,
            "n_train_windows": int(len(ytr)), "n_test_windows": int(len(yte)),
            **res, "fit_seconds": round(time.time() - started, 2),
        }])], ignore_index=True)

        # Cross-fitted attribution is computed only from the outer-training participants.
        att = compute_cross_fitted_attribution(
            Xtr, ytr, gtr, fcols, n_channels=N_CHANNELS, n_features_per_channel=N_FPC,
            n_inner_folds=min(args.inner_folds, len(np.unique(gtr))),
            device=args.device, max_attrib_samples=args.max_attrib,
            max_train_samples=args.max_train, seed=SEED,
        )
        rank_add = [{"outer_participant": int(pid), "lambda": lam,
                     "ranking": ";".join(str(c + 1) for c in att.ranking(lam))}
                    for lam in lambdas]
        rankings = pd.concat([rankings, pd.DataFrame(rank_add)], ignore_index=True)
        A, U = att.central(), att.instability()
        score_add = [{"outer_participant": int(pid), "channel": c + 1,
                      "A_central": float(A[c]), "U_instability": float(U[c])}
                     for c in range(N_CHANNELS)]
        scores = pd.concat([scores, pd.DataFrame(score_add)], ignore_index=True)

        # P3-equivalent curve: one fixed outer-training subsample, then retrain from scratch at k.
        idx = stratified_indices(ytr, args.train_subsample)
        Xc, yc = Xtr[idx], ytr[idx]
        mu = Xc.mean(axis=0)
        sd = Xc.std(axis=0) + 1e-8
        Xc = (Xc - mu) / sd
        Xte_scaled = (Xte - mu) / sd
        # Different lambdas usually select the same subset at a given k. Each distinct subset is
        # fitted once per participant and shared: identical columns, data and seed give an
        # identical model, so this changes compute only, never a result.
        rank_by_lam = {lam: [c + 1 for c in att.ranking(lam)] for lam in lambdas}
        subsets = sorted({tuple(sorted(rank_by_lam[lam][:k])) for lam in lambdas for k in ks})

        def fit_subset(subset):
            cols = channel_columns(list(subset))
            start = time.time()
            model = xgb.XGBClassifier(device=args.device, **XGB_PARAMS)
            model.fit(Xc[:, cols], yc)
            yp = model.predict(Xte_scaled[:, cols])
            return subset, {
                "macro_f1": f1_score(yte, yp, average="macro"),
                "balanced_accuracy": balanced_accuracy_score(yte, yp),
                "accuracy": accuracy_score(yte, yp),
                "weighted_f1": f1_score(yte, yp, average="weighted"),
                "fit_seconds": round(time.time() - start, 2),
            }

        if args.k_workers > 1:
            with ThreadPoolExecutor(max_workers=args.k_workers) as tex:
                fitted = dict(tex.map(fit_subset, subsets))
        else:
            fitted = dict(fit_subset(sub) for sub in subsets)
        curve_add = []
        for lam in lambdas:
            ranking = rank_by_lam[lam]
            for k in ks:
                r = fitted[tuple(sorted(ranking[:k]))]
                curve_add.append({
                    "participant_id": int(pid), "model": "M_XGBoost", "lambda": lam,
                    "channels_k": int(k), "channels": ";".join(map(str, ranking[:k])),
                    "macro_f1": r["macro_f1"], "balanced_accuracy": r["balanced_accuracy"],
                    "accuracy": r["accuracy"], "weighted_f1": r["weighted_f1"],
                    "n_train_windows": int(len(yc)), "n_test_windows": int(len(yte)),
                    "fit_seconds": r["fit_seconds"], "distinct_subsets_fitted": len(subsets),
                })
        curve = pd.concat([curve, pd.DataFrame(curve_add)], ignore_index=True)

        full.sort_values(["participant_id"], inplace=True)
        rankings.sort_values(["outer_participant", "lambda"], inplace=True)
        scores.sort_values(["outer_participant", "channel"], inplace=True)
        curve.sort_values(["participant_id", "lambda", "channels_k"], inplace=True)
        full.to_csv(full_path, index=False)
        rankings.to_csv(rank_path, index=False)
        scores.to_csv(score_path, index=False)
        curve.to_csv(curve_path, index=False)
        el = time.time() - t0
        print(f"[{i}/{len(participants)}] participant {pid:02d} full={res['macro_f1']:.4f} "
              f"top4={rank_add[0]['ranking'].split(';')[:4]} elapsed={el/60:.1f}m",
              flush=True)

    summary = (curve.groupby(["model", "lambda", "channels_k"])
               .agg(n_participants=("participant_id", "nunique"),
                    mean_macro_f1=("macro_f1", "mean"), sd_macro_f1=("macro_f1", "std"),
                    mean_accuracy=("accuracy", "mean"))
               .reset_index())
    summary.to_csv(OUT / "bipolar_summary.csv", index=False)
    (OUT / "bipolar_provenance.json").write_text(json.dumps({
        "feature_file": str(FEATURES.relative_to(ROOT)).replace("\\", "/"),
        "active_gesture_filter": "gesture_id <= 16; gesture 17 (Rest) excluded",
        "n_participants": len(participants), "n_features": len(fcols),
        "n_channels": N_CHANNELS, "features_per_channel": N_FPC,
        "lambdas": list(lambdas), "k_values": ks,
        "full_train_windows": "all outer-training windows",
        "curve_train_subsample": args.train_subsample,
        "attribution_max_train": args.max_train,
        "attribution_max_samples": args.max_attrib,
        "device": args.device, "seed": SEED,
    }, indent=2), encoding="utf-8")

    if (full.participant_id.nunique() != len(participants)
            or rankings.outer_participant.nunique() != len(participants)
            or scores.outer_participant.nunique() != len(participants)
            or curve.participant_id.nunique() != len(participants)):
        print("ASSERTION FAILED: bipolar cohort is incomplete", flush=True)
        return 1
    print("\n" + summary.to_string(index=False), flush=True)
    print(f"\nASSERTION PASSED: {len(participants)} participants x {len(ks)} k x "
          f"{len(lambdas)} lambda; wall clock {(time.time()-t0)/60:.1f} min", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
