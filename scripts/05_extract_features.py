import sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
"""
Script 05: Handcrafted Feature Extraction & Caching.
Applies extract_window_features on all preprocessed windows for GRABMyo and DB5.
Creates 160-dimensional feature matrices (16 channels x 10 features) with full metadata.
Saves cached features to data/features/grabmyo_features.parquet and data/features/db5_features.parquet.
"""

import os
import sys
import numpy as np
import pandas as pd
import scipy.io as sio
from pathlib import Path

from src.semg_sparse.preprocessing.filters import bandpass_filter, notch_filter
from src.semg_sparse.segmentation.windowing import create_sliding_windows
from src.semg_sparse.features.handcrafted import extract_window_features, get_feature_mapping

def extract_and_cache_grabmyo():
    print("[1/2] Extracting and caching GRABMyo features...", flush=True)
    meta_path = Path("data/metadata/grabmyo_recordings.parquet")
    if not meta_path.exists():
        print("  Metadata file missing. Waiting for download/metadata scripts...", flush=True)
        return

    df_meta = pd.read_parquet(meta_path)
    raw_dir = Path("data/raw/grabmyo")
    out_dir = Path("data/features")
    out_dir.mkdir(parents=True, exist_ok=True)

    feat_names, ch_indices, feat_types = get_feature_mapping(16)
    
    rows = []
    has_wfdb = False
    try:
        import wfdb
        has_wfdb = True
    except ImportError:
        pass

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

            if signal is None or signal.shape[1] < 16:
                continue

            # Ensure 16 forearm channels
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
            print(f"  Error extracting GRABMyo {rel_p}: {e}", flush=True)

    if rows:
        df_feat = pd.DataFrame(rows)
        out_p = out_dir / "grabmyo_features.parquet"
        df_feat.to_parquet(out_p, index=False)
        print(f"  [OK] Saved GRABMyo features ({len(df_feat)} windows, {df_feat.shape[1]} columns) to {out_p}", flush=True)

def extract_and_cache_db5():
    print("[2/2] Extracting and caching NinaPro DB5 features...", flush=True)
    meta_path = Path("data/metadata/db5_recordings.parquet")
    if not meta_path.exists():
        print("  DB5 metadata missing.", flush=True)
        return

    df_meta = pd.read_parquet(meta_path)
    raw_dir = Path("data/raw/ninapro_db5")
    out_dir = Path("data/features")
    out_dir.mkdir(parents=True, exist_ok=True)

    feat_names, ch_indices, feat_types = get_feature_mapping(16)
    rows = []

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

            emg = mat['emg'][:, :16]
            restimulus = mat.get('restimulus', mat.get('stimulus', None))
            rerepetition = mat.get('rerepetition', mat.get('repetition', None))

            if restimulus is None:
                continue

            restimulus = restimulus.flatten()
            rerepetition = rerepetition.flatten() if rerepetition is not None else np.ones_like(restimulus)

            filtered = bandpass_filter(emg, fs=fs, lowcut=10.0, highcut=90.0, order=4)
            filtered = notch_filter(filtered, fs=fs, notch_freq=50.0, quality_factor=30.0)

            changes = np.where(np.diff(restimulus) != 0)[0] + 1
            segment_starts = np.concatenate(([0], changes))
            segment_ends = np.concatenate((changes, [len(restimulus)]))

            for s_start, s_end in zip(segment_starts, segment_ends):
                g_id = int(restimulus[s_start])
                rep_id = int(rerepetition[s_start])
                
                if g_id == 0: # Exclude rest for primary task
                    continue

                sub_seg = filtered[s_start:s_end, :]
                if len(sub_seg) < int(0.25 * fs):
                    continue

                windows, bounds = create_sliding_windows(sub_seg, fs=fs, window_ms=250.0, overlap_pct=50.0)
                for w_idx, (win, (b_start, b_end)) in enumerate(zip(windows, bounds)):
                    feat_vec = extract_window_features(win, fs=fs)
                    entry = {
                        "dataset": "NinaPro_DB5",
                        "participant_id": sub_id,
                        "session_id": 1,
                        "exercise_id": ex_id,
                        "gesture_id": g_id,
                        "repetition_id": rep_id,
                        "window_idx": w_idx,
                        "start_sample": s_start + b_start,
                        "end_sample": s_start + b_end
                    }
                    for fn, val in zip(feat_names, feat_vec):
                        entry[fn] = val
                    rows.append(entry)

        except Exception as e:
            print(f"  Error extracting DB5 {rel_p}: {e}", flush=True)

    if rows:
        df_feat = pd.DataFrame(rows)
        out_p = out_dir / "db5_features.parquet"
        df_feat.to_parquet(out_p, index=False)
        print(f"  [OK] Saved DB5 features ({len(df_feat)} windows) to {out_p}", flush=True)

if __name__ == "__main__":
    extract_and_cache_grabmyo()
    extract_and_cache_db5()
