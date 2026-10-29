import sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
"""
Script 03: Metadata Builder.
Scans downloaded raw files for GRABMyo and NinaPro DB5, builds structured recording catalogs,
parses participant IDs, session IDs, gesture IDs, channel counts, and sample counts.
Saves metadata to data/metadata/grabmyo_recordings.parquet and data/metadata/db5_recordings.parquet.
"""

import os
import sys
import re
from pathlib import Path
import numpy as np
import pandas as pd
import scipy.io as sio

def build_grabmyo_metadata():
    print("[1/2] Building GRABMyo recordings metadata...", flush=True)
    grabmyo_dir = Path("data/raw/grabmyo")
    records = []

    # Look for files matching SessionX / SubjectX pattern
    # GRABMyo files can be .dat/.hea WFDB files or .mat files
    hea_files = list(grabmyo_dir.rglob("*.hea"))
    mat_files = list(grabmyo_dir.rglob("*.mat"))
    
    if hea_files:
        import wfdb
        for hea_p in sorted(hea_files):
            try:
                rec_base = str(hea_p.with_suffix(''))
                header = wfdb.rdheader(rec_base)
                rel_path = hea_p.relative_to(grabmyo_dir).as_posix()
                
                # Extract session and subject from path
                # e.g., Session1/session1_participant1_gesture1_trial1.hea
                m_sub = re.search(r"participant[_\s]?(\d+)", rel_path, re.IGNORECASE) or re.search(r"sub[_\s]?(\d+)", rel_path, re.IGNORECASE) or re.search(r"p(\d+)", rel_path, re.IGNORECASE)
                m_sess = re.search(r"session[_\s]?(\d+)", rel_path, re.IGNORECASE) or re.search(r"s(\d+)", rel_path, re.IGNORECASE)
                m_gest = re.search(r"gesture[_\s]?(\d+)", rel_path, re.IGNORECASE) or re.search(r"g(\d+)", rel_path, re.IGNORECASE)
                m_trial = re.search(r"trial[_\s]?(\d+)", rel_path, re.IGNORECASE) or re.search(r"t(\d+)", rel_path, re.IGNORECASE)
                
                pid = int(m_sub.group(1)) if m_sub else 1
                sid = int(m_sess.group(1)) if m_sess else 1
                gid = int(m_gest.group(1)) if m_gest else 1
                tid = int(m_trial.group(1)) if m_trial else 1

                records.append({
                    "dataset": "GRABMyo",
                    "participant_id": pid,
                    "session_id": sid,
                    "gesture_id": gid,
                    "trial_id": tid,
                    "source_file": rel_path,
                    "sampling_rate": header.fs,
                    "n_samples": header.sig_len,
                    "n_channels": header.n_sig,
                    "channel_names": ",".join(header.sig_name),
                    "qc_flag": "PASS"
                })
            except Exception as e:
                print(f"  Error reading {hea_p}: {e}", flush=True)

    elif mat_files:
        for mat_p in sorted(mat_files):
            try:
                rel_path = mat_p.relative_to(grabmyo_dir).as_posix()
                m_sub = re.search(r"participant[_\s]?(\d+)", rel_path, re.IGNORECASE) or re.search(r"sub[_\s]?(\d+)", rel_path, re.IGNORECASE)
                m_sess = re.search(r"session[_\s]?(\d+)", rel_path, re.IGNORECASE)
                m_gest = re.search(r"gesture[_\s]?(\d+)", rel_path, re.IGNORECASE)
                m_trial = re.search(r"trial[_\s]?(\d+)", rel_path, re.IGNORECASE)
                
                pid = int(m_sub.group(1)) if m_sub else 1
                sid = int(m_sess.group(1)) if m_sess else 1
                gid = int(m_gest.group(1)) if m_gest else 1
                tid = int(m_trial.group(1)) if m_trial else 1

                mat = sio.loadmat(mat_p)
                n_samples, n_channels = 0, 16
                for k, v in mat.items():
                    if isinstance(v, np.ndarray) and v.ndim == 2:
                        n_samples, n_channels = v.shape

                records.append({
                    "dataset": "GRABMyo",
                    "participant_id": pid,
                    "session_id": sid,
                    "gesture_id": gid,
                    "trial_id": tid,
                    "source_file": rel_path,
                    "sampling_rate": 2048,
                    "n_samples": n_samples,
                    "n_channels": n_channels,
                    "channel_names": ",".join([f"ch_{i+1}" for i in range(n_channels)]),
                    "qc_flag": "PASS"
                })
            except Exception as e:
                print(f"  Error reading {mat_p}: {e}", flush=True)

    out_dir = Path("data/metadata")
    out_dir.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(records)
    if not df.empty:
        df.to_parquet(out_dir / "grabmyo_recordings.parquet", index=False)
        df.to_csv(out_dir / "grabmyo_recordings.csv", index=False)
        print(f"  [OK] Saved GRABMyo metadata: {len(df)} recordings.", flush=True)
    else:
        print("  [WARNING] No GRABMyo recordings found to build metadata.", flush=True)

def build_db5_metadata():
    print("[2/2] Building NinaPro DB5 recordings metadata...", flush=True)
    db5_dir = Path("data/raw/ninapro_db5")
    records = []

    mat_files = sorted(list(db5_dir.glob("*.mat"))) + sorted(list(db5_dir.rglob("*.mat")))
    mat_files = list(dict.fromkeys(mat_files))

    for mat_p in mat_files:
        try:
            rel_path = mat_p.relative_to(db5_dir).as_posix()
            mat = sio.loadmat(mat_p)
            
            sub_id = int(mat['subject'][0, 0]) if 'subject' in mat else 1
            ex_id = int(mat['exercise'][0, 0]) if 'exercise' in mat else 1
            fs = int(mat['frequency'][0, 0]) if 'frequency' in mat else 200
            
            emg = mat.get('emg', None)
            if emg is not None:
                n_samples, n_channels = emg.shape
            else:
                n_samples, n_channels = 0, 16

            records.append({
                "dataset": "NinaPro_DB5",
                "participant_id": sub_id,
                "session_id": 1,
                "exercise_id": ex_id,
                "source_file": rel_path,
                "sampling_rate": fs,
                "n_samples": n_samples,
                "n_channels": n_channels,
                "channel_names": ",".join([f"myo_{i+1}" for i in range(n_channels)]),
                "qc_flag": "PASS"
            })
        except Exception as e:
            print(f"  Error reading DB5 {mat_p}: {e}", flush=True)

    out_dir = Path("data/metadata")
    out_dir.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(records)
    if not df.empty:
        df.to_parquet(out_dir / "db5_recordings.parquet", index=False)
        df.to_csv(out_dir / "db5_recordings.csv", index=False)
        print(f"  [OK] Saved DB5 metadata: {len(df)} recordings.", flush=True)
    else:
        print("  [WARNING] No DB5 recordings found to build metadata.", flush=True)

if __name__ == "__main__":
    build_grabmyo_metadata()
    build_db5_metadata()
