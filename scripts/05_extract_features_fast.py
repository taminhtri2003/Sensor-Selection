import sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

"""
Script 05 (Fast Parallel): Handcrafted Feature Extraction & Caching.
Multi-threaded/multi-process extractor across 12 CPU threads.
"""

import os
import sys
import numpy as np
import pandas as pd
import scipy.io as sio
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

from src.semg_sparse.preprocessing.filters import bandpass_filter, notch_filter
from src.semg_sparse.segmentation.windowing import create_sliding_windows
from src.semg_sparse.features.handcrafted import extract_window_features, get_feature_mapping

def process_single_recording(row_dict):
    rel_p = row_dict['source_file']
    raw_dir = Path("data/raw/grabmyo")
    full_p = raw_dir / rel_p
    fs = float(row_dict['sampling_rate'])
    pid = int(row_dict['participant_id'])
    sid = int(row_dict['session_id'])
    gid = int(row_dict['gesture_id'])
    tid = int(row_dict['trial_id'])

    feat_names, _, _ = get_feature_mapping(16)
    rows = []

    try:
        signal = None
        if full_p.suffix == '.hea' or full_p.with_suffix('.hea').exists():
            rec_base = str(full_p.with_suffix(''))
            import wfdb
            if Path(rec_base + '.dat').exists():
                rec = wfdb.rdrecord(rec_base)
                signal = rec.p_signal

        if signal is None or signal.shape[1] < 16:
            return rows

        signal = signal[:, :16]
        filtered = bandpass_filter(signal, fs=fs, lowcut=20.0, highcut=450.0, order=4)
        filtered = notch_filter(filtered, fs=fs, notch_freq=50.0, quality_factor=30.0)

        windows, bounds = create_sliding_windows(filtered, fs=fs, window_ms=250.0, overlap_pct=50.0)

        for w_idx, (win, (b_start, b_end)) in enumerate(zip(windows, bounds)):
            feat_vec = extract_window_features(win, fs=fs)
            entry = {
                "dataset": "GRABMyo",
                "participant_id": pid,
                "session_id": sid,
                "gesture_id": gid,
                "trial_id": tid,
                "window_idx": w_idx,
                "start_sample": b_start,
                "end_sample": b_end
            }
            for fn, val in zip(feat_names, feat_vec):
                entry[fn] = val
            rows.append(entry)

    except Exception as e:
        pass

    return rows

def extract_and_cache_grabmyo_fast():
    print("[1/2] Parallel Feature Extraction across 12 CPU Workers...", flush=True)
    meta_path = Path("data/metadata/grabmyo_recordings.parquet")
    if not meta_path.exists():
        print("  [ERROR] Metadata missing.", flush=True)
        return

    df_meta = pd.read_parquet(meta_path)
    out_dir = Path("data/features")
    out_dir.mkdir(parents=True, exist_ok=True)

    records = df_meta.to_dict('records')
    all_rows = []

    with ProcessPoolExecutor(max_workers=12) as executor:
        futures = [executor.submit(process_single_recording, r) for r in records]
        completed = 0
        for future in as_completed(futures):
            res = future.result()
            if res:
                all_rows.extend(res)
            completed += 1
            if completed % 200 == 0:
                print(f"  Processed {completed}/{len(records)} recordings...", flush=True)

    if all_rows:
        df_feat = pd.DataFrame(all_rows)
        out_p = out_dir / "grabmyo_features.parquet"
        df_feat.to_parquet(out_p, index=False)
        print(f"  [OK] Saved {len(df_feat)} windows to {out_p}", flush=True)

if __name__ == "__main__":
    extract_and_cache_grabmyo_fast()
