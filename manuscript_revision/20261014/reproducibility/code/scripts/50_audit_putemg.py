"""putEMG integrity and signal audit (exploratory external replication, added 2026-09-21).

Facts taken from the dataset paper (Kaczmarek et al., Sensors 2019, 19:3548) are VERIFIED here
against the files rather than assumed:
  - 44 subjects x 2 experiments (>= 1 week apart) x 3 trajectories  -> 264 gesture files
  - 24 monopolar channels EMG_1..EMG_24 (bands: elbow 1-8, middle 9-16, wrist 17-24)
  - 5120 Hz, raw 12-bit ADC values; mV = N * 5 / 2**12 * 1000 / 200
  - labels: TRAJ_GT (video-verified; -1 = rejected / relax), 0 = idle, active 1,2,3,6,7,8,9

No checksum file ships with the local copy, so a SHA-256 manifest is written now; it fixes the
state of the data used, it does not prove the download matched the publisher's copy.

Outputs:
  data/manifests/putemg_manifest.csv   (file, subject, session, trajectory, sha256, size)
  reports/putemg_audit.csv             (per-file checks)
  reports/putemg_audit.md
"""

import glob
import hashlib
import os
import re
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.signal import welch

ROOT = Path(__file__).resolve().parent.parent
SRC = Path("F:/XAI - Force/dataset/Data-HDF5")
FS = 5120.0
EMG = [f"EMG_{i}" for i in range(1, 25)]
ACTIVE = (1, 2, 3, 6, 7, 8, 9)
NAME = re.compile(r"emg_gestures-(\d+)-(repeats_long|repeats_short|sequential)-"
                  r"(\d{4}-\d{2}-\d{2})-(\d{2}-\d{2}-\d{2}-\d+)\.hdf5$")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 22), b""):
            h.update(block)
    return h.hexdigest()


def audit(path):
    m = NAME.search(os.path.basename(path))
    rec = {"file": os.path.basename(path), "subject": int(m.group(1)), "trajectory": m.group(2),
           "date": m.group(3), "size": os.path.getsize(path), "sha256": sha256(path)}
    try:
        d = pd.read_hdf(path)
        missing = [c for c in EMG + ["TRAJ_GT"] if c not in d.columns]
        rec["missing_cols"] = ";".join(missing)
        x = d[EMG].to_numpy(np.float64)
        idx = np.asarray(d.index, dtype=np.float64)
        rec["n_samples"] = len(d)
        rec["fs_est"] = float(1.0 / np.median(np.diff(idx)))
        rec["nonfinite"] = int((~np.isfinite(x)).sum())
        rec["non_integer"] = int((np.abs(x - np.round(x)) > 1e-9).sum())
        rec["abs_max_adc"] = float(np.abs(x).max())
        rec["frac_at_rail"] = float((np.abs(x) >= 2047).mean())
        rec["min_channel_std"] = float(x.std(axis=0).min())
        gt = d["TRAJ_GT"].to_numpy()
        rec["labels"] = ";".join(str(int(v)) for v in sorted(pd.unique(gt[~np.isnan(gt)])))
        rec["active_frac"] = float(np.isin(gt, ACTIVE).mean())
        rec["rejected_frac"] = float((gt == -1).mean())
        # powerline: mean PSD over channels of a 60 s mid-record segment
        seg = x[len(x) // 2: len(x) // 2 + int(60 * FS)] * (5 / 4096 * 1000 / 200)
        f, p = welch(seg - seg.mean(0), fs=FS, nperseg=8192, axis=0)
        p = p.mean(1)

        def ratio(f0):
            peak = p[(f >= f0 - 1) & (f <= f0 + 1)].max()
            base = np.median(p[((f >= f0 - 10) & (f <= f0 - 3)) | ((f >= f0 + 3) & (f <= f0 + 10))])
            return float(peak / base)
        rec["line50_ratio"], rec["line60_ratio"] = ratio(50.0), ratio(60.0)
        rec["median_absdiff_mV"] = float(np.median(np.abs(np.diff(seg, axis=0))))
        rec["status"] = "OK" if not missing and rec["nonfinite"] == 0 else "FAIL"
    except Exception as exc:                                       # noqa: BLE001
        rec["status"] = f"ERROR {type(exc).__name__}: {exc}"
    return rec


def main():
    files = sorted(glob.glob(str(SRC / "emg_gestures-*.hdf5")))
    print(f"gesture files: {len(files)}", flush=True)
    with ProcessPoolExecutor(max_workers=8) as ex:
        rows = list(ex.map(audit, files))
    df = pd.DataFrame(rows)
    # session = order of the two experiment dates per subject
    dates = df.groupby("subject").date.apply(lambda s: sorted(s.unique()))
    df["session"] = df.apply(lambda r: dates[r.subject].index(r.date) + 1, axis=1)
    df["n_dates"] = df.subject.map(dates.apply(len))
    gap = dates.apply(lambda v: (pd.Timestamp(v[-1]) - pd.Timestamp(v[0])).days if len(v) > 1 else np.nan)
    (ROOT / "data/manifests").mkdir(parents=True, exist_ok=True)
    df[["file", "subject", "session", "trajectory", "date", "size", "sha256"]].to_csv(
        ROOT / "data/manifests/putemg_manifest.csv", index=False)
    df.to_csv(ROOT / "reports/putemg_audit.csv", index=False)

    ok = df.status == "OK"
    cells = df.groupby(["subject", "session"]).trajectory.nunique()
    lines = ["# putEMG integrity and signal audit", "",
             f"- Gesture files: **{len(df)}**, readable and complete: **{int(ok.sum())}**",
             f"- Subjects: **{df.subject.nunique()}**; subjects with 2 experiment dates: "
             f"**{int((dates.apply(len) == 2).sum())}**; (subject, session) cells with all 3 "
             f"trajectories: **{int((cells == 3).sum())}/{len(cells)}**",
             f"- Days between sessions: min {gap.min():.0f}, median {gap.median():.0f}, max {gap.max():.0f}",
             f"- Sampling rate estimated from timestamps: {df.fs_est.min():.1f}-{df.fs_est.max():.1f} Hz",
             f"- Non-integer ADC samples: {int(df.non_integer.sum())}; non-finite: {int(df.nonfinite.sum())}",
             f"- Max |ADC|: {df.abs_max_adc.max():.0f}; files with any sample at the 12-bit rail "
             f"(|N| >= 2047): {int((df.frac_at_rail > 0).sum())} (max fraction {df.frac_at_rail.max():.2e})",
             f"- Smallest per-channel SD in any file: {df.min_channel_std.min():.2f} ADC units",
             f"- Powerline: median 50 Hz peak/baseline ratio {df.line50_ratio.median():.2f}, "
             f"60 Hz {df.line60_ratio.median():.2f}",
             f"- Median |first difference| (raw, mV): {df.median_absdiff_mV.median():.3e}",
             f"- Label sets seen: {sorted(df.labels.unique().tolist())}",
             f"- Active-gesture fraction of samples: median {df.active_frac.median():.3f}; "
             f"rejected (-1): median {df.rejected_frac.median():.3f}"]
    (ROOT / "reports/putemg_audit.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0 if ok.all() else 1


if __name__ == "__main__":
    sys.exit(main())
