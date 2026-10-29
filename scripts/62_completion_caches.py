"""Feature caches for the completion analyses (decision log 24b, 24c).

  data/cache/rest17/  250 ms features, 17 classes (16 active gestures + Rest), labels 0..16
  data/cache/w150/    150 ms features, 16 active gestures
  data/cache/w500/    500 ms features, 16 active gestures

Checks before anything is written:
  1. The builder, applied to the primary 250 ms parquet with the primary class filter, reproduces
     data/cache/loso_{X,y,subj}.npy exactly, so the new caches differ from the primary one only
     by the intended change (classes or window length).
  2. Re-extracting a few raw records at 250 ms in this Python environment reproduces the stored
     primary features, so the re-extracted window lengths come from the same feature chain.
"""

import importlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
FEAT = ROOT / "data" / "features"
CACHE = ROOT / "data" / "cache"
META_COLS = ["dataset", "participant_id", "session_id", "gesture_id", "trial_id",
             "window_idx", "start_sample", "end_sample"]
SPOT_RECORDS = [(1, 1, 1, 1), (2, 17, 9, 4), (3, 43, 17, 7)]


def arrays(parquet, max_gesture):
    df = pd.read_parquet(parquet)
    fcols = [c for c in df.columns if c not in META_COLS]
    d = df[df.gesture_id <= max_gesture]
    return (d[fcols].to_numpy(np.float32), (d.gesture_id.to_numpy() - 1).astype(np.int64),
            d.participant_id.to_numpy().astype(np.int32),
            d.session_id.to_numpy().astype(np.int32), fcols, d)


def write(name, X, y, s, e, fcols):
    out = CACHE / name
    out.mkdir(parents=True, exist_ok=True)
    files = {"loso_X.npy": X, "loso_y.npy": y, "loso_subj.npy": s, "loso_sess.npy": e}
    if all((out / f).exists() for f in files) and (out / "loso_features.json").exists():
        # A running analysis may hold the cache open; verify it instead of rewriting it.
        same = all(np.array_equal(np.load(out / f, mmap_mode="r"), v) for f, v in files.items())
        if not same or json.loads((out / "loso_features.json").read_text()) != fcols:
            raise SystemExit(f"FATAL: existing cache {out} differs from its source")
        print(f"{name}: existing cache verified")
    else:
        for f, v in files.items():
            np.save(out / f, v)
        (out / "loso_features.json").write_text(json.dumps(fcols))
    print(f"{name}: windows={len(y)} classes={len(np.unique(y))} participants={len(np.unique(s))}")
    return {"windows": int(len(y)), "classes": int(len(np.unique(y))),
            "participants": int(len(np.unique(s)))}


def main():
    primary_fcols = json.loads((CACHE / "loso_features.json").read_text())

    # Check 1: builder reproduces the primary cache.
    X, y, s, _, fcols, _ = arrays(FEAT / "grabmyo_features_full.parquet", 16)
    ok = (fcols == primary_fcols
          and np.array_equal(X, np.load(CACHE / "loso_X.npy"))
          and np.array_equal(y, np.load(CACHE / "loso_y.npy"))
          and np.array_equal(s, np.load(CACHE / "loso_subj.npy")))
    print(f"builder reproduces primary cache: {ok}")
    if not ok:
        return 1

    # Check 2: raw re-extraction in this environment reproduces stored 250 ms features.
    m20 = importlib.import_module("20_extract_features_full")
    full = pd.read_parquet(FEAT / "grabmyo_features_full.parquet")
    max_abs = 0.0
    for rec in SPOT_RECORDS:
        qc, payload = m20.process_record(rec)
        if payload is None:
            print(f"spot record {rec} failed: {qc}")
            return 1
        sess, pid, g, t = rec
        ref = full[(full.session_id == sess) & (full.participant_id == pid)
                   & (full.gesture_id == g) & (full.trial_id == t)].sort_values("window_idx")
        new = payload[1]
        if new.shape != ref[primary_fcols].shape:
            print(f"spot record {rec}: shape {new.shape} vs {ref[primary_fcols].shape}")
            return 1
        refv = ref[primary_fcols].to_numpy(np.float64)
        rel = np.abs(new - refv) / (np.abs(refv) + 1e-6)
        max_abs = max(max_abs, float(rel.max()))
    print(f"spot re-extraction max relative difference: {max_abs:.2e}")
    if max_abs > 1e-4:
        return 1
    del full

    summary = {"builder_reproduces_primary": True, "spot_reextraction_max_rel_diff": max_abs}
    X, y, s, e, fcols, _ = arrays(FEAT / "grabmyo_features_full.parquet", 17)
    summary["rest17"] = write("rest17", X, y, s, e, fcols)
    for ms in (150, 500):
        pq = FEAT / f"grabmyo_features_full_w{ms}ms.parquet"
        if not pq.exists():
            print(f"missing {pq}; run scripts/20_extract_features_full.py --window-ms {ms}")
            return 2
        X, y, s, e, fcols, _ = arrays(pq, 16)
        if fcols != primary_fcols:
            print(f"feature columns differ for {ms} ms")
            return 1
        summary[f"w{ms}"] = write(f"w{ms}", X, y, s, e, fcols)
    out = ROOT / "artifacts" / "completion_analyses"
    out.mkdir(parents=True, exist_ok=True)
    (out / "cache_build.json").write_text(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
