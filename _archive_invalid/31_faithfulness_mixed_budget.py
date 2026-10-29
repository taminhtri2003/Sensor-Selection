"""XAI faithfulness: does removing the channels the attribution called important actually hurt?

A ranking can look convincing and mean nothing. The test is behavioural: delete channels in
ranked order and see whether performance follows. Faithful attribution requires

    P(remove top-ranked first) < P(remove at random) < P(remove bottom-ranked first)

Reusing prior phases instead of recomputing them:

  bottom-removal  Removing the m least important channels leaves the top (16-m). That is exactly
                  the sparse curve from P3 at k = 16-m, so this arm is READ from P3 rather than
                  refitted -- and it must be, since refitting would risk a subtly different
                  protocol producing an inconsistent curve.
  random-removal  Read from P4's random subsets where a matching k exists; recomputed only for
                  the k values P4 did not cover.
  top-removal     The genuinely new arm: keep the (16-m) LEAST important channels. Computed here.

Outputs:
  artifacts/faithfulness/deletion_curves.csv
  artifacts/faithfulness/faithfulness_summary.csv
"""

import argparse
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score
from sklearn.model_selection import StratifiedShuffleSplit
import xgboost as xgb

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "data" / "cache"
RANKINGS = ROOT / "artifacts" / "rankings" / "cross_fitted_rankings.csv"
SPARSE = ROOT / "artifacts" / "metrics"
RANDOM_RAW = ROOT / "artifacts" / "selection_baselines" / "random_subsets_raw.csv"
OUT = ROOT / "artifacts" / "faithfulness"

SEED = 20260728
N_CHANNELS = 16
N_FPC = 10
# Matches the P4 comparison configuration so the three arms are mutually comparable.
CMP_XGB = dict(n_estimators=150, max_depth=6, learning_rate=0.1, subsample=0.8,
               colsample_bytree=0.8, tree_method="hist", random_state=SEED, verbosity=0)
CMP_TRAIN_SUBSAMPLE = 150000


def channel_columns(channels):
    cols = []
    for c in channels:
        cols.extend(range((c - 1) * N_FPC, (c - 1) * N_FPC + N_FPC))
    return np.array(sorted(cols), dtype=np.int64)


def fit_eval(Xtr, ytr, Xte, yte, channels, device):
    cols = channel_columns(channels)
    a, b = Xtr[:, cols], Xte[:, cols]
    mu, sd = a.mean(axis=0), a.std(axis=0) + 1e-8
    m = xgb.XGBClassifier(device=device, **CMP_XGB)
    m.fit((a - mu) / sd, ytr)
    return float(f1_score(yte, m.predict((b - mu) / sd), average="macro"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--srcfa-lambda", type=float, default=0.0)
    ap.add_argument("--keep-sizes", default="2,4,6,8,10,12,14",
                    help="number of channels retained after deletion")
    ap.add_argument("--fit-workers", type=int, default=1,
                    help="parallel top-removal fits within one participant")
    ap.add_argument("--resume", action="store_true",
                    help="reuse complete participant deletion curves")
    args = ap.parse_args()

    if not RANKINGS.exists():
        print(f"FATAL: {RANKINGS} missing — run scripts/25 first")
        return 2
    keeps = [int(x) for x in args.keep_sizes.split(",")]
    OUT.mkdir(parents=True, exist_ok=True)

    rank_df = pd.read_csv(RANKINGS)
    X = np.load(CACHE / "loso_X.npy", mmap_mode="r")
    y = np.asarray(np.load(CACHE / "loso_y.npy", mmap_mode="r"))
    subj = np.asarray(np.load(CACHE / "loso_subj.npy", mmap_mode="r"))
    participants = sorted(np.unique(subj).tolist())

    # Existing arms, read rather than refitted
    sparse_path = SPARSE / "sparse_curve_subject_metrics.csv"
    sparse = pd.read_csv(sparse_path) if sparse_path.exists() else pd.DataFrame()
    rand = pd.read_csv(RANDOM_RAW) if RANDOM_RAW.exists() else pd.DataFrame()
    print(f"reusing: sparse curve rows={len(sparse)}, random subset rows={len(rand)}", flush=True)

    rows = []
    completed = set()
    result_path = OUT / "deletion_curves.csv"
    if args.resume and result_path.exists():
        previous = pd.read_csv(result_path)
        for pid, g in previous.groupby("participant_id"):
            top = g[g.arm == "remove_top"]
            bottom = g[g.arm == "remove_bottom"]
            if set(top.n_kept.astype(int)) == set(keeps) and set(bottom.n_kept.astype(int)) == set(keeps):
                completed.add(int(pid))
        rows = [r for r in previous.to_dict("records")
                if int(r["participant_id"]) in completed]
        print(f"resuming {len(completed)} complete faithfulness participants", flush=True)
    t0 = time.time()
    for i, pid in enumerate(participants, 1):
        if int(pid) in completed:
            continue
        sel = rank_df[(rank_df.outer_participant == pid) &
                      (np.isclose(rank_df["lambda"], args.srcfa_lambda))]
        if sel.empty:
            print(f"FATAL: no ranking for participant {pid}")
            return 2
        ranking = [int(c) for c in sel.iloc[0]["ranking"].split(";")]

        te = subj == pid
        tr = ~te
        Xtr_full = np.asarray(X[tr], dtype=np.float32)
        Xte = np.asarray(X[te], dtype=np.float32)
        ytr, yte = y[tr], y[te]
        if CMP_TRAIN_SUBSAMPLE < len(ytr):
            sss = StratifiedShuffleSplit(n_splits=1, train_size=CMP_TRAIN_SUBSAMPLE,
                                         random_state=SEED)
            idx, _ = next(sss.split(Xtr_full, ytr))
            Xtr_full, ytr = Xtr_full[idx], ytr[idx]

        def fit_top(keep):
            # TOP-REMOVAL: the important channels are deleted, the least important are retained
            kept = ranking[-keep:]
            f1_top = fit_eval(Xtr_full, ytr, Xte, yte, kept, args.device)
            return {"participant_id": int(pid), "arm": "remove_top", "n_kept": keep,
                    "n_removed": N_CHANNELS - keep,
                    "channels": ";".join(map(str, kept)),
                    "macro_f1": f1_top, "source": "computed"}

        if args.fit_workers > 1:
            with ThreadPoolExecutor(max_workers=args.fit_workers) as tex:
                top_rows = list(tex.map(fit_top, keeps))
        else:
            top_rows = [fit_top(keep) for keep in keeps]
        rows.extend(top_rows)

        for keep in keeps:

            # BOTTOM-REMOVAL: identical to keeping the top-k, read from P3
            if not sparse.empty:
                s = sparse[(sparse.participant_id == pid) & (sparse.channels_k == keep) &
                           (np.isclose(sparse["lambda"], args.srcfa_lambda))]
                if not s.empty:
                    rows.append({"participant_id": int(pid), "arm": "remove_bottom",
                                 "n_kept": keep, "n_removed": N_CHANNELS - keep,
                                 "channels": s.iloc[0]["channels"],
                                 "macro_f1": float(s.iloc[0]["macro_f1"]),
                                 "source": "reused_from_sparse_curve"})

            # RANDOM-REMOVAL: read from P4 if that k was covered
            if not rand.empty:
                r = rand[(rand.participant_id == pid) & (rand.channels_k == keep)]
                if not r.empty:
                    rows.append({"participant_id": int(pid), "arm": "remove_random",
                                 "n_kept": keep, "n_removed": N_CHANNELS - keep,
                                 "channels": f"{len(r)} draws",
                                 "macro_f1": float(r.macro_f1.mean()),
                                 "source": "reused_from_random_baseline"})

        pd.DataFrame(rows).to_csv(result_path, index=False)
        el = time.time() - t0
        print(f"[{i}/{len(participants)}] participant {pid:02d} "
              f"elapsed={el/60:.1f}m eta={el/i*(len(participants)-i)/60:.1f}m", flush=True)

    df = pd.DataFrame(rows)
    summary = (df.groupby(["arm", "n_kept"])
               .agg(n_participants=("participant_id", "nunique"),
                    mean_macro_f1=("macro_f1", "mean"), sd=("macro_f1", "std"))
               .reset_index().sort_values(["n_kept", "mean_macro_f1"]))
    summary.to_csv(OUT / "faithfulness_summary.csv", index=False)
    print("\n" + summary.to_string(index=False), flush=True)

    # Faithfulness verdict per retained size
    print("\nfaithfulness check (expected: remove_top < remove_random < remove_bottom)", flush=True)
    piv = summary.pivot(index="n_kept", columns="arm", values="mean_macro_f1")
    for k, r in piv.iterrows():
        have = [a for a in ("remove_top", "remove_random", "remove_bottom") if a in r
                and pd.notna(r.get(a))]
        if len(have) < 2:
            print(f"  n_kept={k}: insufficient arms ({have})", flush=True)
            continue
        ordered = all(r[have[i]] <= r[have[i + 1]] for i in range(len(have) - 1))
        vals = ", ".join(f"{a}={r[a]:.4f}" for a in have)
        print(f"  n_kept={k}: {vals}  -> {'FAITHFUL' if ordered else 'ORDER VIOLATED'}",
              flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
