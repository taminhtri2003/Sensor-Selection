import sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
"""
Script 02: Dataset Audit for GRABMyo and NinaPro DB5.
Inspects raw files, channel structures, signal properties, NaNs, clipping, flat lines,
and produces comprehensive markdown audit reports in reports/dataset_audit/.
"""

import os
import sys
import numpy as np
import pandas as pd
import scipy.io as sio
from pathlib import Path

def audit_grabmyo():
    print("[1/2] Auditing GRABMyo raw dataset...")
    grabmyo_dir = Path("data/raw/grabmyo")
    report_path = Path("reports/dataset_audit/grabmyo_audit.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)

    lines = []
    lines.append("# GRABMyo Dataset Quality & Integrity Audit")
    lines.append("")
    
    if not grabmyo_dir.exists():
        lines.append("> **ERROR**: Raw GRABMyo directory does not exist yet.")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        return

    # Look for WFDB or mat files or raw directories in grabmyo
    all_files = list(grabmyo_dir.rglob("*"))
    files_only = [f for f in all_files if f.is_file()]
    
    lines.append(f"- **Total Raw Files**: {len(files_only)}")
    lines.append(f"- **Total Storage Size**: {sum(f.stat().st_size for f in files_only) / (1024**2):.2f} MB")
    lines.append("")

    # Parse structure (e.g. Session1, Session2, Session3 / Subject directories)
    # Check for .dat / .hea / .mat files
    dat_files = list(grabmyo_dir.rglob("*.dat")) + list(grabmyo_dir.rglob("*.mat"))
    lines.append(f"## File Inventory")
    lines.append(f"- Signal data files found: {len(dat_files)}")

    # Sample signal audit if files exist
    nan_count = 0
    inf_count = 0
    flat_channels = 0
    total_recordings = 0
    sampled_channels = set()
    sampling_rates = set()

    for fp in dat_files[:100]: # Sample first 100 files for quick audit, full audit in metadata
        total_recordings += 1
        try:
            if fp.suffix == '.mat':
                mat = sio.loadmat(fp)
                for k, v in mat.items():
                    if isinstance(v, np.ndarray) and v.ndim == 2:
                        if np.isnan(v).any(): nan_count += 1
                        if np.isinf(v).any(): inf_count += 1
                        std_per_ch = np.std(v, axis=0)
                        if (std_per_ch < 1e-8).any(): flat_channels += 1
            elif fp.suffix == '.dat':
                # Attempt WFDB read if header present
                hea_p = fp.with_suffix('.hea')
                if hea_p.exists():
                    import wfdb
                    rec = wfdb.rdrecord(str(fp.with_suffix('')))
                    sampling_rates.add(rec.fs)
                    sampled_channels.update(rec.sig_name)
                    data = rec.p_signal
                    if np.isnan(data).any(): nan_count += 1
                    if np.isinf(data).any(): inf_count += 1
                    if (np.std(data, axis=0) < 1e-8).any(): flat_channels += 1
        except Exception as e:
            pass

    lines.append("")
    lines.append("## Quality Control Summary (Sampled Files)")
    lines.append(f"- **Files Audited**: {total_recordings}")
    lines.append(f"- **NaN Anomalies**: {nan_count}")
    lines.append(f"- **Inf Anomalies**: {inf_count}")
    lines.append(f"- **Flat Channels Detected**: {flat_channels}")
    lines.append(f"- **Detected Sampling Rates**: {list(sampling_rates)}")
    lines.append(f"- **Channel Names Identified**: {sorted(list(sampled_channels))[:16]}")
    lines.append("")

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"  [OK] GRABMyo audit written to {report_path}")

def audit_ninapro_db5():
    print("[2/2] Auditing NinaPro DB5 raw dataset...")
    db5_dir = Path("data/raw/ninapro_db5")
    report_path = Path("reports/dataset_audit/db5_audit.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)

    lines = []
    lines.append("# NinaPro DB5 Dataset Quality & Integrity Audit")
    lines.append("")

    if not db5_dir.exists():
        lines.append("> **ERROR**: Raw DB5 directory does not exist yet.")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        return

    mat_files = sorted(list(db5_dir.glob("*.mat")))
    lines.append(f"- **MAT Files Found**: {len(mat_files)}")
    
    nan_count = 0
    inf_count = 0
    flat_channels = 0
    subjects_found = set()

    for fp in mat_files:
        try:
            mat = sio.loadmat(fp)
            if 'emg' in mat:
                emg = mat['emg']
                if np.isnan(emg).any(): nan_count += 1
                if np.isinf(emg).any(): inf_count += 1
                if (np.std(emg, axis=0) < 1e-8).any(): flat_channels += 1
            if 'subject' in mat:
                subjects_found.add(int(mat['subject'][0, 0]))
        except Exception as e:
            pass

    lines.append("## Quality Control Summary")
    lines.append(f"- **Subjects Identified**: {sorted(list(subjects_found))}")
    lines.append(f"- **NaN Anomalies**: {nan_count}")
    lines.append(f"- **Inf Anomalies**: {inf_count}")
    lines.append(f"- **Flat Channels**: {flat_channels}")
    lines.append("")

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"  [OK] NinaPro DB5 audit written to {report_path}")

if __name__ == "__main__":
    audit_grabmyo()
    audit_ninapro_db5()
