"""Bipolar feature extraction: the 8 conventional sEMG sensors formed from the 16 monopolar electrodes.

Why this is required rather than optional.

The primary analysis selects among 16 **monopolar** electrodes. A claim of the form "k sensors
suffice" is ambiguous under that unit: selecting electrodes F3 and F11 without their ring partners
does not describe anything a conventional bipolar armband could instantiate. `Electrodelocation.pdf`
shows the forearm montage is 2 rings of 8, 2 cm apart, so the conventional sensing unit is the
vertically aligned pair:

    bipolar_j = F_j - F_{j+8},   j = 1..8

This produces the 8 forearm channels the GRABMyo data descriptor and the wider literature refer to.
Running the same pipeline on this representation answers whether the study's conclusions survive
when the unit is a deployable sensor rather than a single electrode.

Bipolar derivation also removes common-mode content shared by the two electrodes, so the resulting
signal is not simply a subset of the monopolar information — the comparison is genuinely different,
not merely coarser.

Outputs:
  data/features/grabmyo_bipolar_features.parquet
  data/features/grabmyo_bipolar_qc.csv
  reports/bipolar_extraction_report.md
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

from src.semg_sparse.features.handcrafted import (  # noqa: E402
    extract_window_features,
    get_feature_mapping,
)
from src.semg_sparse.preprocessing.filters import bandpass_filter, notch_filter  # noqa: E402
from src.semg_sparse.segmentation.windowing import create_sliding_windows  # noqa: E402

SESSIONS = (1, 2, 3)
PARTICIPANTS = tuple(range(1, 44))
GESTURES = tuple(range(1, 18))
TRIALS = tuple(range(1, 8))
RING1 = tuple(f"F{i}" for i in range(1, 9))     # proximal ring
RING2 = tuple(f"F{i}" for i in range(9, 17))    # distal ring, 2 cm away

EXPECTED_FS = 2048.0
BAND_LOW, BAND_HIGH, BAND_ORDER = 20.0, 450.0, 4
NOTCH_HZ, NOTCH_Q = 50.0, 30.0
WINDOW_MS, OVERLAP_PCT = 250.0, 50.0
N_BIPOLAR = 8

# Count-feature threshold, derived from THIS representation's own amplitude scale.
#
# Bipolar derivation cancels common-mode content and roughly halves the signal: measured
# median |diff| is 4.35e-3 mV for bipolar versus 8.74e-3 mV for monopolar. Inheriting the
# monopolar threshold of 1.0e-2 puts it at 2.30x the bipolar signal scale instead of the 1.14x
# used for monopolar, which suppresses the count features (SSC median fell to 5 of a possible 511).
#
# That is the same defect as the original WAMP saturation, mirrored: a threshold carried across a
# change of representation without re-deriving it. Set here to 1.15x the measured median |diff|,
# matching the monopolar ratio so the two representations are treated consistently.
#
# 2026-09-22 (decision_log Decision 20): the 4.35e-3 mV median quoted above could not be reproduced.
# Applying the documented rule to the documented 54 probe records (raw bipolar median 3.40e-3 mV;
# scripts/39_loo_threshold_check.py) gives 1.15 x 3.40e-3 = 3.9e-3 -> 4e-3 mV (one significant
# figure), identical in all 43 leave-one-out folds. The earlier 5e-3 mV run is archived in
# _archive_invalid/bipolar_threshold_5e-3/.
BIPOLAR_THRESH = 4.0e-3

FEAT_NAMES, _, _ = get_feature_mapping(N_BIPOLAR)


def record_base(sess, pid, gesture, trial):
    return (ROOT / f"Session{sess}" / f"session{sess}_participant{pid}"
            / f"session{sess}_participant{pid}_gesture{gesture}_trial{trial}")


def process_record(job):
    sess, pid, gesture, trial = job
    base = record_base(sess, pid, gesture, trial)
    qc = {"session_id": sess, "participant_id": pid, "gesture_id": gesture, "trial_id": trial,
          "status": "OK", "reason": "", "n_windows": 0}
    try:
        if not base.with_suffix(".dat").exists():
            qc.update(status="MISSING", reason="no .dat")
            return qc, None
        rec = wfdb.rdrecord(str(base))
        sig = np.asarray(rec.p_signal, dtype=np.float64)
        names = list(rec.sig_name or [])
        if float(rec.fs) != EXPECTED_FS:
            qc.update(status="BAD_FS", reason=f"fs={rec.fs}")
            return qc, None
        try:
            i1 = [names.index(c) for c in RING1]
            i2 = [names.index(c) for c in RING2]
        except ValueError:
            qc.update(status="BAD_CHANNEL_NAMES", reason="F1..F16 not all present")
            return qc, None

        # Bipolar derivation: ring1 electrode minus its vertically aligned ring2 partner
        bip = sig[:, i1] - sig[:, i2]
        if not np.all(np.isfinite(bip)):
            qc.update(status="NONFINITE", reason="NaN/Inf after derivation")
            return qc, None
        if (np.std(bip, axis=0) < 1e-12).any():
            qc.update(status="FLAT_CHANNEL", reason="zero-variance bipolar channel")
            return qc, None

        filt = bandpass_filter(bip, fs=EXPECTED_FS, lowcut=BAND_LOW, highcut=BAND_HIGH,
                               order=BAND_ORDER)
        filt = notch_filter(filt, fs=EXPECTED_FS, notch_freq=NOTCH_HZ, quality_factor=NOTCH_Q)
        windows, bounds = create_sliding_windows(filt, fs=EXPECTED_FS, window_ms=WINDOW_MS,
                                                 overlap_pct=OVERLAP_PCT)
        if len(windows) == 0:
            qc.update(status="TOO_SHORT", reason=f"{sig.shape[0]} samples")
            return qc, None

        meta = np.empty((len(windows), 5), dtype=np.int32)
        feats = np.empty((len(windows), len(FEAT_NAMES)), dtype=np.float32)
        for i, (win, (b0, b1)) in enumerate(zip(windows, bounds)):
            feats[i] = extract_window_features(
                win, fs=EXPECTED_FS, zc_thresh=BIPOLAR_THRESH,
                ssc_thresh=BIPOLAR_THRESH, wamp_thresh=BIPOLAR_THRESH).astype(np.float32)
            meta[i] = (pid, sess, gesture, trial, i)
        qc["n_windows"] = len(windows)
        return qc, (meta, feats)
    except Exception as exc:
        qc.update(status="ERROR", reason=f"{type(exc).__name__}: {exc}")
        qc["traceback"] = traceback.format_exc(limit=2)
        return qc, None


def main():
    jobs = [(s, p, g, t) for s in SESSIONS for p in PARTICIPANTS for g in GESTURES for t in TRIALS]
    print(f"expected records: {len(jobs)}  bipolar channels: {N_BIPOLAR}", flush=True)

    qc_rows, metas, feats = [], [], []
    done = 0
    with ProcessPoolExecutor(max_workers=10) as ex:
        futs = [ex.submit(process_record, j) for j in jobs]
        for fut in as_completed(futs):
            qc, payload = fut.result()
            qc_rows.append(qc)
            if payload is not None:
                metas.append(payload[0])
                feats.append(payload[1])
            done += 1
            if done % 1000 == 0:
                ok = sum(1 for r in qc_rows if r["status"] == "OK")
                print(f"  {done}/{len(jobs)} ok={ok}", flush=True)

    out = ROOT / "data" / "features"
    out.mkdir(parents=True, exist_ok=True)
    qc = pd.DataFrame(qc_rows)
    qc.to_csv(out / "grabmyo_bipolar_qc.csv", index=False)

    meta = np.concatenate(metas, axis=0)
    F = np.concatenate(feats, axis=0)
    df = pd.DataFrame(meta, columns=["participant_id", "session_id", "gesture_id",
                                     "trial_id", "window_idx"])
    df.insert(0, "dataset", "GRABMyo-bipolar")
    df = pd.concat([df, pd.DataFrame(F, columns=FEAT_NAMES)], axis=1)
    df = df.sort_values(["session_id", "participant_id", "gesture_id", "trial_id", "window_idx"])
    df.to_parquet(out / "grabmyo_bipolar_features.parquet", index=False)

    n_ok = int((qc.status == "OK").sum())
    with open(ROOT / "reports" / "bipolar_extraction_report.md", "w", encoding="utf-8") as f:
        f.write("# GRABMyo bipolar feature extraction (8 conventional sensors)\n\n")
        f.write(f"- Derivation: `bipolar_j = F_j - F_(j+8)`, j = 1..8 "
                f"(ring 1 minus vertically aligned ring 2 partner, 2 cm apart)\n")
        f.write(f"- Records expected: **{len(jobs)}**, extracted OK: **{n_ok}**\n")
        f.write(f"- Status breakdown: `{qc.status.value_counts().to_dict()}`\n")
        f.write(f"- Windows: **{len(df)}**\n")
        f.write(f"- Channels: **{N_BIPOLAR}** x 10 features = {len(FEAT_NAMES)}\n\n")
        f.write("## Why this exists\n\n")
        f.write("The primary analysis selects among 16 **monopolar** electrodes. Under that unit a "
                "'k sensor' claim is ambiguous, because an arbitrary subset of monopolar electrodes "
                "need not form deployable bipolar pairs. This representation uses the conventional "
                "sensing unit so the study's conclusions can be checked against what a real armband "
                "could instantiate.\n\n")
        f.write("Bipolar derivation also cancels common-mode content shared by the electrode pair, "
                "so this is a genuinely different representation rather than a coarser view of the "
                "same information.\n")

    print(f"\nstatus={qc.status.value_counts().to_dict()}")
    print(f"windows={len(df)} participants={df.participant_id.nunique()} "
          f"sessions={sorted(df.session_id.unique())} features={len(FEAT_NAMES)}")
    if n_ok != len(jobs):
        print(f"COHORT ASSERTION FAILED: {len(jobs) - n_ok} records failed")
        return 1
    print("COHORT ASSERTION PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
