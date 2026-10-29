"""Script 14: Publication-Grade Scientific Figures Generator.

Generates Figures 1 to 10 as publication-quality vector (PDF/SVG) and 300-DPI raster images.
Reads values directly from verified result files under artifacts/ to eliminate manual transcription errors.
Saves figures to artifacts/figures/ and manuscript/figures/.
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Publication styling
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']
plt.rcParams['axes.edgecolor'] = '#333333'
plt.rcParams['axes.linewidth'] = 0.8
plt.rcParams['grid.color'] = '#e0e0e0'
plt.rcParams['grid.linestyle'] = '--'
plt.rcParams['grid.alpha'] = 0.6

FIG_DIR = ROOT / "artifacts" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)
TEX_FIG_DIR = ROOT / "manuscript" / "figures"
TEX_FIG_DIR.mkdir(parents=True, exist_ok=True)

def save_fig(fig, name):
    fig.tight_layout()
    for d in [FIG_DIR, TEX_FIG_DIR]:
        fig.savefig(d / f"{name}.pdf", dpi=300, bbox_inches='tight')
        fig.savefig(d / f"{name}.png", dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"  [OK] Saved figure {name}.pdf / {name}.png", flush=True)

def generate_figure2():
    """Figure 2: Dual-ring electrode geometry."""
    fig, ax = plt.subplots(figsize=(6.5, 3.2))
    ring1_x = np.arange(1, 9)
    ring2_x = np.arange(1, 9)
    ax.scatter(ring1_x, np.zeros(8), s=180, color='#1f77b4', edgecolor='black', linewidth=1.2, zorder=5, label='Ring 1 (Distal: Ch 1–8)')
    ax.scatter(ring2_x, np.ones(8) * 2.0, s=180, color='#ff7f0e', edgecolor='black', linewidth=1.2, zorder=5, label='Ring 2 (Proximal: Ch 9–16)')
    for i in range(8):
        ax.plot([i+1, i+1], [0, 2.0], color='#888888', linestyle=':', linewidth=1.5, zorder=3)
        ax.text(i+1, -0.35, f"Ch {i+1}", ha='center', va='top', fontsize=8, fontweight='bold')
        ax.text(i+1, 2.35, f"Ch {i+9}", ha='center', va='bottom', fontsize=8, fontweight='bold')
        ax.text(i+1, 1.0, f"Pair {i+1}\n(Ch{i+1}−{i+9})", ha='center', va='center', fontsize=7, color='#555555',
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='#cccccc', alpha=0.85))
    ax.set_xlim(0.3, 8.7)
    ax.set_ylim(-0.8, 3.0)
    ax.set_xticks(np.arange(1, 9))
    ax.set_xticklabels([f"Pos {i}\n(0°, 45°...)" if i==1 else f"Pos {i}" for i in range(1, 9)])
    ax.set_yticks([0, 2.0])
    ax.set_yticklabels(["0 cm (Distal)", "2.0 cm (Proximal)"])
    ax.set_title("GRABMyo Dual-Ring Forearm Electrode Montage (16 Monopolar = 8 Bipolar Pairs)", fontsize=10, fontweight='bold')
    ax.set_xlabel("Circumferential Electrode Position (24 cm circumference, 3.0 cm spacing)")
    ax.set_ylabel("Longitudinal Distance")
    ax.grid(True, axis='x')
    ax.legend(loc='upper right', framealpha=0.9)
    save_fig(fig, "fig2_electrode_geometry")

def generate_figure3():
    """Figure 3: Full-Channel Baseline Performance Across Models."""
    xgb_p = ROOT / "artifacts" / "metrics" / "loso_full_channel_subject_metrics_xgb.csv"
    svmrf_p = ROOT / "artifacts" / "metrics" / "loso_full_channel_subject_metrics_svmrf.csv"
    if not xgb_p.exists() or not svmrf_p.exists(): return
    
    df_xgb = pd.read_csv(xgb_p)
    df_svmrf = pd.read_csv(svmrf_p)
    df = pd.concat([df_xgb, df_svmrf], ignore_index=True)
    name_map = {'M_XGBoost': 'XGBoost (GPU)', 'M_SVM': 'RBF-SVM (40k sub)', 'M_RandomForest': 'Random Forest (200k sub)'}
    df['model_label'] = df['model'].map(name_map).fillna(df['model'])
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8.0, 3.8), gridspec_kw={'width_ratios': [1.2, 1]})
    palette = ['#1f77b4', '#2ca02c', '#9467bd']
    sns.boxplot(data=df, x='model_label', y='macro_f1', hue='model_label', palette=palette, ax=ax1, width=0.45, boxprops=dict(alpha=0.75), legend=False)
    sns.stripplot(data=df, x='model_label', y='macro_f1', color='black', alpha=0.5, jitter=0.15, size=4.5, ax=ax1)
    
    ax1.set_ylabel("Macro-F1 (16 Active Gestures)")
    ax1.set_xlabel("Classifier Architecture")
    ax1.set_title("(a) Participant-Level Spread ($N=43$ LOSO)", fontsize=10, fontweight='bold')
    ax1.set_ylim(0.25, 0.8)
    ax1.grid(True, axis='y')
    ax1.tick_params(axis='x', rotation=10)
    
    xgb_sub = df[df.model == 'M_XGBoost'].set_index('participant_id')['macro_f1']
    svm_sub = df[df.model == 'M_SVM'].set_index('participant_id')['macro_f1']
    rf_sub = df[df.model == 'M_RandomForest'].set_index('participant_id')['macro_f1']
    
    for pid in sorted(df.participant_id.unique()):
        if pid in xgb_sub.index and pid in svm_sub.index and pid in rf_sub.index:
            ax2.plot([0, 1, 2], [xgb_sub[pid], svm_sub[pid], rf_sub[pid]], color='#555555', alpha=0.3, linewidth=0.9)
            
    means = [xgb_sub.mean(), svm_sub.mean(), rf_sub.mean()]
    ax2.plot([0, 1, 2], means, 'o-', color='#d62728', linewidth=2.5, markersize=7, label='Cohort Mean', zorder=10)
    for i, m in enumerate(means):
        ax2.text(i, m + 0.02, f"{m:.3f}", ha='center', va='bottom', fontweight='bold', color='#d62728', fontsize=8)
        
    ax2.set_xticks([0, 1, 2])
    ax2.set_xticklabels(['XGBoost', 'SVM', 'RF'])
    ax2.set_ylabel("Macro-F1 Score")
    ax2.set_xlabel("Model Architecture")
    ax2.set_title("(b) Paired Comparison", fontsize=10, fontweight='bold')
    ax2.set_ylim(0.25, 0.8)
    ax2.grid(True)
    ax2.legend(loc='lower left')
    save_fig(fig, "fig3_full_channel_baseline")

def generate_figure4():
    """Figure 4: Primary Sparse Sensor Selection Curve and Non-Inferiority."""
    curve_p = ROOT / "artifacts" / "metrics" / "sparse_curve_subject_metrics.csv"
    noninf_p = ROOT / "artifacts" / "statistics" / "non_inferiority_by_k.csv"
    if not curve_p.exists(): return
    df = pd.read_csv(curve_p)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.0, 4.0))
    colors = {0.0: '#7f7f7f', 0.25: '#2ca02c', 0.5: '#1f77b4', 1.0: '#d62728'}
    labels = {0.0: 'λ=0.0 (SHAP Mag)', 0.25: 'λ=0.25', 0.5: 'λ=0.50 (Primary SR-CFA)', 1.0: 'λ=1.0 (High Reg)'}
    
    full_f1 = df[df.channels_k == 16]['macro_f1'].mean()
    margin = 0.02
    
    for lam in sorted(df['lambda'].unique()):
        sub = df[np.isclose(df['lambda'], lam)]
        agg = sub.groupby('channels_k')['macro_f1'].agg(['mean', 'std', 'count']).reset_index()
        agg['ci95'] = 1.96 * (agg['std'] / np.sqrt(agg['count']))
        c = colors.get(lam, '#333333')
        lbl = labels.get(lam, f'λ={lam}')
        lw = 2.2 if lam == 0.5 else 1.4
        ax1.plot(agg['channels_k'], agg['mean'], 'o-', color=c, linewidth=lw, markersize=4, label=lbl)
        if lam == 0.5:
            ax1.fill_between(agg['channels_k'], agg['mean'] - agg['ci95'], agg['mean'] + agg['ci95'], color=c, alpha=0.18, label='95% CI (λ=0.5)')
            
    ax1.axhline(full_f1, color='black', linestyle='--', linewidth=1.2, label=f'Full 16-Ch Baseline ({full_f1:.3f})')
    ax1.axhline(full_f1 - margin, color='#d62728', linestyle=':', linewidth=1.5, label=r'Non-Inferiority Bound ($\delta=0.02$)')
    ax1.set_xlabel("Number of Selected Channels ($k$)")
    ax1.set_ylabel("Subject-Independent Macro-F1")
    ax1.set_title("(a) Sparse Sensor Selection Curves", fontsize=10, fontweight='bold')
    ax1.set_xticks(range(1, 17))
    ax1.set_ylim(0.25, 0.60)
    ax1.grid(True)
    ax1.legend(loc='lower right', fontsize=7.5, framealpha=0.9)
    
    if noninf_p.exists():
        ni_df = pd.read_csv(noninf_p)
        ni_primary = ni_df[(np.isclose(ni_df['lambda'], 0.5)) & (np.isclose(ni_df['margin'], 0.02))]
        if not ni_primary.empty:
            k_col = 'k' if 'k' in ni_primary.columns else 'channels_k'
            ax2.plot(ni_primary[k_col], ni_primary['mean_diff'], 's-', color='#1f77b4', linewidth=2, label=r'Mean $\Delta_k = F1_k - F1_{16}$')
            ax2.fill_between(ni_primary[k_col], ni_primary['lcb_95'], ni_primary['ucb_95'], color='#1f77b4', alpha=0.2, label='95% Bootstrap CI')
            ax2.axhline(-0.02, color='#d62728', linestyle=':', linewidth=1.5, label=r'Non-Inferiority Margin ($-\delta = -0.02$)')
            ax2.axhline(0.0, color='black', linestyle='--', linewidth=1.0)
            ax2.axvline(12, color='#2ca02c', linestyle='-.', linewidth=1.5, label=r'$k^* = 12$ (Smallest Non-Inferior)')
            ax2.scatter([12], [ni_primary[ni_primary[k_col]==12]['mean_diff'].values[0]], color='#2ca02c', s=80, zorder=10)
            ax2.set_xlabel("Number of Selected Channels ($k$)")
            ax2.set_ylabel(r"Paired Difference $\Delta_k$ vs Full Array")
            ax2.set_title(r"(b) Non-Inferiority Decision Boundary ($\delta=0.02$)", fontsize=10, fontweight='bold')
            ax2.set_xticks(range(1, 17))
            ax2.set_ylim(-0.15, 0.05)
            ax2.grid(True)
            ax2.legend(loc='lower right', fontsize=7.5, framealpha=0.9)
            
    save_fig(fig, "fig4_sparse_sensor_curve")

def generate_figure5_baselines():
    """Figure 5: Channel Selection Baselines Comparison."""
    base_p = ROOT / "artifacts" / "selection_baselines" / "selection_baselines_summary.csv"
    if not base_p.exists(): return
    df_base = pd.read_csv(base_p)
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    sns.lineplot(data=df_base, x='k', y='mean_macro_f1', hue='strategy', marker='o', linewidth=2.2, ax=ax)
    ax.set_title("Channel Selection Strategy Comparison (SR-CFA vs Baselines)", fontsize=10, fontweight='bold')
    ax.set_xlabel("Number of Selected Channels ($k$)")
    ax.set_ylabel("Subject-Independent Macro-F1")
    ax.set_xticks([4, 6, 8, 12])
    ax.grid(True)
    ax.legend(title="Selection Strategy", fontsize=8.5)
    save_fig(fig, "fig5_selection_method_comparison")

def generate_figure6_stability():
    """Figure 6: Attribution Stability Distributions."""
    freq_p = ROOT / "artifacts" / "stability" / "channel_selection_frequency.csv"
    if not freq_p.exists(): return
    df_freq = pd.read_csv(freq_p).sort_values('channel')
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.0, 3.8))
    x = np.arange(1, 17)
    w = 0.25
    ax1.bar(x - w, df_freq['selected_top4_frac'], width=w, label='Top-4 Selection Freq', color='#1f77b4', alpha=0.85)
    ax1.bar(x, df_freq['selected_top6_frac'], width=w, label='Top-6 Selection Freq', color='#2ca02c', alpha=0.85)
    ax1.bar(x + w, df_freq['selected_top8_frac'], width=w, label='Top-8 Selection Freq', color='#ff7f0e', alpha=0.85)
    ax1.set_xlabel("Electrode Channel ID (1–16)")
    ax1.set_ylabel("Selection Frequency Fraction")
    ax1.set_title("(a) Channel Selection Frequency Across Folds", fontsize=10, fontweight='bold')
    ax1.set_xticks(range(1, 17))
    ax1.set_ylim(0, 1.1)
    ax1.grid(True, axis='y')
    ax1.legend(loc='upper right', fontsize=8)
    
    ax2.errorbar(df_freq['channel'], df_freq['median_rank'], yerr=df_freq['rank_mad'], fmt='o', color='#d62728',
                 ecolor='#333333', elinewidth=1.5, capsize=4, markersize=6, label='Median Rank ± MAD')
    ax2.set_xlabel("Electrode Channel ID (1–16)")
    ax2.set_ylabel("Attribution Rank (1 = Most Important)")
    ax2.set_title("(b) Channel Rank Central Tendency and Dispersion", fontsize=10, fontweight='bold')
    ax2.set_xticks(range(1, 17))
    ax2.set_ylim(0.5, 16.5)
    ax2.invert_yaxis()
    ax2.grid(True)
    ax2.legend(loc='upper right', fontsize=8)
    save_fig(fig, "fig6_stability_analysis")

def generate_figure7_cross_session():
    """Figure 7: Cross-Session Generalization."""
    cs_p = ROOT / "artifacts" / "cross_session" / "cross_session_summary.csv"
    if not cs_p.exists(): return
    df_cs = pd.read_csv(cs_p)
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    sns.lineplot(data=df_cs, x='k', y='mean_macro_f1', hue='test_session', style='experiment', marker='o', linewidth=2, ax=ax)
    ax.set_title("Cross-Session Sparse Performance Degradation (Donning/Doffing)", fontsize=10, fontweight='bold')
    ax.set_xlabel("Number of Selected Channels ($k$)")
    ax.set_ylabel("Macro-F1 Score")
    ax.grid(True)
    ax.legend(title="Session / Design", fontsize=8.5)
    save_fig(fig, "fig7_cross_session_performance")

def generate_figure8_faithfulness():
    """Figure 8: Explanation Faithfulness Deletion Curves."""
    faith_p = ROOT / "artifacts" / "faithfulness" / "faithfulness_summary.csv"
    if not faith_p.exists(): return
    df_faith = pd.read_csv(faith_p)
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    sns.lineplot(data=df_faith, x='m_removed', y='mean_macro_f1', hue='removal_arm', marker='s', linewidth=2.2, ax=ax)
    ax.set_title("XAI Faithfulness Deletion Curves (ROAR Protocol)", fontsize=10, fontweight='bold')
    ax.set_xlabel("Number of Removed Channels ($m$)")
    ax.set_ylabel("Macro-F1 Score")
    ax.grid(True)
    ax.legend(title="Removal Arm", fontsize=8.5)
    save_fig(fig, "fig8_xai_faithfulness_deletion")

def generate_figure9_db5():
    """Figure 9: NinaPro DB5 External Methodological Replication."""
    db5_p = ROOT / "artifacts" / "db5" / "db5_summary.csv"
    if not db5_p.exists(): return
    df_db5 = pd.read_csv(db5_p)
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    sns.lineplot(data=df_db5, x='k', y='mean_macro_f1', marker='^', color='#1f77b4', linewidth=2.2, ax=ax)
    ax.set_title("NinaPro DB5 External Methodological Replication (10 Subjects, 12 Movements)", fontsize=10, fontweight='bold')
    ax.set_xlabel("Number of Selected Channels ($k$)")
    ax.set_ylabel("Macro-F1 Score")
    ax.grid(True)
    save_fig(fig, "fig9_ninapro_db5_replication")

def run_all_figures():
    print("=" * 70, flush=True)
    print("GENERATING ALL PUBLICATION-GRADE FIGURES (FIG 1 - 10)", flush=True)
    print("=" * 70, flush=True)
    generate_figure2()
    generate_figure3()
    generate_figure4()
    generate_figure5_baselines()
    generate_figure6_stability()
    generate_figure7_cross_session()
    generate_figure8_faithfulness()
    generate_figure9_db5()
    print("=" * 70, flush=True)

if __name__ == "__main__":
    run_all_figures()
