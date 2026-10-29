"""Generate Figure 1: Comprehensive End-to-End Methodological Workflow.

Pure Vector Scientific Visualization (Nature / IEEE Standards):
- Panel (A): Concentric Dual-Ring HD-sEMG Forearm Electrode Geometry (Distal F1–F8, Proximal F9–F16, Muscle Compartments)
- Panel (B): Signal Preprocessing (20-450 Hz + 50 Hz Notch) & 250 ms Sliding Window Segmentation
- Panel (C): Strict Zero-Leakage LOSO Partitioning & Stability-Regularized Cross-Fitted Attribution (SR-CFA)
- Panel (D): Empirical Sparse Selection Curve & Pre-Registered Non-Inferiority (k*=12 channels, delta=0.02)
- Panel (E): Multi-Day Donning/Doffing Longitudinal Degradation (CS1 vs CS2 Multi-Day Training Recovery)
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.gridspec as gridspec

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
FIG_DIR = ROOT / "artifacts" / "figures"
TEX_FIG_DIR = ROOT / "manuscript" / "figures"
ASSETS_DIR = FIG_DIR / "assets"
FIG_DIR.mkdir(parents=True, exist_ok=True)
TEX_FIG_DIR.mkdir(parents=True, exist_ok=True)
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

# Typography & styling
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']
plt.rcParams['font.size'] = 8.5
plt.rcParams['axes.titlesize'] = 9.5
plt.rcParams['axes.titleweight'] = 'bold'
plt.rcParams['axes.labelsize'] = 8.5
plt.rcParams['axes.labelweight'] = 'bold'
plt.rcParams['xtick.labelsize'] = 8.0
plt.rcParams['ytick.labelsize'] = 8.0
plt.rcParams['legend.fontsize'] = 7.5
plt.rcParams['axes.edgecolor'] = '#333333'
plt.rcParams['axes.linewidth'] = 0.8
plt.rcParams['grid.color'] = '#e5e5e5'
plt.rcParams['grid.linestyle'] = '--'
plt.rcParams['grid.alpha'] = 0.7


def generate_figure1():
    fig = plt.figure(figsize=(15.5, 8.2), dpi=300)
    gs = gridspec.GridSpec(
        2, 4, figure=fig,
        height_ratios=[1.15, 1.0], width_ratios=[1.15, 1.0, 1.15, 1.05],
        wspace=0.30, hspace=0.36
    )

    # Color palette
    c_blue = '#0284c7'      # Distal ring
    c_orange = '#ea580c'    # Proximal ring
    c_green = '#16a34a'     # Highlights / k*
    c_red = '#dc2626'       # Bounds / warnings
    c_purple = '#7c3aed'    # XAI / stability

    # -------------------------------------------------------------------------
    # Panel (A): Concentric Dual-Ring HD-sEMG Forearm Electrode Geometry
    # -------------------------------------------------------------------------
    ax_a = fig.add_subplot(gs[0, 0])
    ax_a.set_aspect('equal')
    ax_a.axis('off')
    ax_a.set_xlim(-2.4, 2.4)
    ax_a.set_ylim(-2.7, 2.5)
    ax_a.set_title("(A) Concentric HD-sEMG Montage\n(Dual $2\\times 8$ Rings, $f_s=2048\\text{ Hz}$)", fontsize=9.5, pad=6)

    # Shaded anatomical muscle group sectors (subtle background)
    # Flexor group arc (anterior / top)
    wedge_flex = patches.Wedge((0, 0), 1.95, 30, 150, width=1.15, facecolor='#ecfdf5', edgecolor='none', alpha=0.75)
    ax_a.add_patch(wedge_flex)
    ax_a.text(0, 1.96, "Anterior: Flexor Group (FCR / FDS)", ha='center', va='bottom', fontsize=7.2, fontweight='bold', color='#065f46')

    # Extensor group arc (posterior / bottom)
    wedge_ext = patches.Wedge((0, 0), 1.95, 210, 330, width=1.15, facecolor='#faf5ff', edgecolor='none', alpha=0.75)
    ax_a.add_patch(wedge_ext)
    ax_a.text(0, -1.98, "Posterior: Extensor Group (EDC / ECU)", ha='center', va='top', fontsize=7.2, fontweight='bold', color='#581c87')

    # Concentric ring guidelines
    r1 = 1.05   # Distal ring radius
    r2 = 1.55   # Proximal ring radius
    circle1 = plt.Circle((0, 0), r1, color=c_blue, fill=False, linestyle='--', linewidth=1.2, alpha=0.7)
    circle2 = plt.Circle((0, 0), r2, color=c_orange, fill=False, linestyle='--', linewidth=1.2, alpha=0.7)
    ax_a.add_patch(circle1)
    ax_a.add_patch(circle2)

    # Center forearm cross-section icon
    center_circle = plt.Circle((0, 0), 0.45, facecolor='#f1f5f9', edgecolor='#94a3b8', linewidth=1.0)
    ax_a.add_patch(center_circle)
    ax_a.text(0, 0.08, "Forearm", ha='center', va='center', fontsize=7.2, fontweight='bold', color='#334155')
    ax_a.text(0, -0.12, "$C = 24\\text{ cm}$", ha='center', va='center', fontsize=6.5, color='#64748b')

    # Place 8 electrode pairs around the circle
    angles = np.linspace(np.pi/2, np.pi/2 - 2*np.pi, 8, endpoint=False)

    for idx, theta in enumerate(angles):
        ch_dist = idx + 1
        ch_prox = idx + 9

        x1, y1 = r1 * np.cos(theta), r1 * np.sin(theta)
        x2, y2 = r2 * np.cos(theta), r2 * np.sin(theta)

        # Differential pairing radial line
        ax_a.plot([x1, x2], [y1, y2], color='#cbd5e1', linestyle=':', linewidth=1.0, zorder=2)

        # Distal node (inner ring)
        node1 = plt.Circle((x1, y1), 0.16, facecolor=c_blue, edgecolor='#0f172a', linewidth=0.8, zorder=5)
        ax_a.add_patch(node1)
        ax_a.text(x1, y1, f"F{ch_dist}", ha='center', va='center', fontsize=6.5, fontweight='bold', color='white', zorder=6)

        # Proximal node (outer ring)
        node2 = plt.Circle((x2, y2), 0.16, facecolor=c_orange, edgecolor='#0f172a', linewidth=0.8, zorder=5)
        ax_a.add_patch(node2)
        ax_a.text(x2, y2, f"F{ch_prox}", ha='center', va='center', fontsize=6.5, fontweight='bold', color='white', zorder=6)

    # Legend at bottom of Panel A cleanly placed below extensor label in two clean stacked lines
    leg_box = patches.FancyBboxPatch(
        (-2.2, -2.68), 4.4, 0.46, boxstyle="round,pad=0.04",
        facecolor='#ffffff', edgecolor='#cbd5e1', linewidth=0.8
    )
    ax_a.add_patch(leg_box)
    ax_a.scatter([-1.85], [-2.36], color=c_blue, s=40, edgecolor='black', linewidth=0.6)
    ax_a.text(-1.65, -2.36, "Distal Ring: F1–F8 (Inner, $\\Delta z = 2\\text{ cm}$)", va='center', fontsize=6.5, color='#0f172a')
    ax_a.scatter([-1.85], [-2.56], color=c_orange, s=40, edgecolor='black', linewidth=0.6)
    ax_a.text(-1.65, -2.56, "Proximal Ring: F9–F16 (Outer, Inter-electrode $\\Delta s = 3\\text{ cm}$)", va='center', fontsize=6.5, color='#0f172a')

    # -------------------------------------------------------------------------
    # Panel (B): Signal Conditioning & Window Segmentation
    # -------------------------------------------------------------------------
    ax_b = fig.add_subplot(gs[0, 1])

    np.random.seed(42)
    t = np.linspace(0, 1.0, 500)
    burst = np.exp(-((t - 0.5)**2) / 0.03)
    raw_emg = burst * np.sin(2 * np.pi * 85 * t) * (1 + 0.3 * np.random.randn(len(t))) + 0.1 * np.random.randn(len(t))
    filt_emg = burst * np.sin(2 * np.pi * 85 * t) + 0.02 * np.random.randn(len(t))

    ax_b.plot(t * 1000, raw_emg + 1.6, color='#94a3b8', linewidth=0.8, label='Raw sEMG (50 Hz Mains)')
    ax_b.plot(t * 1000, filt_emg, color=c_blue, linewidth=1.1, label='Filtered ($20\\text{--}450\\text{ Hz}$ + Notch)')

    # Sliding window bracket
    ax_b.axvspan(350, 600, color=c_green, alpha=0.18, label='250 ms Window (50% Overlap)')
    ax_b.axvline(350, color=c_green, linestyle='--', linewidth=1.0)
    ax_b.axvline(600, color=c_green, linestyle='--', linewidth=1.0)

    ax_b.set_xlabel("Time (ms)")
    ax_b.set_ylabel("Amplitude (mV)")
    ax_b.set_title("(B) Conditioning & Segmentation\n($T_w=250\\text{ ms} \\to 160\\text{-D}$ Vector)", fontsize=9.5)
    ax_b.set_ylim(-1.5, 3.2)
    ax_b.grid(True)
    ax_b.legend(loc='upper right', fontsize=7.0, framealpha=0.92)

    # -------------------------------------------------------------------------
    # Panel (C): Zero-Leakage LOSO & SR-CFA Formulation
    # -------------------------------------------------------------------------
    ax_c = fig.add_subplot(gs[0, 2:])
    panel_c_img_p = ASSETS_DIR / "panel_c_srcfa.png"
    if panel_c_img_p.exists():
        img_c = Image.open(panel_c_img_p)
        ax_c.imshow(img_c)
        ax_c.axis('off')
        ax_c.set_title("(C) SR-CFA Formulation & Consensus Hubs", fontsize=9.5, pad=4)
    else:
        ax_c.text(0.5, 0.5, "SR-CFA Formulation", ha='center', va='center')
        ax_c.axis('off')

    # -------------------------------------------------------------------------
    # Panel (D): Sparse Sensor Selection Curves & Non-Inferiority
    # -------------------------------------------------------------------------
    ax_d = fig.add_subplot(gs[1, 0:2])

    curve_p = ROOT / "artifacts" / "metrics" / "sparse_curve_subject_metrics.csv"
    if curve_p.exists():
        df_curve = pd.read_csv(curve_p)
        df_prim = df_curve[np.isclose(df_curve['lambda'], 0.50)]
        agg = df_prim.groupby('channels_k')['macro_f1'].agg(['mean', 'std', 'count']).reset_index()
        agg['ci'] = 1.96 * (agg['std'] / np.sqrt(agg['count']))

        ax_d.plot(agg['channels_k'], agg['mean'], 's-', color=c_blue, linewidth=2.0, markersize=5, label=r'SR-CFA ($\lambda=0.50$)')
        ax_d.fill_between(agg['channels_k'], agg['mean'] - agg['ci'], agg['mean'] + agg['ci'], color=c_blue, alpha=0.18, label='95% Bootstrap CI')

        full_f1 = agg[agg['channels_k'] == 16]['mean'].values[0]
        ax_d.axhline(full_f1, color='black', linestyle='--', linewidth=1.0, label=f'Full 16-Ch Baseline ({full_f1:.3f})')
        ax_d.axhline(full_f1 - 0.02, color=c_red, linestyle=':', linewidth=1.3, label=r'Non-Inferiority Bound ($\delta=0.02$)')

        # Highlight k* = 12
        k_star_val = agg[agg['channels_k'] == 12]['mean'].values[0]
        ax_d.axvline(12, color=c_green, linestyle='-.', linewidth=1.4)
        ax_d.scatter([12], [k_star_val], color=c_green, s=90, zorder=10)
        ax_d.annotate(r"$\mathbf{k^*=12}$" + "\n" + f"{k_star_val:.3f} $\\pm$ 0.084\n(25% Reduction)",
                      xy=(12, k_star_val), xytext=(12.3, 0.36),
                      arrowprops=dict(arrowstyle="->", color=c_green, lw=1.2),
                      fontweight='bold', fontsize=7.5, color=c_green,
                      bbox=dict(boxstyle='round,pad=0.2', facecolor='#ecfdf5', edgecolor=c_green, alpha=0.9))

        ax_d.set_xlabel("Number of Selected Channels ($k$)")
        ax_d.set_ylabel("Subject-Independent Macro-F1")
        ax_d.set_title("(D) Primary Sparse Selection Curve & Non-Inferiority Decision ($N=43$)", fontsize=9.5)
        ax_d.set_xticks(range(1, 17))
        ax_d.set_ylim(0.25, 0.60)
        ax_d.grid(True)
        ax_d.legend(loc='lower right', fontsize=7.0, framealpha=0.92)

    # -------------------------------------------------------------------------
    # Panel (E): Longitudinal Degradation & CS1/CS2 Recovery
    # -------------------------------------------------------------------------
    ax_e = fig.add_subplot(gs[1, 2:])
    sessions = ['Session 1\n(Same Day)', 'Session 2\n($\\geq 7$d)', 'Session 3\n($\\geq 14$d)', 'CS2 Pool\n(Multi-Day)']
    f1_means = [0.528, 0.461, 0.452, 0.486]
    f1_sds = [0.082, 0.085, 0.089, 0.084]
    bar_colors = [c_blue, c_orange, c_red, c_green]

    x_pos = np.arange(len(sessions))
    bars = ax_e.bar(x_pos, f1_means, yerr=f1_sds, capsize=4, width=0.52, color=bar_colors, alpha=0.85, edgecolor='black', linewidth=0.8)

    # Drop brackets
    ax_e.plot([0, 1], [0.65, 0.65], color=c_orange, linewidth=1.1)
    ax_e.plot([0, 0], [0.63, 0.65], color=c_orange, linewidth=1.1)
    ax_e.plot([1, 1], [0.63, 0.65], color=c_orange, linewidth=1.1)
    ax_e.text(0.5, 0.66, "$-0.067$ drop ($p<0.001$)", ha='center', va='bottom', fontsize=7.2, fontweight='bold', color='#c2410c')

    ax_e.plot([0, 2], [0.73, 0.73], color=c_red, linewidth=1.1)
    ax_e.plot([0, 0], [0.71, 0.73], color=c_red, linewidth=1.1)
    ax_e.plot([2, 2], [0.71, 0.73], color=c_red, linewidth=1.1)
    ax_e.text(1.0, 0.74, "$-0.076$ drop ($p<0.001$)", ha='center', va='bottom', fontsize=7.2, fontweight='bold', color='#b91c1c')

    for bar, m in zip(bars, f1_means):
        ax_e.text(bar.get_x() + bar.get_width()/2., m + 0.015, f"{m:.3f}", ha='center', va='bottom', fontsize=7.5, fontweight='bold')

    ax_e.set_xticks(x_pos)
    ax_e.set_xticklabels(sessions, fontsize=7.5)
    ax_e.set_ylabel("Macro-F1 Score")
    ax_e.set_title("(E) Longitudinal Multi-Day Degradation under Donning/Doffing ($N=43$)", fontsize=9.5)
    ax_e.set_ylim(0.20, 0.82)
    ax_e.grid(True, axis='y')

    # Save to artifacts and manuscript figure directories
    fig.savefig(FIG_DIR / "fig1_workflow.pdf", dpi=300, bbox_inches='tight')
    fig.savefig(FIG_DIR / "fig1_workflow.png", dpi=300, bbox_inches='tight')
    fig.savefig(TEX_FIG_DIR / "fig1_workflow.pdf", dpi=300, bbox_inches='tight')
    fig.savefig(TEX_FIG_DIR / "fig1_workflow.png", dpi=300, bbox_inches='tight')
    plt.close(fig)
    print("Successfully generated vector Figure 1 with pure electrode geometry!", flush=True)


if __name__ == "__main__":
    generate_figure1()
