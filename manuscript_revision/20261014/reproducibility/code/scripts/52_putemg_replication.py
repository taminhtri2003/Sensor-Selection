"""putEMG exploratory replication (design fixed in reports/decision_log.md, Decision 19).

LOSO over 44 participants. For each held-out participant p, using outer-training participants only:
z-scoring, XGBoost fitting (stratified 200k cap, same as the GRABMyo curve), cross-fitted TreeSHAP
over 5 participant-disjoint inner folds, ranking Q_c(lambda); then the lambda = 0 sparse curve for
k = 1..24 and 10 random k-subsets at k in {6, 12, 18}. The k = 24 point of the curve uses all
channel columns in the same order and seed as the full model, so it IS the full-array model.

Outputs (artifacts/putemg/): full_channel.csv, rankings.csv, scores.csv, sparse_curve.csv,
random_subsets.csv. Resumable per participant (--resume).
"""
import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score
from sklearn.model_selection import StratifiedShuffleSplit

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src.semg_sparse.xai.cross_fitted import compute_cross_fitted_attribution  # noqa: E402

FEATURES = ROOT / "data/features/putemg_features.parquet"
OUT = ROOT / "artifacts/putemg"
SEED = 20260728
N_CH, N_FPC = 24, 10
LAMBDAS = (0.0, 0.25, 0.5, 1.0)
KS = tuple(range(1, 25))
RANDOM_KS, N_RANDOM = (6, 12, 18), 10
TRAIN_CAP = 200000
META = ["dataset", "participant_id", "session_id", "gesture_id", "trial_id", "window_idx"]
XGB_PARAMS = dict(n_estimators=300, max_depth=6, learning_rate=0.1, subsample=0.8,
                  colsample_bytree=0.8, tree_method="hist", random_state=SEED, verbosity=0)


def cols_of(channels):
    return np.array(sorted(c0 for c in channels for c0 in range((c - 1) * N_FPC, c * N_FPC)))


def fit_eval(Xtr, ytr, Xte, yte, device, cols):
    a, b = Xtr[:, cols], Xte[:, cols]
    mu, sd = a.mean(0), a.std(0) + 1e-8
    m = xgb.XGBClassifier(device=device, **XGB_PARAMS)
    m.fit((a - mu) / sd, ytr)
    yp = m.predict((b - mu) / sd)
    return {"macro_f1": f1_score(yte, yp, average="macro"),
            "balanced_accuracy": balanced_accuracy_score(yte, yp),
            "accuracy": accuracy_score(yte, yp)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--only", default="", help="comma list of participants (timing runs)")
    ap.add_argument("--shard", default="", help="i/n: run participants[i::n], write *_shard{i}.csv "
                    "(compute-only parallelism; merge with --merge)")
    ap.add_argument("--merge", type=int, default=0, help="merge n shard files and exit")
    args = ap.parse_args()

    names = ["full_channel", "rankings", "scores", "sparse_curve", "random_subsets"]
    if args.merge:
        for n in names:
            parts_ = [pd.read_csv(OUT / f"{n}_shard{i}.csv") for i in range(args.merge)]
            pd.concat(parts_, ignore_index=True).to_csv(OUT / f"{n}.csv", index=False)
        print("merged", args.merge, "shards")
        return 0
    df = pd.read_parquet(FEATURES)
    fcols = [c for c in df.columns if c not in META]
    assert len(fcols) == N_CH * N_FPC
    X = df[fcols].to_numpy(np.float32)
    classes = sorted(df.gesture_id.unique())
    y = df.gesture_id.map({g: i for i, g in enumerate(classes)}).to_numpy(np.int64)
    subj = df.participant_id.to_numpy()
    parts = sorted(np.unique(subj).tolist())
    if args.only:
        parts = [int(v) for v in args.only.split(",")]
    suffix = ""
    if args.shard:
        i_, n_ = (int(v) for v in args.shard.split("/"))
        parts = parts[i_::n_]
        suffix = f"_shard{i_}"
    print(f"putEMG: {len(X)} windows, {len(fcols)} features, classes {classes}, "
          f"{len(np.unique(subj))} participants", flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    paths = {n: OUT / f"{n}{suffix}.csv" for n in names}
    tabs = {n: (pd.read_csv(p).to_dict("records") if (args.resume and p.exists()) else [])
            for n, p in paths.items()}
    done = {r["participant_id"] for r in tabs["random_subsets"]} if args.resume else set()
    # a participant is complete only if its last-written table has all rows
    if done:
        rs = pd.DataFrame(tabs["random_subsets"])
        done = {p for p in done if (rs.participant_id == p).sum() == len(RANDOM_KS) * N_RANDOM}
        for n in names:
            key = "outer_participant" if n in ("rankings", "scores") else "participant_id"
            tabs[n] = [r for r in tabs[n] if r[key] in done]
    print(f"resuming {len(done)} complete participants", flush=True)
    t0 = time.time()

    for i, pid in enumerate(parts, 1):
        if pid in done:
            continue
        te = subj == pid
        tr_all = np.flatnonzero(~te)
        if len(tr_all) > TRAIN_CAP:
            sss = StratifiedShuffleSplit(n_splits=1, train_size=TRAIN_CAP, random_state=SEED)
            tr = tr_all[next(sss.split(tr_all, y[tr_all]))[0]]
        else:
            tr = tr_all
        Xtr, ytr, gtr = X[tr], y[tr], subj[tr]
        Xte, yte = X[te], y[te]
        base = {"participant_id": pid, "n_train_windows": len(tr), "n_test_windows": int(te.sum())}

        att = compute_cross_fitted_attribution(
            Xtr, ytr, gtr, fcols, n_channels=N_CH, n_features_per_channel=N_FPC,
            n_inner_folds=5, device=args.device, max_attrib_samples=20000, seed=SEED)
        A, U = att.central(), att.instability()
        tabs["scores"] += [{"outer_participant": pid, "channel": c + 1, "A_central": float(A[c]),
                            "U_instability": float(U[c])} for c in range(N_CH)]
        for lam in LAMBDAS:
            tabs["rankings"].append({"outer_participant": pid, "lambda": lam,
                                     "ranking": ";".join(str(c + 1) for c in att.ranking(lam))})
        ranking = [c + 1 for c in att.ranking(0.0)]
        for k in KS:
            r = fit_eval(Xtr, ytr, Xte, yte, args.device, cols_of(ranking[:k]))
            tabs["sparse_curve"].append({**base, "lambda": 0.0, "channels_k": k,
                                         "channels": ";".join(map(str, ranking[:k])), **r})
            if k == N_CH:
                tabs["full_channel"].append({**base, "model": "M_XGBoost", "channels_k": N_CH, **r})
        rng = np.random.default_rng(SEED + pid)
        for k in RANDOM_KS:
            for d in range(N_RANDOM):
                ch = sorted((rng.choice(N_CH, size=k, replace=False) + 1).tolist())
                r = fit_eval(Xtr, ytr, Xte, yte, args.device, cols_of(ch))
                tabs["random_subsets"].append({**base, "channels_k": k, "draw": d,
                                               "channels": ";".join(map(str, ch)), **r})
        for n, p in paths.items():
            pd.DataFrame(tabs[n]).to_csv(p, index=False)
        f24 = tabs["full_channel"][-1]["macro_f1"]
        print(f"[{i}/{len(parts)}] p{pid} n_train={len(tr)} full={f24:.4f} top6={ranking[:6]} "
              f"elapsed={(time.time()-t0)/60:.1f}m", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
