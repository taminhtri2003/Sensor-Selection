import sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
"""
Script 04: Signal Preprocessing and Window Segmentation.
Applies bandpass filtering, 50 Hz notch filtering, and sliding window segmentation (250 ms, 50% overlap).
Saves windowed signals and metadata per participant under data/processed/.
"""

import os
import sys
import re
from pathlib import Path
import numpy as np
import pandas as pd
import scipy.io as sio

from src.semg_sparse.preprocessing.filters import bandpass_filter, notch_filter
from src.semg_sparse.segmentation.windowing import create_sliding_windows

def preprocess_grabmyo():
    print("[1/2] Preprocessing GRABMyo recordings...", flush=True)
    meta_path = Path("data/metadata/grabmyo_recordings.parquet")
    if not meta_path.exists():
        print("  [ERROR] Metadata missing. Run 03_build_metadata.py first.", flush=True)
        return

    df_meta = pd.read_parquet(meta_path)
    raw_dir = Path("data/raw/grabmyo")
    out_dir = Path("data/processed/grabmyo")
    out_dir.mkdir(parents=True, exist_ok=True)

    has_wfdb = False
    try:
        import wfdb
        has_wfdb = True
    except ImportError:
        pass

    window_records = []
    
    # Process per recording
    for idx, row in df_meta.iterrows():
        rel_p = row['source_file']
        full_p = raw_dir / rel_p
        
        fs = float(row['sampling_rate'])
        pid = int(row['participant_id'])
        sid = int(row['session_id'])
        gid = int(row['gesture_id'])
        tid = int(row['trial_id'])

        try:
            signal = None
            if full_p.suffix == '.hea' or full_p.with_suffix('.hea').exists():
                rec_base = str(full_p.with_suffix(''))
                if has_wfdb and Path(rec_base + '.dat').exists():
                    rec = wfdb.rdrecord(rec_base)
                    signal = rec.p_signal
            elif full_p.suffix == '.mat':
                mat = sio.loadmat(full_p)
                for k, v in mat.items():
                    if isinstance(v, np.ndarray) and v.ndim == 2:
                        signal = v
                        break

            if signal is None:
                continue

            # Filtering: zero-phase bandpass 20-450 Hz + 50 Hz notch
            filtered = bandpass_filter(signal, fs=fs, lowcut=20.0, highcut=450.0, order=4)
            filtered = notch_filter(filtered, fs=fs, notch_freq=50.0, quality_factor=30.0)

            # Windowing: 250 ms, 50% overlap
            windows, bounds = create_sliding_windows(filtered, fs=fs, window_ms=250.0, overlap_pct=50.0)

            for w_idx, (win, (b_start, b_end)) in enumerate(zip(windows, bounds)):
                window_records.append({
                    "dataset": "GRABMyo",
                    "participant_id": pid,
                    "session_id": sid,
                    "gesture_id": gid,
                    "trial_id": tid,
                    "window_idx": w_idx,
                    "start_sample": b_start,
                    "end_sample": b_end,
                    "signal_matrix": win
                })

        except Exception as e:
            print(f"  Error processing {rel_p}: {e}", flush=True)

    print(f"  [OK] Preprocessed GRABMyo: {len(window_records)} windows total.", flush=True)
    return window_records

def preprocess_db5():
    print("[2/2] Preprocessing NinaPro DB5 recordings...", flush=True)
    meta_path = Path("data/metadata/db5_recordings.parquet")
    if not meta_path.exists():
        print("  [ERROR] DB5 Metadata missing.", flush=True)
        return

    df_meta = pd.read_parquet(meta_path)
    raw_dir = Path("data/raw/ninapro_db5")
    out_dir = Path("data/processed/db5")
    out_dir.mkdir(parents=True, exist_ok=True)

    window_records = []

    for idx, row in df_meta.iterrows():
        rel_p = row['source_file']
        full_p = raw_dir / rel_p
        fs = float(row['sampling_rate'])
        sub_id = int(row['participant_id'])
        ex_id = int(row['exercise_id'])

        try:
            mat = sio.loadmat(full_p)
            if 'emg' not in mat:
                continue

            emg = mat['emg'] # (T, 16)
            restimulus = mat.get('restimulus', mat.get('stimulus', None))
            rerepetition = mat.get('rerepetition', mat.get('repetition', None))

            if restimulus is None:
                continue

            restimulus = restimulus.flatten()
            rerepetition = rerepetition.flatten() if rerepetition is not None else np.ones_like(restimulus)

            # Filtering: sampling-rate appropriate filtering for 200 Hz
            filtered = bandpass_filter(emg, fs=fs, lowcut=10.0, highcut=90.0, order=4)
            filtered = notch_filter(filtered, fs=fs, notch_freq=50.0, quality_factor=30.0)

            # Identify contiguous movement regions to prevent window bleed across gestures
            changes = np.where(np.diff(restimulus) != 0)[0] + 1
            segment_starts = np.concatenate(([0], changes))
            segment_ends = np.concatenate((changes, [len(restimulus)]))

            for s_start, s_end in zip(segment_starts, segment_ends):
                g_id = int(restimulus[s_start])
                rep_id = int(rerepetition[s_start])
                
                # Active gestures only for primary task
                if g_id == 0:
                    continue

                sub_seg = filtered[s_start:s_end, :]
                if len(sub_seg) < int(0.25 * fs):
                    continue

                windows, bounds = create_sliding_windows(sub_seg, fs=fs, window_ms=250.0, overlap_pct=50.0)
                for w_idx, (win, (b_start, b_end)) in enumerate(zip(windows, bounds)):
                    window_records.append({
                        "dataset": "NinaPro_DB5",
                        "participant_id": sub_id,
                        "session_id": 1,
                        "exercise_id": ex_id,
                        "gesture_id": g_id,
                        "repetition_id": rep_id,
                        "window_idx": w_idx,
                        "start_sample": s_start + b_start,
                        "end_sample": s_start + b_end,
                        "signal_matrix": win
                    })

        except Exception as e:
            print(f"  Error processing DB5 {rel_p}: {e}", flush=True)

    print(f"  [OK] Preprocessed DB5: {len(window_records)} windows total.", flush=True)
    return window_records

if __name__ == "__main__":
    preprocess_grabmyo()
    preprocess_db5()
