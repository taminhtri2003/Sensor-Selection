"""putEMG feature extraction (exploratory external replication; design in decision_log Decision 19).

Pass 1: per-file median |first difference| of the FILTERED signal (mV) -> threshold rule
        (1.15 x median, one significant figure), verified leave-one-participant-out. Aborts if
        any fold would give a different threshold (then fold-wise features would be required).
Pass 2: windows of 250 ms / 50% overlap inside contiguous active TRAJ_GT runs, 10 features x 24 ch.

Outputs:
  artifacts/putemg/threshold_probe.csv, artifacts/putemg/threshold_loo.csv
  data/features/putemg_features.parquet, data/features/putemg_extraction_qc.csv
  reports/putemg_feature_extraction_report.md
"""
import glob
import os
import re
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src.semg_sparse.features.handcrafted import extract_window_features, get_feature_mapping  # noqa: E402
from src.semg_sparse.preprocessing.filters import bandpass_filter, notch_filter  # noqa: E402
from src.semg_sparse.segmentation.windowing import create_sliding_windows  # noqa: E402

SRC = Path("F:/XAI - Force/dataset/Data-HDF5")
ART = ROOT / "artifacts" / "putemg"
FEAT = ROOT / "data" / "features"
FS = 5120.0
N_CH = 24
EMG = [f"EMG_{i}" for i in range(1, N_CH + 1)]
TO_MV = 5.0 / 4096 * 1000 / 200
ACTIVE = (1, 2, 3, 6, 7, 8, 9)
TRAJ = {"repeats_long": 1, "sequential": 2, "repeats_short": 3}
NAME = re.compile(r"emg_gestures-(\d+)-(repeats_long|repeats_short|sequential)-"
                  r"(\d{4}-\d{2}-\d{2})-")
FEAT_NAMES, _, _ = get_feature_mapping(N_CH)


def load(path):
    d = pd.read_hdf(path)
    x = d[EMG].to_numpy(np.float64) * TO_MV
    f = bandpass_filter(x, fs=FS, lowcut=20.0, highcut=450.0, order=4)
    f = notch_filter(f, fs=FS, notch_freq=50.0, quality_factor=30.0)
    return f, d["TRAJ_GT"].to_numpy()


def probe(path):
    m = NAME.search(os.path.basename(path))
    f, _ = load(path)
    return {"file": os.path.basename(path), "subject": int(m.group(1)),
            "median_absdiff_filtered_mV": float(np.median(np.abs(np.diff(f, axis=0))))}


def rule(med):
    return float(f"{1.15 * med:.0e}")


def extract(job):
    path, session, thresh = job
    m = NAME.search(os.path.basename(path))
    subj, traj = int(m.group(1)), TRAJ[m.group(2)]
    f, gt = load(path)
    gt = np.where(np.isnan(gt), -9, gt).astype(int)
    edges = np.flatnonzero(np.diff(gt) != 0) + 1
    starts, stops = np.r_[0, edges], np.r_[edges, len(gt)]
    meta, feats, qc = [], [], []
    run = 0
    for a, b in zip(starts, stops):
        lab = int(gt[a])
        if lab not in ACTIVE:
            continue
        run += 1
        wins, _ = create_sliding_windows(f[a:b], fs=FS, window_ms=250.0, overlap_pct=50.0)
        qc.append({"subject": subj, "session": session, "trajectory": traj, "run": run,
                   "gesture": lab, "n_samples": int(b - a), "n_windows": int(len(wins))})
        for i, w in enumerate(wins):
            feats.append(extract_window_features(w, fs=FS, zc_thresh=thresh, ssc_thresh=thresh,
                                                 wamp_thresh=thresh).astype(np.float32))
            meta.append((subj, session, lab, traj * 1000 + run, i))
    return (np.asarray(meta, np.int32).reshape(-1, 5), np.asarray(feats, np.float32).reshape(-1, len(FEAT_NAMES)), qc)


def main():
    files = sorted(glob.glob(str(SRC / "emg_gestures-*.hdf5")))
    assert len(files) == 264, len(files)
    man = pd.read_csv(ROOT / "data/manifests/putemg_manifest.csv").set_index("file")
    ART.mkdir(parents=True, exist_ok=True)

    pp = ART / "threshold_probe.csv"
    if pp.exists():
        pr = pd.read_csv(pp)
    else:
        with ProcessPoolExecutor(max_workers=6) as ex:
            pr = pd.DataFrame(list(ex.map(probe, files)))
        pr.to_csv(pp, index=False)
    pooled = float(pr.median_absdiff_filtered_mV.median())
    thresh = rule(pooled)
    loo = pd.DataFrame([{"held_out": s,
                         "loo_median": float(pr[pr.subject != s].median_absdiff_filtered_mV.median())}
                        for s in sorted(pr.subject.unique())])
    loo["loo_threshold"] = loo.loo_median.map(rule)
    loo["identical"] = np.isclose(loo.loo_threshold, thresh)
    loo.to_csv(ART / "threshold_loo.csv", index=False)
    print(f"pooled filtered median |diff| = {pooled:.4g} mV -> threshold {thresh:g} mV; "
          f"LOO median {loo.loo_median.min():.4g}-{loo.loo_median.max():.4g}; "
          f"identical in {int(loo.identical.sum())}/{len(loo)} folds", flush=True)
    if not loo.identical.all():
        print("ABORT: threshold depends on the held-out participant; fold-wise features required")
        return 3

    jobs = [(p, int(man.loc[os.path.basename(p), "session"]), thresh) for p in files]
    metas, feats, qcs = [], [], []
    with ProcessPoolExecutor(max_workers=6) as ex:
        for n, (m, x, q) in enumerate(ex.map(extract, jobs), 1):
            metas.append(m), feats.append(x), qcs.extend(q)
            if n % 20 == 0:
                print(f"  {n}/264 files", flush=True)
    meta = np.concatenate(metas)
    X = np.concatenate(feats)
    df = pd.DataFrame(meta, columns=["participant_id", "session_id", "gesture_id", "trial_id",
                                     "window_idx"])
    df.insert(0, "dataset", "putEMG")
    df = pd.concat([df, pd.DataFrame(X, columns=FEAT_NAMES)], axis=1)
    FEAT.mkdir(parents=True, exist_ok=True)
    df.to_parquet(FEAT / "putemg_features.parquet", index=False)
    qc = pd.DataFrame(qcs)
    qc.to_csv(FEAT / "putemg_extraction_qc.csv", index=False)

    per = df.groupby("participant_id").size()
    cls = df.groupby("gesture_id").size()
    lines = ["# putEMG feature extraction", "",
             f"- Files: 264; participants: {df.participant_id.nunique()}; sessions per participant: "
             f"{df.groupby('participant_id').session_id.nunique().min()}-"
             f"{df.groupby('participant_id').session_id.nunique().max()}",
             f"- Active runs: {len(qc)}; runs shorter than one window: {int((qc.n_windows == 0).sum())}",
             f"- Windows: {len(df)}; per participant min {per.min()}, median {per.median():.0f}, max {per.max()}",
             f"- Count-feature threshold: {thresh:g} mV (pooled filtered median |diff| {pooled:.4g} mV; "
             f"identical in {int(loo.identical.sum())}/{len(loo)} leave-one-out folds)",
             "", "| gesture | windows |", "|---|---|"] + [f"| {g} | {c} |" for g, c in cls.items()]
    (ROOT / "reports/putemg_feature_extraction_report.md").write_text("\n".join(lines) + "\n",
                                                                       encoding="utf-8")
    print("\n".join(lines))
    ok = df.participant_id.nunique() == 44 and df.gesture_id.nunique() == 7
    print("COHORT ASSERTION", "PASSED" if ok else "FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
