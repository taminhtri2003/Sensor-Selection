"""Feature extraction for NinaPro DB5 exercise E1, using DB5-specific preprocessing.

Deliberate differences from the GRABMyo pipeline, each justified by reports/db5_signal_audit.md
rather than inherited:

  band-pass   10-89 Hz effective; requested95Hz is capped by the shared filter at0.45*fs-1
  notch       none (not 50 Hz)          -- no powerline peak exists in DB5
  window      50 samples = 250 ms       -- same duration, far fewer samples
  thresholds  7 ADC units (not 0.01 mV) -- DB5 is 8-bit integer ADC codes, not millivolts

The threshold is set to ~1.17x the measured median |diff| of this dataset, matching the ratio used
for GRABMyo (1e-2 mV vs its median |diff| of 8.74e-3). Carrying the GRABMyo value across unchanged
would sit ~6 orders of magnitude below DB5's signal and saturate the count features, which is the
defect that was just removed from the GRABMyo pipeline.

Segmentation uses `restimulus`/`rerepetition` (refined movement boundaries) rather than the raw
prompt timing in `stimulus`. Windows never cross a movement or repetition boundary.

Outputs:
  data/features/db5_features.parquet
  data/features/db5_extraction_qc.csv
  reports/db5_feature_extraction_report.md
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.io as sio

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.semg_sparse.features.handcrafted import (  # noqa: E402
    extract_window_features,
    get_feature_mapping,
)
from src.semg_sparse.preprocessing.filters import bandpass_filter  # noqa: E402
from src.semg_sparse.segmentation.windowing import create_sliding_windows  # noqa: E402

RAW = ROOT / "data" / "raw" / "ninapro_db5"
OUT = ROOT / "data" / "features"
REPORTS = ROOT / "reports"

FS = 200.0
BAND_LOW, BAND_HIGH, BAND_ORDER = 10.0, 95.0, 4
WINDOW_MS, OVERLAP_PCT = 250.0, 50.0
N_CHANNELS = 16
THRESH = 7.0                      # ADC units; see module docstring
EXPECTED_SUBJECTS = 10
EXPECTED_MOVEMENTS = 12
EXPECTED_REPS = 6

FEAT_NAMES, _, _ = get_feature_mapping(N_CHANNELS)


def contiguous_blocks(labels, reps):
    """Yield (movement, repetition, start, stop) for each contiguous constant-label run."""
    key = np.stack([labels, reps], axis=1)
    change = np.any(np.diff(key, axis=0) != 0, axis=1)
    edges = np.flatnonzero(change) + 1
    starts = np.concatenate([[0], edges])
    stops = np.concatenate([edges, [len(labels)]])
    for a, b in zip(starts, stops):
        yield int(labels[a]), int(reps[a]), int(a), int(b)


def main():
    files = sorted(RAW.rglob("*_E1_*.mat"))
    if not files:
        print("FATAL: no DB5 E1 files found; run scripts/22_acquire_db5.py first")
        return 2

    qc_rows, meta_blocks, feat_blocks = [], [], []

    for f in files:
        subject = f.parent.name                     # s1..s10 (folder identity is the key)
        d = sio.loadmat(str(f))
        emg = np.asarray(d["emg"], dtype=np.float64)[:, :N_CHANNELS]
        rst = np.asarray(d["restimulus"]).ravel().astype(int)
        rrep = np.asarray(d.get("rerepetition", d["repetition"])).ravel().astype(int)

        filtered = bandpass_filter(emg, fs=FS, lowcut=BAND_LOW, highcut=BAND_HIGH,
                                   order=BAND_ORDER)
        # No notch: reports/db5_signal_audit.md shows no powerline peak (ratios 0.26 / 0.65).

        n_win_subject = 0
        for movement, rep, a, b in contiguous_blocks(rst, rrep):
            if movement == 0 or rep == 0:           # rest / inter-trial: excluded from primary
                continue
            seg = filtered[a:b]
            windows, bounds = create_sliding_windows(
                seg, fs=FS, window_ms=WINDOW_MS, overlap_pct=OVERLAP_PCT)
            if len(windows) == 0:
                qc_rows.append({
                    "subject": subject, "movement": movement, "repetition": rep,
                    "n_samples": int(b - a), "n_windows": 0,
                    "status": "TOO_SHORT",
                    "reason": f"{b-a} samples < {int(WINDOW_MS/1000*FS)}",
                })
                continue

            meta = np.empty((len(windows), 4), dtype=np.int32)
            feats = np.empty((len(windows), len(FEAT_NAMES)), dtype=np.float32)
            for i, (win, (s0, s1)) in enumerate(zip(windows, bounds)):
                feats[i] = extract_window_features(
                    win, fs=FS, zc_thresh=THRESH, ssc_thresh=THRESH, wamp_thresh=THRESH
                ).astype(np.float32)
                meta[i] = (int(subject[1:]), movement, rep, i)
            meta_blocks.append(meta)
            feat_blocks.append(feats)
            n_win_subject += len(windows)
            qc_rows.append({
                "subject": subject, "movement": movement, "repetition": rep,
                "n_samples": int(b - a), "n_windows": int(len(windows)),
                "status": "OK", "reason": "",
            })
        print(f"  {subject}: {n_win_subject} windows", flush=True)

    OUT.mkdir(parents=True, exist_ok=True)
    qc = pd.DataFrame(qc_rows)
    qc.to_csv(OUT / "db5_extraction_qc.csv", index=False)

    meta = np.concatenate(meta_blocks, axis=0)
    feats = np.concatenate(feat_blocks, axis=0)
    df = pd.DataFrame(meta, columns=["participant_id", "gesture_id", "trial_id", "window_idx"])
    df.insert(0, "dataset", "NinaProDB5")
    df.insert(2, "session_id", 1)
    df = pd.concat([df, pd.DataFrame(feats, columns=FEAT_NAMES)], axis=1)
    df.to_parquet(OUT / "db5_features.parquet", index=False)

    n_sub = df.participant_id.nunique()
    n_mov = df.gesture_id.nunique()
    n_rep = df.trial_id.nunique()
    counts = df.groupby("gesture_id").size()

    with open(REPORTS / "db5_feature_extraction_report.md", "w", encoding="utf-8") as fh:
        fh.write("# NinaPro DB5 feature extraction (exercise E1)\n\n")
        fh.write(f"- Subjects: **{n_sub}**\n- Movements: **{n_mov}** (rest excluded)\n")
        fh.write(f"- Repetitions: **{n_rep}**\n- Windows: **{len(df)}**\n")
        fh.write(f"- Blocks too short to window: "
                 f"**{int((qc.status == 'TOO_SHORT').sum())}**\n\n")
        fh.write("## Preprocessing (DB5-specific, see reports/db5_signal_audit.md)\n\n")
        fh.write(f"- Band-pass {BAND_LOW}-{min(BAND_HIGH, 0.45*FS-1):g} Hz effective (requested {BAND_HIGH:g} Hz upper cutoff), SciPy order argument {BAND_ORDER}, forward-backward\n")
        fh.write("- **No notch** — no powerline peak present\n")
        fh.write(f"- Window {WINDOW_MS:.0f} ms = {int(WINDOW_MS/1000*FS)} samples, "
                 f"{OVERLAP_PCT:.0f}% overlap, never crossing movement or repetition boundaries\n")
        fh.write(f"- Count-feature threshold {THRESH} ADC units (DB5 is 8-bit integer data)\n")
        fh.write(f"- Labels from `restimulus`/`rerepetition`\n\n")
        fh.write("## Windows per movement\n\n| movement | windows |\n|---|---|\n")
        for g, c in counts.items():
            fh.write(f"| {g} | {c} |\n")
        fh.write("\n## Comparability caveat\n\n")
        fh.write("Amplitude features are in **arbitrary ADC units**, not mV. They are not "
                 "numerically comparable with GRABMyo. Only relative quantities — rankings, "
                 "ranking agreement, retained-channel fraction, performance deltas — may be "
                 "compared across datasets.\n")

    print(f"\nsubjects={n_sub} movements={n_mov} reps={n_rep} windows={len(df)}")
    problems = []
    if n_sub != EXPECTED_SUBJECTS:
        problems.append(f"{n_sub} subjects != {EXPECTED_SUBJECTS}")
    if n_mov != EXPECTED_MOVEMENTS:
        problems.append(f"{n_mov} movements != {EXPECTED_MOVEMENTS}")
    if n_rep != EXPECTED_REPS:
        problems.append(f"{n_rep} repetitions != {EXPECTED_REPS}")
    if problems:
        print("COHORT ASSERTION FAILED: " + "; ".join(problems))
        return 1
    print("COHORT ASSERTION PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
