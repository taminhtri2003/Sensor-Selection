"""Feature extraction over the COMPLETE verified GRABMyo cohort (43 participants x 3 sessions).

Replaces scripts/05_extract_features_fast.py, which read a partial mirror
(data/raw/grabmyo: 29 participants, session 1 only) and swallowed every per-record failure
with `except Exception: pass`, silently reducing the cohort to 15 participants.

Design rules enforced here:
  1. Read from the checksum-verified root trees Session1/, Session2/, Session3/ only.
  2. Every record produces a QC row. A record may only be dropped with a recorded reason.
  3. The realised cohort is asserted against the expected cohort; any shortfall is a hard failure.
  4. Channel selection is validated per record against the header signal names (F1..F16),
     never assumed from position alone.

Outputs:
  data/features/grabmyo_features_full.parquet   one row per window
  data/features/grabmyo_extraction_qc.csv       one row per expected record
  reports/feature_extraction_report.md
"""

import sys
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd
import wfdb

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.semg_sparse.preprocessing.filters import bandpass_filter, notch_filter  # noqa: E402
from src.semg_sparse.features.handcrafted import (  # noqa: E402
    extract_window_features,
    get_feature_mapping,
)
from src.semg_sparse.segmentation.windowing import create_sliding_windows  # noqa: E402

SESSIONS = (1, 2, 3)
PARTICIPANTS = tuple(range(1, 44))
GESTURES = tuple(range(1, 18))          # 17 = Rest (see MotionSequence.txt)
TRIALS = tuple(range(1, 8))
FOREARM = tuple(f"F{i}" for i in range(1, 17))

EXPECTED_FS = 2048.0
EXPECTED_NSIG = 32
BAND_LOW, BAND_HIGH, BAND_ORDER = 20.0, 450.0, 4
NOTCH_HZ, NOTCH_Q = 50.0, 30.0          # 50 Hz confirmed empirically, see signal_properties_audit
WINDOW_MS, OVERLAP_PCT = 250.0, 50.0

FEAT_NAMES, _, _ = get_feature_mapping(16)


def record_base(sess, pid, gesture, trial):
    return (ROOT / f"Session{sess}" / f"session{sess}_participant{pid}"
            / f"session{sess}_participant{pid}_gesture{gesture}_trial{trial}")


def process_record(job):
    """Return (qc_row, feature_rows). Never raises; failures are reported, not swallowed."""
    sess, pid, gesture, trial = job
    base = record_base(sess, pid, gesture, trial)
    qc = {
        "session_id": sess, "participant_id": pid, "gesture_id": gesture, "trial_id": trial,
        "path": str(base.relative_to(ROOT)).replace("\\", "/"),
        "status": "OK", "reason": "", "n_samples": 0, "n_sig": 0, "fs": 0.0, "n_windows": 0,
    }

    try:
        if not base.with_suffix(".dat").exists():
            qc.update(status="MISSING", reason="no .dat file")
            return qc, None

        rec = wfdb.rdrecord(str(base))
        sig = np.asarray(rec.p_signal, dtype=np.float64)
        fs = float(rec.fs)
        names = list(rec.sig_name or [])
        qc.update(n_samples=int(sig.shape[0]), n_sig=int(sig.shape[1]), fs=fs)

        if sig.shape[1] != EXPECTED_NSIG:
            qc.update(status="BAD_CHANNELS", reason=f"expected {EXPECTED_NSIG} signals, got {sig.shape[1]}")
            return qc, None
        if fs != EXPECTED_FS:
            qc.update(status="BAD_FS", reason=f"expected {EXPECTED_FS} Hz, got {fs}")
            return qc, None

        # Validate forearm channel identity rather than trusting positional slicing.
        try:
            idx = [names.index(ch) for ch in FOREARM]
        except ValueError:
            qc.update(status="BAD_CHANNEL_NAMES", reason=f"F1..F16 not all present in {names[:20]}")
            return qc, None
        if idx != list(range(16)):
            qc.update(status="CHANNEL_ORDER", reason=f"F1..F16 not in positions 0..15: {idx}")
            return qc, None

        emg = sig[:, idx]
        if not np.all(np.isfinite(emg)):
            qc.update(status="NONFINITE", reason="NaN or Inf present in forearm channels")
            return qc, None
        flat = np.std(emg, axis=0) < 1e-12
        if flat.any():
            qc.update(status="FLAT_CHANNEL", reason=f"zero-variance channels: {np.where(flat)[0].tolist()}")
            return qc, None

        filtered = bandpass_filter(emg, fs=fs, lowcut=BAND_LOW, highcut=BAND_HIGH, order=BAND_ORDER)
        filtered = notch_filter(filtered, fs=fs, notch_freq=NOTCH_HZ, quality_factor=NOTCH_Q)

        windows, bounds = create_sliding_windows(
            filtered, fs=fs, window_ms=WINDOW_MS, overlap_pct=OVERLAP_PCT
        )
        if len(windows) == 0:
            qc.update(status="TOO_SHORT", reason=f"{sig.shape[0]} samples < window length")
            return qc, None

        n_win = len(windows)
        meta = np.empty((n_win, 7), dtype=np.int32)
        feats = np.empty((n_win, len(FEAT_NAMES)), dtype=np.float32)
        for w_idx, (win, (b0, b1)) in enumerate(zip(windows, bounds)):
            feats[w_idx] = extract_window_features(win, fs=fs).astype(np.float32)
            meta[w_idx] = (pid, sess, gesture, trial, w_idx, b0, b1)

        qc["n_windows"] = n_win
        return qc, (meta, feats)

    except Exception as exc:  # recorded, never silently dropped
        qc.update(status="ERROR", reason=f"{type(exc).__name__}: {exc}",
                  n_windows=0)
        qc["traceback"] = traceback.format_exc(limit=3)
        return qc, None


def main():
    jobs = [(s, p, g, t) for s in SESSIONS for p in PARTICIPANTS for g in GESTURES for t in TRIALS]
    expected = len(jobs)
    print(f"expected records: {expected}", flush=True)

    qc_rows, meta_blocks, feat_blocks = [], [], []
    done = 0
    with ProcessPoolExecutor(max_workers=10) as ex:
        futures = [ex.submit(process_record, j) for j in jobs]
        for fut in as_completed(futures):
            qc_row, payload = fut.result()
            qc_rows.append(qc_row)
            if payload is not None:
                meta_blocks.append(payload[0])
                feat_blocks.append(payload[1])
            done += 1
            if done % 500 == 0:
                ok = sum(1 for r in qc_rows if r["status"] == "OK")
                nw = sum(b.shape[0] for b in feat_blocks)
                print(f"  {done}/{expected}  ok={ok}  windows={nw}", flush=True)

    qc = pd.DataFrame(qc_rows).sort_values(
        ["session_id", "participant_id", "gesture_id", "trial_id"]
    )
    out_dir = ROOT / "data" / "features"
    out_dir.mkdir(parents=True, exist_ok=True)
    qc.to_csv(out_dir / "grabmyo_extraction_qc.csv", index=False)

    meta = np.concatenate(meta_blocks, axis=0)
    feats = np.concatenate(feat_blocks, axis=0)
    del meta_blocks, feat_blocks

    meta_cols = ["participant_id", "session_id", "gesture_id", "trial_id",
                 "window_idx", "start_sample", "end_sample"]
    df = pd.DataFrame(meta, columns=meta_cols)
    df.insert(0, "dataset", "GRABMyo")
    df = pd.concat([df, pd.DataFrame(feats, columns=FEAT_NAMES)], axis=1)
    del meta, feats
    df = df.sort_values(["session_id", "participant_id", "gesture_id", "trial_id", "window_idx"])
    df.to_parquet(out_dir / "grabmyo_features_full.parquet", index=False)

    n_ok = int((qc["status"] == "OK").sum())
    status_counts = qc["status"].value_counts().to_dict()
    got_p = sorted(df["participant_id"].unique())
    got_s = sorted(df["session_id"].unique())
    got_g = sorted(df["gesture_id"].unique())

    report = ROOT / "reports" / "feature_extraction_report.md"
    with open(report, "w", encoding="utf-8") as f:
        f.write("# GRABMyo feature extraction — complete cohort\n\n")
        f.write(f"- Expected records: **{expected}** (43 participants x 3 sessions x 17 gestures x 7 trials)\n")
        f.write(f"- Extracted OK: **{n_ok}**\n")
        f.write(f"- Status breakdown: `{status_counts}`\n")
        f.write(f"- Total windows: **{len(df)}**\n")
        f.write(f"- Participants realised: **{len(got_p)}**\n")
        f.write(f"- Sessions realised: **{got_s}**\n")
        f.write(f"- Gestures realised: **{len(got_g)}**\n\n")
        f.write("## Preprocessing\n\n")
        f.write(f"- Channels: 16 forearm (F1..F16), validated by header name per record\n")
        f.write(f"- Bandpass: {BAND_LOW}-{BAND_HIGH} Hz, order {BAND_ORDER}, zero-phase (filtfilt)\n")
        f.write(f"- Notch: {NOTCH_HZ} Hz, Q={NOTCH_Q}, zero-phase — 50 Hz confirmed empirically\n")
        f.write(f"- Window: {WINDOW_MS} ms, {OVERLAP_PCT}% overlap, never crossing trial boundaries\n")
        f.write(f"- Features: 10 per channel x 16 channels = 160\n\n")
        if n_ok < expected:
            f.write("## Failed records\n\n")
            bad = qc[qc["status"] != "OK"]
            for _, r in bad.head(60).iterrows():
                f.write(f"- `{r['path']}` — {r['status']}: {r['reason']}\n")
            if len(bad) > 60:
                f.write(f"\n...and {len(bad) - 60} more (see grabmyo_extraction_qc.csv)\n")

    print(f"\nstatus: {status_counts}")
    print(f"windows={len(df)} participants={len(got_p)} sessions={got_s} gestures={len(got_g)}")

    # Hard cohort assertion — the failure mode that produced the fabricated manuscript.
    problems = []
    if len(got_p) != 43:
        problems.append(f"participants {len(got_p)} != 43")
    if got_s != [1, 2, 3]:
        problems.append(f"sessions {got_s} != [1, 2, 3]")
    if len(got_g) != 17:
        problems.append(f"gestures {len(got_g)} != 17")
    if n_ok != expected:
        problems.append(f"{expected - n_ok} records failed extraction")
    if problems:
        print("\nCOHORT ASSERTION FAILED: " + "; ".join(problems))
        return 1
    print("\nCOHORT ASSERTION PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
