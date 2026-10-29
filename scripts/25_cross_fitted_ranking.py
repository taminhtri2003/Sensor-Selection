"""Cross-fitted channel attribution and stability-regularised ranking, per outer LOSO fold.

For each held-out participant p, the ranking R_{-p} is derived using only the other 42
participants: inner subject-grouped folds are fitted on inner-train subjects and attributed on
inner-validation subjects. Participant p influences neither the models, the scaler, nor the
ranking, so the sparse subset later evaluated on p was chosen without seeing p.

Retaining per-inner-fold importances is the point: it is what makes attribution *stability*
measurable, and stability is the quantity the study turns on.

Outputs:
  artifacts/rankings/cross_fitted_importance_long.csv   one row per (outer fold, inner fold, channel)
  artifacts/rankings/cross_fitted_scores.csv            A_c, U_c, Q_c(lambda) per outer fold
  artifacts/rankings/cross_fitted_rankings.csv          ordered channel list per outer fold and lambda
"""

import argparse
import hashlib
import importlib.metadata
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.semg_sparse.xai.cross_fitted import compute_cross_fitted_attribution  # noqa: E402

CACHE = ROOT / "data" / "cache"
OUT = ROOT / "artifacts" / "rankings"
CHECKPOINTS = OUT / "cross_fitted_checkpoints"
SEED = 20260728
LAMBDAS = (0.0, 0.25, 0.5, 1.0)
N_CHANNELS = 16
N_FPC = 10


def run_outer(job):
    pid, paths, n_inner, device, max_attrib, max_train = job
    xp, yp, sp, fj = paths
    X = np.load(xp, mmap_mode="r")
    y = np.load(yp, mmap_mode="r")
    subj = np.load(sp, mmap_mode="r")
    fcols = json.loads(Path(fj).read_text())

    tr = np.asarray(subj) != pid          # outer test participant excluded entirely
    Xtr = np.asarray(X[tr], dtype=np.float32)
    ytr = np.asarray(y[tr])
    gtr = np.asarray(subj[tr])

    t = time.time()
    res = compute_cross_fitted_attribution(
        Xtr, ytr, gtr, fcols, n_channels=N_CHANNELS, n_features_per_channel=N_FPC,
        n_inner_folds=n_inner, device=device, max_attrib_samples=max_attrib,
        max_train_samples=max_train, seed=SEED, excluded_subjects=(pid,),
    )

    long_rows = []
    for j in range(res.importance_norm.shape[0]):
        for c in range(N_CHANNELS):
            long_rows.append({
                "outer_participant": int(pid), "inner_fold": j, "channel": c + 1,
                "importance_raw": float(res.importance_raw[j, c]),
                "importance_norm": float(res.importance_norm[j, c]),
                "inner_held_subjects": ";".join(map(str, res.fold_subjects[j])),
                "n_attrib_samples": res.n_attrib_samples[j],
            })

    A, U = res.central(), res.instability()
    score_rows = [{
        "outer_participant": int(pid), "channel": c + 1,
        "A_central": float(A[c]), "U_instability": float(U[c]),
        **{f"Q_lam{lam}": float(res.score(lam)[c]) for lam in LAMBDAS},
    } for c in range(N_CHANNELS)]

    rank_rows = [{
        "outer_participant": int(pid), "lambda": lam,
        "ranking": ";".join(str(c + 1) for c in res.ranking(lam)),
    } for lam in LAMBDAS]

    # Per-individual attribution: one row per (outer fold, attributed subject, channel).
    # Fold-level importance averages over a group of held-out subjects and so understates
    # between-person variation; these rows allow the stronger claim to be tested directly.
    subj_rows = [
        {"outer_participant": int(pid), "attributed_subject": int(s), "channel": c + 1,
         "importance_norm": float(v[c])}
        for s, v in res.per_subject_norm.items() for c in range(N_CHANNELS)
    ]

    return pid, long_rows, score_rows, rank_rows, subj_rows, round(time.time() - t, 1)


def checkpoint_path(pid):
    """Return the durable checkpoint path for one completed outer fold."""
    return CHECKPOINTS / f"outer_{int(pid):02d}.json"


def write_checkpoint(pid, long_rows, score_rows, rank_rows, subj_rows, seconds):
    """Persist one completed fold atomically so an interrupted run can resume safely."""
    CHECKPOINTS.mkdir(parents=True, exist_ok=True)
    payload = {
        "outer_participant": int(pid),
        "long_rows": long_rows,
        "score_rows": score_rows,
        "rank_rows": rank_rows,
        "subj_rows": subj_rows,
        "seconds": float(seconds),
    }
    target = checkpoint_path(pid)
    temp = target.with_suffix(".json.tmp")
    temp.write_text(json.dumps(payload), encoding="utf-8")
    temp.replace(target)


def read_checkpoint(pid):
    """Read a checkpoint and validate its identity before using it."""
    path = checkpoint_path(pid)
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if int(payload.get("outer_participant", -1)) != int(pid):
        raise ValueError(f"checkpoint identity mismatch: {path}")
    return payload


def main():
    global OUT, CHECKPOINTS
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--inner-folds", type=int, default=5)
    ap.add_argument("--max-attrib", type=int, default=20000)
    ap.add_argument("--max-train", type=int, default=200000,
                    help="cap inner-fold training windows; see decision log 8")
    ap.add_argument("--resume", action="store_true",
                    help="reuse complete per-outer-fold checkpoints in the rankings directory")
    ap.add_argument("--output-dir", type=Path, default=OUT,
                    help="isolated destination for a new protocol; legacy checkpoints cannot be resumed blindly")
    args = ap.parse_args()
    OUT = args.output_dir.resolve()
    CHECKPOINTS = OUT / "cross_fitted_checkpoints"

    OUT.mkdir(parents=True, exist_ok=True)
    xp, yp, sp = CACHE / "loso_X.npy", CACHE / "loso_y.npy", CACHE / "loso_subj.npy"
    fj = CACHE / "loso_features.json"
    for p in (xp, yp, sp, fj):
        if not p.exists():
            print(f"FATAL: {p} missing — run scripts/24_full_channel_loso_parallel.py first")
            return 2

    def digest(path):
        h = hashlib.sha256()
        with path.open('rb') as f:
            for chunk in iter(lambda: f.read(1024*1024), b''):
                h.update(chunk)
        return h.hexdigest()

    protocol = {"inner_folds": args.inner_folds, "device": args.device,
                "max_attrib": args.max_attrib, "max_train": args.max_train,
                "seed": SEED, "xgboost": importlib.metadata.version('xgboost'),
                "source_sha256": digest(ROOT / 'src/semg_sparse/xai/cross_fitted.py'),
                "inputs": {p.name: digest(p) for p in (xp,yp,sp,fj)}}
    manifest = OUT / 'protocol_fingerprint.json'
    has_checkpoints = CHECKPOINTS.exists() and any(CHECKPOINTS.glob('outer_*.json'))
    if has_checkpoints and not manifest.exists():
        raise ValueError('legacy checkpoints have no protocol fingerprint; use a new --output-dir')
    if manifest.exists() and json.loads(manifest.read_text()) != protocol:
        raise ValueError('checkpoint inputs/protocol changed; use a new --output-dir')
    manifest.write_text(json.dumps(protocol,indent=2),encoding='utf-8')

    subj = np.load(sp, mmap_mode="r")
    participants = sorted(np.unique(np.asarray(subj)).tolist())
    completed = {}
    if args.resume:
        completed = {p: read_checkpoint(p) for p in participants}
        completed = {p: v for p, v in completed.items() if v is not None}
        if completed:
            print(f"resuming {len(completed)}/{len(participants)} completed outer folds from "
                  f"{CHECKPOINTS}", flush=True)
    print(f"outer folds={len(participants)} inner={args.inner_folds} "
          f"workers={args.workers} device={args.device} "
          f"pending={len(participants) - len(completed)}", flush=True)

    jobs = [(p, (str(xp), str(yp), str(sp), str(fj)), args.inner_folds,
             args.device, args.max_attrib, args.max_train) for p in participants]
    jobs = [j for j in jobs if j[0] not in completed]

    longs = [row for p in completed.values() for row in p["long_rows"]]
    scores = [row for p in completed.values() for row in p["score_rows"]]
    ranks = [row for p in completed.values() for row in p["rank_rows"]]
    subjects = [row for p in completed.values() for row in p["subj_rows"]]
    t0, done = time.time(), 0
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        futs = [ex.submit(run_outer, j) for j in jobs]
        for fut in as_completed(futs):
            pid, lr, sr, rr, pr, secs = fut.result()
            write_checkpoint(pid, lr, sr, rr, pr, secs)
            longs += lr
            scores += sr
            ranks += rr
            subjects += pr
            done += 1
            top = next(r["ranking"] for r in rr if r["lambda"] == 0.0).split(";")[:4]
            el = time.time() - t0
            print(f"[{done}/{len(jobs)}] participant {pid:02d} top4(lam=0)={top} "
                  f"{secs}s  elapsed={el/60:.1f}m "
                  f"eta={el/done*(len(jobs)-done)/60:.1f}m",
                  flush=True)
            pd.DataFrame(scores).to_csv(OUT / "cross_fitted_scores.csv", index=False)

    longs.sort(key=lambda r: (r["outer_participant"], r["inner_fold"], r["channel"]))
    scores.sort(key=lambda r: (r["outer_participant"], r["channel"]))
    ranks.sort(key=lambda r: (r["outer_participant"], r["lambda"]))
    subjects.sort(key=lambda r: (r["outer_participant"], r["attributed_subject"], r["channel"]))
    pd.DataFrame(longs).to_csv(OUT / "cross_fitted_importance_long.csv", index=False)
    pd.DataFrame(scores).to_csv(OUT / "cross_fitted_scores.csv", index=False)
    pd.DataFrame(ranks).to_csv(OUT / "cross_fitted_rankings.csv", index=False)
    pd.DataFrame(subjects).to_csv(OUT / "per_subject_attribution.csv", index=False)

    df = pd.DataFrame(scores)
    pop = df.groupby("channel").A_central.mean().sort_values(ascending=False)
    print("\nmean A_c across outer folds (population view):", flush=True)
    print(pop.to_string(), flush=True)

    n_out = df.outer_participant.nunique()
    if n_out != len(participants):
        print(f"ASSERTION FAILED: {n_out} outer folds != {len(participants)}")
        return 1
    print(f"\nASSERTION PASSED: {n_out} outer folds x {N_CHANNELS} channels")
    print(f"wall clock: {(time.time()-t0)/60:.1f} min")
    return 0


if __name__ == "__main__":
    sys.exit(main())
