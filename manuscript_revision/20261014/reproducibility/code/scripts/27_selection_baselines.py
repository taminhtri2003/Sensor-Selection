"""Selection baselines: does attribution-guided channel selection beat the alternatives?

This is the phase that can sink the headline. If random subsets of the same size match SR-CFA,
the explainability framing has no engineering value and the paper becomes a negative result. The
comparison is therefore built to be fair rather than flattering:

  - every selection method is evaluated with an IDENTICAL model configuration and identical
    training budget, so differences come from the channel subset and nothing else;
  - all methods are computed per outer fold from outer-training data only, exactly as SR-CFA is;
  - the geometric baseline is an algorithmic farthest-point selection over the real 2x8 electrode
    montage, never a hand-picked set that happens to look good.

Methods compared at matched k:
  SRCFA_lam*   stability-regularised attribution   (from P2)
  SHAP_lam0    attribution magnitude only          (from P2; the ablation for gate G2)
  PERM         permutation importance
  MI           mutual information
  RANDOM       random subsets (distribution, not just its mean)
  GEOM         equispaced/farthest-point over the montage

Outputs:
  artifacts/selection_baselines/selection_baseline_metrics.csv
  artifacts/selection_baselines/random_subsets_raw.csv
  artifacts/selection_baselines/compute_budget.json   what was run and what was capped
"""

import argparse
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_selection import mutual_info_classif
from sklearn.inspection import permutation_importance
from sklearn.metrics import f1_score
from sklearn.model_selection import StratifiedShuffleSplit
import xgboost as xgb

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "data" / "cache"
RANKINGS = ROOT / "artifacts" / "rankings" / "cross_fitted_rankings.csv"
OUT = ROOT / "artifacts" / "selection_baselines"

SEED = 20260728
N_CHANNELS = 16
N_FPC = 10

# Shared comparison configuration. Deliberately lighter than the headline model: the question here
# is the *relative* merit of channel subsets, and a lighter model lets the random baseline be
# sampled densely enough to characterise its distribution. Applied identically to every method, so
# no method is advantaged. The absolute numbers are therefore not comparable to the P1/P3 headline
# figures and must never be quoted as such.
# This is an exploratory relative-comparison model, deliberately lighter than the P1/P3
# headline model.  The frozen plan fixes the random-subset counts, not this compute-only model
# configuration; the 50-tree setting is recorded in compute_budget.json and the decision log.
CMP_XGB = dict(n_estimators=50, max_depth=6, learning_rate=0.1, subsample=0.8,
               colsample_bytree=0.8, tree_method="hist", random_state=SEED, verbosity=0)
CMP_TRAIN_SUBSAMPLE = 150000

# Electrode montage: F1..F8 = ring 1, F9..F16 = ring 2, 8 circumferential positions, rings 2 cm
# apart (Electrodelocation.pdf). Used only by the geometric baseline.
RING_SEP_CM = 2.0
CIRCUMFERENCE_CM = 24.0


def montage_coords():
    """(x, y) per channel: x = arc position around the forearm, y = longitudinal ring position."""
    coords = np.zeros((N_CHANNELS, 2))
    for ch in range(N_CHANNELS):
        circ_idx = ch % 8
        ring = ch // 8
        coords[ch, 0] = circ_idx * (CIRCUMFERENCE_CM / 8.0)
        coords[ch, 1] = ring * RING_SEP_CM
    return coords


def circular_distance(a, b):
    dx = abs(a[0] - b[0])
    dx = min(dx, CIRCUMFERENCE_CM - dx)      # the array wraps around the forearm
    return float(np.hypot(dx, a[1] - b[1]))


def geometric_selection(k, seed=SEED):
    """Farthest-point sampling over the montage: algorithmic, deterministic, not hand-chosen."""
    coords = montage_coords()
    chosen = [0]                              # deterministic start; ranking is by spread thereafter
    while len(chosen) < k:
        best, best_d = None, -1.0
        for c in range(N_CHANNELS):
            if c in chosen:
                continue
            d = min(circular_distance(coords[c], coords[s]) for s in chosen)
            if d > best_d:
                best, best_d = c, d
        chosen.append(best)
    return [c + 1 for c in chosen[:k]]


def channel_columns(channels_1based):
    cols = []
    for c in channels_1based:
        cols.extend(range((c - 1) * N_FPC, (c - 1) * N_FPC + N_FPC))
    return np.array(sorted(cols), dtype=np.int64)


def subsample_idx(y, n, seed=SEED):
    if n is None or n >= len(y):
        return np.arange(len(y))
    sss = StratifiedShuffleSplit(n_splits=1, train_size=n, random_state=seed)
    return next(sss.split(np.zeros((len(y), 1)), y))[0]


def fit_eval(Xtr, ytr, Xte, yte, channels, device, already_scaled=False):
    cols = channel_columns(channels)
    a, b = Xtr[:, cols], Xte[:, cols]
    if not already_scaled:
        mu, sd = a.mean(axis=0), a.std(axis=0) + 1e-8
        a, b = (a - mu) / sd, (b - mu) / sd
    m = xgb.XGBClassifier(device=device, **CMP_XGB)
    m.fit(a, ytr)
    return f1_score(yte, m.predict(b), average="macro")


def derive_perm_and_mi(Xtr, ytr, device, seed=SEED):
    """Permutation importance and mutual information, computed on outer-training data only."""
    # Both are computed on a further subsample purely for tractability; this affects all
    # non-attribution baselines equally and is recorded in the budget file.
    idx = subsample_idx(ytr, 40000, seed)
    Xs, ys = Xtr[idx], ytr[idx]
    mu, sd = Xs.mean(axis=0), Xs.std(axis=0) + 1e-8
    Xs = (Xs - mu) / sd

    inner = subsample_idx(ys, 20000, seed)
    m = xgb.XGBClassifier(device=device, **CMP_XGB)
    m.fit(Xs[inner], ys[inner])
    hold = np.setdiff1d(np.arange(len(ys)), inner)[:8000]
    pi = permutation_importance(m, Xs[hold], ys[hold], n_repeats=3,
                                random_state=seed, scoring="f1_macro", n_jobs=1)
    perm_ch = pi.importances_mean.reshape(N_CHANNELS, N_FPC).mean(axis=1)

    mi = mutual_info_classif(Xs[inner], ys[inner], random_state=seed)
    mi_ch = mi.reshape(N_CHANNELS, N_FPC).mean(axis=1)

    order = lambda v: [int(c) + 1 for c in np.lexsort((np.arange(N_CHANNELS), -v))]
    return order(perm_ch), order(mi_ch)


def run_fold(job):
    (pid, paths, ks, srcfa_rank, shap_rank, n_random_by_k, device, seed, fit_workers) = job
    xp, yp, sp = paths
    X = np.load(xp, mmap_mode="r")
    y = np.load(yp, mmap_mode="r")
    subj = np.load(sp, mmap_mode="r")

    te = np.asarray(subj) == pid
    tr = ~te
    Xtr = np.asarray(X[tr], dtype=np.float32)
    Xte = np.asarray(X[te], dtype=np.float32)
    ytr, yte = np.asarray(y[tr]), np.asarray(y[te])

    keep = subsample_idx(ytr, CMP_TRAIN_SUBSAMPLE, seed)
    Xtr, ytr = Xtr[keep], ytr[keep]

    perm_rank, mi_rank = derive_perm_and_mi(Xtr, ytr, device, seed)
    # Scaling is per feature, so computing it once across all 160 features is exactly equivalent
    # to scaling each selected subset independently.  It avoids repeating the same transform for
    # every fixed/random subset while keeping statistics strictly outer-training-only.
    mu = Xtr.mean(axis=0)
    sd = Xtr.std(axis=0) + 1e-8
    Xtr_scaled = (Xtr - mu) / sd
    Xte_scaled = (Xte - mu) / sd
    rng = np.random.default_rng(seed + int(pid))

    rows, raw = [], []
    for k in ks:
        n_random = int(n_random_by_k[int(k)])
        fixed = {
            "SRCFA": srcfa_rank[:k],
            "SHAP_lam0": shap_rank[:k],
            "PERM": perm_rank[:k],
            "MI": mi_rank[:k],
            "GEOM": geometric_selection(k),
        }
        tasks = [("fixed", name, chans, None) for name, chans in fixed.items()]
        random_tasks = []
        for r in range(n_random):
            chans = sorted(rng.choice(np.arange(1, N_CHANNELS + 1), size=k, replace=False).tolist())
            random_tasks.append(("random", "RANDOM", chans, r))
        tasks.extend(random_tasks)

        def evaluate(task):
            kind, name, chans, draw = task
            t = time.time()
            f1 = fit_eval(Xtr_scaled, ytr, Xte_scaled, yte, chans, device,
                          already_scaled=True)
            return kind, name, chans, draw, f1, round(time.time() - t, 2)

        if fit_workers > 1 and len(tasks) > 1:
            with ThreadPoolExecutor(max_workers=fit_workers) as tex:
                evaluated = list(tex.map(evaluate, tasks))
        else:
            evaluated = [evaluate(task) for task in tasks]

        fixed_results = {}
        random_results = []
        for kind, name, chans, draw, f1, fit_seconds in evaluated:
            if kind == "fixed":
                fixed_results[name] = f1
                rows.append({"participant_id": int(pid), "method": name, "channels_k": int(k),
                             "channels": ";".join(map(str, chans)), "macro_f1": f1,
                             "fit_seconds": fit_seconds})
            else:
                random_results.append((int(draw), chans, f1))
                raw.append({"participant_id": int(pid), "channels_k": int(k), "draw": int(draw),
                            "channels": ";".join(map(str, chans)), "macro_f1": f1})

        random_results.sort(key=lambda x: x[0])
        scores = [x[2] for x in random_results]
        if scores:
            s = np.array(scores)
            srcfa_f1 = fixed_results["SRCFA"]
            rows.append({
                "participant_id": int(pid), "method": "RANDOM", "channels_k": int(k),
                "channels": f"{n_random} draws", "macro_f1": float(s.mean()),
                "random_sd": float(s.std()), "random_min": float(s.min()),
                "random_max": float(s.max()),
                # Where SR-CFA sits inside the random distribution. Near 0.5 means the attribution
                # ranking is no better than picking channels at random -- decision gate G3.
                "srcfa_percentile": float((s < srcfa_f1).mean()),
                "fit_seconds": np.nan})
    return rows, raw


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--k-values", default="4,6,8")
    ap.add_argument("--n-random", type=int, default=100)
    ap.add_argument("--n-random-at-k-star", type=int, default=500)
    ap.add_argument("--k-star", type=int, default=0,
                    help="prespecified k* from P5; receives the larger random draw count")
    ap.add_argument("--srcfa-lambda", type=float, default=0.5)
    ap.add_argument("--fit-workers", type=int, default=1,
                    help="parallel XGBoost subset fits within one participant fold")
    ap.add_argument("--resume", action="store_true",
                    help="reuse complete participant folds in existing baseline outputs")
    args = ap.parse_args()

    if not RANKINGS.exists():
        print(f"FATAL: {RANKINGS} missing — run scripts/25_cross_fitted_ranking.py first")
        return 2

    ks = [int(x) for x in args.k_values.split(",")]
    if args.k_star and args.k_star not in ks:
        print(f"FATAL: --k-star {args.k_star} is not in --k-values {ks}", flush=True)
        return 2
    n_random_by_k = {
        int(k): (args.n_random_at_k_star if args.k_star and int(k) == args.k_star
                 else args.n_random)
        for k in ks
    }
    OUT.mkdir(parents=True, exist_ok=True)
    rank_df = pd.read_csv(RANKINGS)

    xp, yp, sp = CACHE / "loso_X.npy", CACHE / "loso_y.npy", CACHE / "loso_subj.npy"
    subj = np.load(sp, mmap_mode="r")
    participants = sorted(np.unique(np.asarray(subj)).tolist())

    def ranking_for(pid, lam):
        sel = rank_df[(rank_df.outer_participant == pid) & (np.isclose(rank_df["lambda"], lam))]
        if sel.empty:
            raise SystemExit(f"FATAL: no ranking for participant {pid} lambda {lam}")
        return [int(c) for c in sel.iloc[0]["ranking"].split(";")]

    jobs = [(pid, (str(xp), str(yp), str(sp)), ks,
             ranking_for(pid, args.srcfa_lambda), ranking_for(pid, 0.0),
             n_random_by_k, args.device, SEED, args.fit_workers) for pid in participants]

    budget = {
        "k_values": ks, "n_random_per_k": args.n_random,
        "frozen_plan_requested": {"n_subsets_per_k": 100, "n_subsets_at_k_star": 500},
        "actually_run": {"n_subsets_by_k": n_random_by_k,
                          "n_subsets_per_k": args.n_random,
                          "n_subsets_at_k_star": (n_random_by_k.get(args.k_star)
                                                    if args.k_star else None)},
        "capped": (args.n_random < 100
                    or (args.k_star and args.n_random_at_k_star < 500)),
        "cap_reason": ("No cap; frozen random-subset counts were used."
                       if not (args.n_random < 100
                               or (args.k_star and args.n_random_at_k_star < 500)) else
                       "Random baseline counts were reduced from the frozen plan for compute; "
                       "this deviation must be reported."),
        "comparison_model": CMP_XGB, "comparison_train_subsample": CMP_TRAIN_SUBSAMPLE,
        "note": ("All methods share this configuration, so the comparison is fair, but absolute "
                 "values are NOT comparable to the P1/P3 headline numbers."),
    }
    (OUT / "compute_budget.json").write_text(json.dumps(budget, indent=2))
    print(json.dumps(budget["actually_run"]), flush=True)
    if budget["capped"]:
        print("NOTE: random-subset coverage is below at least one frozen-plan count", flush=True)

    metrics_path = OUT / "selection_baseline_metrics.csv"
    raw_path = OUT / "random_subsets_raw.csv"
    rows, raw = [], []
    completed = set()
    if args.resume and metrics_path.exists():
        previous = pd.read_csv(metrics_path)
        expected_rows = len(ks) * (5 + (1 if args.n_random else 0))
        for pid, g in previous.groupby("participant_id"):
            if len(g) == expected_rows and set(g.channels_k.astype(int)) == set(ks):
                completed.add(int(pid))
        rows = previous.to_dict("records")
        if raw_path.exists():
            raw = pd.read_csv(raw_path).to_dict("records")
        jobs = [j for j in jobs if int(j[0]) not in completed]
        print(f"resuming {len(completed)} completed participant folds from {metrics_path}",
              flush=True)

    t0, done = time.time(), 0
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        futs = [ex.submit(run_fold, j) for j in jobs]
        for fut in as_completed(futs):
            r, rw = fut.result()
            rows += r
            raw += rw
            done += 1
            pd.DataFrame(rows).to_csv(metrics_path, index=False)
            pd.DataFrame(raw).to_csv(raw_path, index=False)
            el = time.time() - t0
            print(f"[{done}/{len(jobs)}] elapsed={el/60:.1f}m "
                  f"eta={el/done*(len(jobs)-done)/60:.1f}m", flush=True)

    df = pd.DataFrame(rows)
    summ = (df.groupby(["method", "channels_k"])
            .agg(n=("participant_id", "nunique"), mean_macro_f1=("macro_f1", "mean"),
                 sd=("macro_f1", "std")).reset_index()
            .sort_values(["channels_k", "mean_macro_f1"], ascending=[True, False]))
    summ.to_csv(OUT / "selection_baseline_summary.csv", index=False)
    print("\n" + summ.to_string(index=False), flush=True)
    print(f"\nwall clock: {(time.time()-t0)/60:.1f} min")
    return 0


if __name__ == "__main__":
    sys.exit(main())
