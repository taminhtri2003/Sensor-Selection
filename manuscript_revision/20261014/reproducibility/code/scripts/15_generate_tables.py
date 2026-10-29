"""Script 15: Publication Table Generator.

Generates LaTeX and CSV tables (Tables 1-8) for manuscript insertion directly from result files.
Saves tables to artifacts/tables/ and manuscript/tables/.
"""

import os
import sys
import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

TAB_DIR = ROOT / "artifacts" / "tables"
TAB_DIR.mkdir(parents=True, exist_ok=True)
TEX_TAB_DIR = ROOT / "manuscript" / "tables"
TEX_TAB_DIR.mkdir(parents=True, exist_ok=True)

def generate_table1_datasets():
    """Table 1: Dataset Characteristics."""
    data = [
        {
            "Dataset": "GRABMyo v1.1.0",
            "Role": "Primary Evidence",
            "Participants": 43,
            "Sessions": 3,
            "Channels": 16,
            "Sampling Frequency (Hz)": 2048,
            "Gestures": "16 active",
            "Sensor Setup": "Dual concentric 8-channel rings (monopolar)"
        },
        {
            "Dataset": "NinaPro DB5",
            "Role": "External Replication",
            "Participants": 10,
            "Sessions": 1,
            "Channels": 16,
            "Sampling Frequency (Hz)": 200,
            "Gestures": "12 active",
            "Sensor Setup": "Dual 8-channel Myo armbands"
        }
    ]
    df = pd.DataFrame(data)
    df.to_csv(TAB_DIR / "table1_datasets.csv", index=False)
    tex = df.to_latex(index=False, caption="Characteristics of Primary Benchmark and External Replication Datasets", label="tab:datasets")
    for d in [TAB_DIR, TEX_TAB_DIR]:
        with open(d / "table1_datasets.tex", "w", encoding="utf-8") as f:
            f.write(tex)
    print("  [OK] Generated Table 1 (Datasets)", flush=True)

def generate_table2_full_channel():
    """Table 2: Full-Channel Subject-Independent Model Performance."""
    xgb_p = ROOT / "artifacts" / "metrics" / "loso_full_channel_subject_metrics_xgb.csv"
    svmrf_p = ROOT / "artifacts" / "metrics" / "loso_full_channel_subject_metrics_svmrf.csv"
    if not xgb_p.exists() or not svmrf_p.exists(): return

    df_xgb = pd.read_csv(xgb_p)
    df_svmrf = pd.read_csv(svmrf_p)
    df = pd.concat([df_xgb, df_svmrf], ignore_index=True)

    summary = df.groupby('model').agg(
        mean_macro_f1=('macro_f1', 'mean'),
        std_macro_f1=('macro_f1', 'std'),
        min_macro_f1=('macro_f1', 'min'),
        max_macro_f1=('macro_f1', 'max'),
        mean_accuracy=('accuracy', 'mean')
    ).reset_index()

    summary.to_csv(TAB_DIR / "table2_full_channel_performance.csv", index=False)
    tex = summary.to_latex(index=False, float_format="%.3f", caption="Full 16-Channel LOSO Baseline Performance ($N=43$)", label="tab:full_channel")
    for d in [TAB_DIR, TEX_TAB_DIR]:
        with open(d / "table2_full_channel_performance.tex", "w", encoding="utf-8") as f:
            f.write(tex)
    print("  [OK] Generated Table 2 (Full Channel)", flush=True)

def generate_table3_sparse_perf():
    """Table 3: Sparse-Channel Performance and Non-Inferiority Decisions."""
    curve_p = ROOT / "artifacts" / "metrics" / "sparse_curve_subject_metrics.csv"
    noninf_p = ROOT / "artifacts" / "statistics" / "non_inferiority_by_k.csv"
    if not curve_p.exists(): return

    df_curve = pd.read_csv(curve_p)
    df_primary = df_curve[np.isclose(df_curve['lambda'], 0.5)]

    summary = df_primary.groupby('channels_k').agg(
        mean_macro_f1=('macro_f1', 'mean'),
        std_macro_f1=('macro_f1', 'std')
    ).reset_index().rename(columns={'channels_k': 'k'})

    if noninf_p.exists():
        df_ni = pd.read_csv(noninf_p)
        df_ni_02 = df_ni[(np.isclose(df_ni['lambda'], 0.5)) & (np.isclose(df_ni['margin'], 0.02))]
        k_col = 'k' if 'k' in df_ni_02.columns else 'channels_k'
        summary = summary.merge(df_ni_02[[k_col, 'mean_diff', 'lcb_95', 'ucb_95', 'is_non_inferior']].rename(columns={k_col: 'k'}), on='k', how='left')

    summary.sort_values('k', ascending=False, inplace=True)
    summary.to_csv(TAB_DIR / "table3_sparse_performance.csv", index=False)
    tex = summary.to_latex(index=False, float_format="%.4f", caption="Sparse Sensor Configuration Performance and Non-Inferiority Decisions (\\delta=0.02)", label="tab:sparse_perf")
    for d in [TAB_DIR, TEX_TAB_DIR]:
        with open(d / "table3_sparse_performance.tex", "w", encoding="utf-8") as f:
            f.write(tex)
    print("  [OK] Generated Table 3 (Sparse Performance)", flush=True)

def generate_table4_stability():
    """Table 4: Attribution Stability Across Tiers."""
    stab_p = ROOT / "artifacts" / "stability" / "stability_summary.csv"
    if not stab_p.exists(): return
    df_stab = pd.read_csv(stab_p)
    df_stab.to_csv(TAB_DIR / "table4_stability_summary.csv", index=False)
    tex = df_stab.to_latex(index=False, float_format="%.3f", caption="Attribution Stability Across Evaluation Tiers", label="tab:stability")
    for d in [TAB_DIR, TEX_TAB_DIR]:
        with open(d / "table4_stability_summary.tex", "w", encoding="utf-8") as f:
            f.write(tex)
    print("  [OK] Generated Table 4 (Stability Summary)", flush=True)

def run_all_tables():
    print("=" * 70, flush=True)
    print("GENERATING ALL PUBLICATION TABLES", flush=True)
    print("=" * 70, flush=True)
    generate_table1_datasets()
    generate_table2_full_channel()
    generate_table3_sparse_perf()
    generate_table4_stability()
    print("=" * 70, flush=True)

if __name__ == "__main__":
    run_all_tables()
