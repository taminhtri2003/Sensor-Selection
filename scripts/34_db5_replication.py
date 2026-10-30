"""External methodological replication on NinaPro DB5.

Runs the same conceptual pipeline as the GRABMyo arm — LOSO over subjects, cross-fitted
attribution inside outer-training data, sparse sensor curve, non-inferiority — on a dataset with
different hardware, a different sampling rate, a different movement set, and a different
quantisation.

What is being replicated is the METHOD, not the answer. Specifically NOT claimed:
  - that the same physical channels matter (the montages are unrelated: GRABMyo is 2 rings of 8
    monopolar forearm electrodes; DB5 is two Myo armbands)
  - that absolute performance is comparable (different class counts, 16 vs 12; different bandwidth,
    2048 Hz vs an aliasing 200 Hz; different units, mV vs 8-bit ADC codes)

What IS compared: whether the procedure behaves the same way — how concentrated the attribution is,
what fraction of channels can be dropped, and whether attribution beats a random subset.

Outputs:
  artifacts/db5/db5_full_channel_metrics.csv
  artifacts/db5/db5_rankings.csv
  artifacts/db5/db5_sparse_curve.csv
  artifacts/db5/db5_summary.csv
"""

import argparse
import importlib.metadata
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score
import xgboost as xgb

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.semg_sparse.xai.cross_fitted import compute_cross_fitted_attribution  # noqa: E402
from src.semg_sparse.checkpoints import atomic_csv, ensure_protocol, sha256  # noqa: E402

FEATURES = ROOT / "data" / "features" / "db5_features.parquet"
OUT = ROOT / "artifacts" / "db5"

SEED = 20260728
N_CHANNELS = 16
N_FPC = 10
LAMBDAS = (0.0, 0.25, 0.5, 1.0)
META_COLS = ["dataset", "participant_id", "session_id", "gesture_id", "trial_id", "window_idx"]
XGB_PARAMS = dict(n_estimators=300, max_depth=6, learning_rate=0.1, subsample=0.8,
                  colsample_bytree=0.8, tree_method="hist", random_state=SEED, verbosity=0)


def channel_columns(channels):
    cols = []
    for c in channels:
        cols.extend(range((c - 1) * N_FPC, (c - 1) * N_FPC + N_FPC))
    return np.array(sorted(cols), dtype=np.int64)


def fit_eval(Xtr, ytr, Xte, yte, device, cols=None):
    a = Xtr if cols is None else Xtr[:, cols]
    b = Xte if cols is None else Xte[:, cols]
    mu, sd = a.mean(axis=0), a.std(axis=0) + 1e-8
    m = xgb.XGBClassifier(device=device, **XGB_PARAMS)
    m.fit((a - mu) / sd, ytr)
    yp = m.predict((b - mu) / sd)
    return {
        "macro_f1": f1_score(yte, yp, average="macro"),
        "balanced_accuracy": balanced_accuracy_score(yte, yp),
        "accuracy": accuracy_score(yte, yp),
        "weighted_f1": f1_score(yte, yp, average="weighted"),
    }


def protocol_for(inner_folds, ks, device='cuda'):
    """Fingerprint semantic settings and source data before any DB5 checkpoint reuse."""
    return {
        'experiment': 'NinaPro DB5 E1', 'seed': SEED, 'inner_folds': inner_folds, 'device': device,
        'k_values': sorted(ks), 'lambdas': list(LAMBDAS), 'xgb_params': XGB_PARAMS,
        'features_sha256': sha256(FEATURES),
        'sources': {name: sha256(ROOT / name) for name in (
            'scripts/34_db5_replication.py', 'src/semg_sparse/checkpoints.py',
            'src/semg_sparse/xai/cross_fitted.py')},
        'versions': {name: importlib.metadata.version(name) for name in (
            'numpy', 'pandas', 'scikit-learn', 'xgboost')},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--inner-folds", type=int, default=5)
    ap.add_argument("--k-values", default="1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16")
    ap.add_argument("--resume", action="store_true",
                    help="reuse complete subject outputs in artifacts/db5")
    args = ap.parse_args()

    if not FEATURES.exists():
        print(f"FATAL: {FEATURES} missing — run scripts/33_db5_features.py first")
        return 2
    ks = [int(x) for x in args.k_values.split(",")]
    OUT.mkdir(parents=True, exist_ok=True)

    df = pd.read_parquet(FEATURES)
    fcols = [c for c in df.columns if c not in META_COLS]
    X = df[fcols].to_numpy(np.float32)
    # DB5 E1 movement ids are 1..12; map to 0..11
    y = (df.gesture_id.to_numpy() - 1).astype(np.int64)
    subj = df.participant_id.to_numpy()
    participants = sorted(np.unique(subj).tolist())
    print(f"DB5: {X.shape[0]} windows, {X.shape[1]} features, "
          f"{len(np.unique(y))} classes, {len(participants)} subjects", flush=True)

    full_path = OUT / "db5_full_channel_metrics.csv"
    rank_path = OUT / "db5_rankings.csv"
    curve_path = OUT / "db5_sparse_curve.csv"
    score_path = OUT / "db5_scores.csv"

    if args.resume and any(p.exists() for p in (full_path, rank_path, curve_path, score_path)):
        if not curve_path.with_suffix('.protocol.json').exists():
            raise ValueError('DB5 checkpoints have no protocol fingerprint; use a new output directory')
    ensure_protocol(curve_path, protocol_for(args.inner_folds, ks, device=args.device), args.resume)

    def read(path):
        return pd.read_csv(path) if path.exists() else pd.DataFrame()

    full_df = read(full_path)
    rank_df = read(rank_path)
    curve_df = read(curve_path)
    score_df = read(score_path)
    finished = set()
    if args.resume:
        for pid in participants:
            if any(frame.empty for frame in (full_df, rank_df, curve_df, score_df)):
                break
            f = full_df[full_df.participant_id == pid]
            r = rank_df[rank_df.outer_participant == pid]
            c = curve_df[curve_df.participant_id == pid]
            s = score_df[score_df.outer_participant == pid]
            if (len(f) == 1 and len(r) == len(LAMBDAS)
                    and set(np.round(r["lambda"].astype(float), 8)) == set(LAMBDAS)
                    and len(c) == len(ks) and set(c.channels_k.astype(int)) == set(ks)
                    and not c.duplicated(['participant_id', 'channels_k']).any()
                    and len(s) == N_CHANNELS and set(s.channel) == set(range(1, N_CHANNELS + 1))
                    and np.isfinite(f[['macro_f1', 'accuracy', 'balanced_accuracy', 'weighted_f1']]).all().all()
                    and np.isfinite(c[['macro_f1', 'accuracy', 'balanced_accuracy', 'weighted_f1']]).all().all()):
                finished.add(int(pid))
        print(f"resuming {len(finished)} complete DB5 subjects", flush=True)
        full_df = full_df[full_df.participant_id.isin(finished)] if not full_df.empty else full_df
        rank_df = rank_df[rank_df.outer_participant.isin(finished)] if not rank_df.empty else rank_df
        curve_df = curve_df[curve_df.participant_id.isin(finished)] if not curve_df.empty else curve_df
        score_df = score_df[score_df.outer_participant.isin(finished)] if not score_df.empty else score_df

    full_rows = full_df.to_dict("records")
    rank_rows = rank_df.to_dict("records")
    curve_rows = curve_df.to_dict("records")
    score_rows = score_df.to_dict("records")
    t0 = time.time()

    for i, pid in enumerate(participants, 1):
        if int(pid) in finished:
            continue
        te = subj == pid
        tr = ~te
        Xtr, Xte = X[tr], X[te]
        ytr, yte = y[tr], y[te]
        gtr = subj[tr]

        # --- full channel baseline -------------------------------------------------------------
        res = fit_eval(Xtr, ytr, Xte, yte, args.device)
        full_rows.append({"participant_id": int(pid), "model": "M_XGBoost", "channels_k": 16,
                          "n_train_windows": int(len(ytr)), "n_test_windows": int(len(yte)),
                          **res})

        # --- cross-fitted ranking from outer-training subjects only ---------------------------
        att = compute_cross_fitted_attribution(
            Xtr, ytr, gtr, fcols, n_channels=N_CHANNELS, n_features_per_channel=N_FPC,
            n_inner_folds=min(args.inner_folds, len(np.unique(gtr))),
            device=args.device, max_attrib_samples=20000, seed=SEED,
        )
        for lam in LAMBDAS:
            rank_rows.append({"outer_participant": int(pid), "lambda": lam,
                              "ranking": ";".join(str(c + 1) for c in att.ranking(lam))})
        A, U = att.central(), att.instability()
        score_rows.extend({"outer_participant": int(pid), "channel": c + 1,
                           "A_central": float(A[c]), "U_instability": float(U[c])}
                          for c in range(N_CHANNELS))

        # --- sparse curve on the lambda=0 ranking ---------------------------------------------
        ranking = [c + 1 for c in att.ranking(0.0)]
        for k in ks:
            cols = channel_columns(ranking[:k])
            r = fit_eval(Xtr, ytr, Xte, yte, args.device, cols=cols)
            curve_rows.append({"participant_id": int(pid), "model": "M_XGBoost", "lambda": 0.0,
                               "channels_k": int(k),
                               "channels": ";".join(map(str, ranking[:k])), **r})

        atomic_csv(pd.DataFrame(full_rows), full_path)
        atomic_csv(pd.DataFrame(rank_rows), rank_path)
        atomic_csv(pd.DataFrame(score_rows), score_path)
        atomic_csv(pd.DataFrame(curve_rows), curve_path)
        el = time.time() - t0
        print(f"[{i}/{len(participants)}] subject {pid} full={res['macro_f1']:.4f} "
              f"top4={ranking[:4]} elapsed={el/60:.1f}m", flush=True)

    atomic_csv(pd.DataFrame(rank_rows), rank_path)
    atomic_csv(pd.DataFrame(score_rows), score_path)

    full = pd.DataFrame(full_rows)
    curve = pd.DataFrame(curve_rows)
    summary = (curve.groupby("channels_k")
               .agg(n_subjects=("participant_id", "nunique"),
                    mean_macro_f1=("macro_f1", "mean"), sd=("macro_f1", "std"))
               .reset_index())
    summary.to_csv(OUT / "db5_summary.csv", index=False)

    print(f"\nfull-channel Macro-F1: {full.macro_f1.mean():.4f} "
          f"(sd {full.macro_f1.std():.4f}, n={len(full)})", flush=True)
    print("\nsparse curve:", flush=True)
    print(summary.to_string(index=False), flush=True)

    if full.participant_id.nunique() != len(participants):
        print("ASSERTION FAILED: not every subject covered")
        return 1
    print(f"\nASSERTION PASSED: {len(participants)} subjects x {len(ks)} k values")
    print(f"wall clock: {(time.time()-t0)/60:.1f} min")
    return 0


if __name__ == "__main__":
    sys.exit(main())
