"""Generate a publication-grade Cell Architecture Diagram for Figure 2.

Follows the canonical 'cell architecture' visual paradigm seen in top IEEE/Nature/Elsevier papers:
- Modular processing cell with input data streams, dimension annotations (R^{160}, R^{16x10}, R^{16}, R^k)
- Mathematical operator nodes: summation, channel pooling, median central tendency, MAD dispersion penalty
- Cross-fitting state buffer and stability gate (lambda multiplier)
- Output sparse masking and channel reduction gate
"""

import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIG_DIR = ROOT / "artifacts" / "figures"
TEX_FIG_DIR = ROOT / "manuscript" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)
TEX_FIG_DIR.mkdir(parents=True, exist_ok=True)

# Publication styling
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']
plt.rcParams['font.size'] = 8.5
plt.rcParams['axes.titlesize'] = 10
plt.rcParams['axes.titleweight'] = 'bold'

def draw_operator_node(ax, x, y, symbol, radius=0.32, color='#ffffff', edgecolor='#333333', text_color='#111111', font_size=10):
    """Draw a circular mathematical operator node (e.g., +, -, x, sum)."""
    circle = patches.Circle((x, y), radius, facecolor=color, edgecolor=edgecolor, linewidth=1.4, zorder=10)
    ax.add_patch(circle)
    ax.text(x, y, symbol, ha='center', va='center', fontsize=font_size, fontweight='bold', color=text_color, zorder=11)

def draw_cell_architecture():
    fig = plt.figure(figsize=(13.5, 6.6), dpi=300)
    ax = fig.add_subplot(1, 1, 1)
    ax.axis('off')
    ax.set_xlim(0, 15)
    ax.set_ylim(0, 7.5)

    # Outer Cell Boundary (SR-CFA Cell)
    cell_box = patches.FancyBboxPatch((2.2, 0.6), 10.4, 6.2, boxstyle="round,pad=0.25",
                                      facecolor='#f8fafc', edgecolor='#0f766e', linewidth=2.0, linestyle='-')
    ax.add_patch(cell_box)
    ax.text(7.4, 6.55, r"Stability-Regularized Cross-Fitted Attribution (SR-CFA) Computing Cell",
            ha='center', va='center', fontweight='bold', fontsize=11, color='#0f766e')

    # -------------------------------------------------------------------------
    # 1. Inputs entering from Left
    # -------------------------------------------------------------------------
    # Input Feature Vector
    ax.annotate('', xy=(2.2, 5.0), xytext=(0.4, 5.0),
                arrowprops=dict(arrowstyle="->", color='#1e293b', lw=2.0))
    ax.text(1.2, 5.35, r"$\mathbf{x}_i \in \mathbb{R}^{160}$", ha='center', va='bottom', fontsize=9.5, fontweight='bold', color='#0369a1')
    ax.text(1.2, 4.65, "16 Ch $\\times$ 10 Feats\n(MAV, RMS...)", ha='center', va='top', fontsize=7.5, color='#475569')

    # Group Fold ID Input
    ax.annotate('', xy=(2.2, 2.0), xytext=(0.4, 2.0),
                arrowprops=dict(arrowstyle="->", color='#1e293b', lw=2.0))
    ax.text(1.2, 2.35, r"$g_i \in \{1,\dots,K_{\mathrm{in}}\}$", ha='center', va='bottom', fontsize=9.0, fontweight='bold', color='#b45309')
    ax.text(1.2, 1.65, "Inner Group-KFold\n(Subject ID)", ha='center', va='top', fontsize=7.5, color='#475569')

    # -------------------------------------------------------------------------
    # 2. Inside the Cell: Processing Blocks
    # -------------------------------------------------------------------------

    # (A) TreeSHAP Attribution Block
    box_shap = patches.FancyBboxPatch((2.7, 4.2), 2.2, 1.6, boxstyle="round,pad=0.1",
                                     facecolor='#e0f2fe', edgecolor='#0284c7', linewidth=1.4)
    ax.add_patch(box_shap)
    ax.text(3.8, 5.35, "TreeSHAP Engine", ha='center', va='center', fontweight='bold', fontsize=8.5, color='#0369a1')
    ax.text(3.8, 4.85, r"$\mathcal{O}(T L D^2)$", ha='center', va='center', fontsize=8.0, color='#0284c7')
    ax.text(3.8, 4.45, r"$\phi_{i,(c,f)} \in \mathbb{R}^{16 \times 10}$", ha='center', va='center', fontsize=7.8, fontweight='bold', color='#0f172a')

    # Connect Input to TreeSHAP Block
    ax.plot([2.2, 2.7], [5.0, 5.0], color='#1e293b', lw=2.0)

    # (B) Channel Pooling Operator (\sum | \cdot |)
    draw_operator_node(ax, 5.7, 5.0, r"$\bigoplus$", radius=0.32, color='#fef08a', edgecolor='#ca8a04', font_size=11)
    ax.text(5.7, 5.5, r"$\Phi_{i,c} = \sum_{f=1}^{10} |\phi_{i,(c,f)}|$", ha='center', va='bottom', fontsize=7.5, fontweight='bold', color='#854d0e')

    # Wire from SHAP to Pool
    ax.annotate('', xy=(5.38, 5.0), xytext=(4.9, 5.0), arrowprops=dict(arrowstyle="->", color='#1e293b', lw=1.8))

    # (C) Inner-Fold Cross-Fitting Memory Buffer
    box_buf = patches.FancyBboxPatch((4.7, 1.4), 2.0, 1.4, boxstyle="round,pad=0.1",
                                    facecolor='#fef3c7', edgecolor='#d97706', linewidth=1.4)
    ax.add_patch(box_buf)
    ax.text(5.7, 2.4, "Fold Buffer", ha='center', va='center', fontweight='bold', fontsize=8.5, color='#b45309')
    ax.text(5.7, 1.95, r"$K_{\mathrm{in}}=5$ Splits", ha='center', va='center', fontsize=7.5, color='#78350f')
    ax.text(5.7, 1.6, r"$I_{j,c} \in \mathbb{R}^{K \times 16}$", ha='center', va='center', fontsize=7.8, fontweight='bold', color='#451a03')

    # Wire from Group ID to Buffer and Pool to Buffer
    ax.plot([2.2, 4.7], [2.0, 2.0], color='#1e293b', lw=1.8)
    ax.plot([5.7, 5.7], [4.68, 2.8], color='#1e293b', lw=1.6, linestyle='--')
    ax.annotate('', xy=(5.7, 2.8), xytext=(5.7, 3.2), arrowprops=dict(arrowstyle="->", color='#1e293b', lw=1.6))

    # (D) Statistical Operator Branches: Central Tendency vs Dispersion Penalty
    # Wire splitting from Fold Buffer
    ax.plot([6.7, 7.3], [2.0, 2.0], color='#1e293b', lw=1.8)
    ax.plot([7.3, 7.3], [1.4, 4.2], color='#1e293b', lw=1.8)

    # Branch 1: Median Operator (Ac)
    draw_operator_node(ax, 8.4, 4.2, r"$\mathrm{Med}$", radius=0.36, color='#dcfce7', edgecolor='#16a34a', text_color='#15803d', font_size=8.5)
    ax.annotate('', xy=(8.04, 4.2), xytext=(7.3, 4.2), arrowprops=dict(arrowstyle="->", color='#1e293b', lw=1.8))
    ax.text(8.4, 4.75, r"$\mathbf{A}_c = \operatorname{median}(I_{j,c})$", ha='center', va='bottom', fontsize=8.0, fontweight='bold', color='#15803d')

    # Branch 2: MAD Operator (Uc)
    draw_operator_node(ax, 8.4, 1.4, r"$\mathrm{MAD}$", radius=0.36, color='#fee2e2', edgecolor='#dc2626', text_color='#b91c1c', font_size=8.0)
    ax.annotate('', xy=(8.04, 1.4), xytext=(7.3, 1.4), arrowprops=dict(arrowstyle="->", color='#1e293b', lw=1.8))
    ax.text(8.4, 0.85, r"$\mathbf{U}_c = \operatorname{MAD}(I_{j,c})$", ha='center', va='top', fontsize=8.0, fontweight='bold', color='#b91c1c')

    # Multiplier Node (lambda * Uc)
    draw_operator_node(ax, 9.8, 1.4, r"$\bigotimes$", radius=0.32, color='#ffedd5', edgecolor='#ea580c', text_color='#c2410c', font_size=11)
    ax.annotate('', xy=(9.48, 1.4), xytext=(8.76, 1.4), arrowprops=dict(arrowstyle="->", color='#1e293b', lw=1.8))
    # Lambda input from bottom
    ax.annotate('', xy=(9.8, 1.08), xytext=(9.8, 0.2), arrowprops=dict(arrowstyle="->", color='#ea580c', lw=1.8))
    ax.text(9.8, 0.05, r"Regularizer $\lambda \geq 0$", ha='center', va='top', fontsize=8.5, fontweight='bold', color='#c2410c')
    ax.text(9.8, 1.9, r"$\lambda \cdot \mathbf{U}_c$", ha='center', va='bottom', fontsize=8.0, fontweight='bold', color='#c2410c')

    # Subtraction Node: Ac - (lambda * Uc)
    draw_operator_node(ax, 9.8, 4.2, r"$\ominus$", radius=0.34, color='#ede9fe', edgecolor='#7c3aed', text_color='#6d28d9', font_size=11)
    ax.annotate('', xy=(9.46, 4.2), xytext=(8.76, 4.2), arrowprops=dict(arrowstyle="->", color='#1e293b', lw=1.8))
    ax.plot([9.8, 9.8], [1.72, 3.86], color='#1e293b', lw=1.8)
    ax.annotate('', xy=(9.8, 3.86), xytext=(9.8, 3.5), arrowprops=dict(arrowstyle="->", color='#1e293b', lw=1.8))
    ax.text(9.8, 4.85, r"$\mathbf{Q}_c(\lambda) = \mathbf{A}_c - \lambda \mathbf{U}_c$", ha='center', va='bottom', fontsize=8.2, fontweight='bold', color='#6d28d9')

    # Ranking & Top-k Selection Box
    box_rank = patches.FancyBboxPatch((10.8, 3.4), 1.6, 1.6, boxstyle="round,pad=0.1",
                                     facecolor='#f3e8ff', edgecolor='#9333ea', linewidth=1.4)
    ax.add_patch(box_rank)
    ax.text(11.6, 4.6, r"Top-$k$ Mask", ha='center', va='center', fontweight='bold', fontsize=8.5, color='#7e22ce')
    ax.text(11.6, 4.1, r"$\operatorname{argsort}(-Q_c)$", ha='center', va='center', fontsize=7.5, color='#581c87')
    ax.text(11.6, 3.65, r"$\mathbf{m}_k \in \{0,1\}^{16}$", ha='center', va='center', fontsize=7.8, fontweight='bold', color='#3b0764')

    ax.annotate('', xy=(10.8, 4.2), xytext=(10.14, 4.2), arrowprops=dict(arrowstyle="->", color='#1e293b', lw=1.8))

    # -------------------------------------------------------------------------
    # 3. Outputs Exiting to Right
    # -------------------------------------------------------------------------
    # Channel reduction output wire
    ax.annotate('', xy=(14.5, 4.2), xytext=(12.4, 4.2),
                arrowprops=dict(arrowstyle="->", color='#0f766e', lw=2.2))
    ax.text(13.45, 4.55, r"Selected Subset $\mathcal{S}_k$", ha='center', va='bottom', fontsize=9.0, fontweight='bold', color='#0f766e')
    ax.text(13.45, 3.75, r"Optimal $k^*=12$", ha='center', va='top', fontsize=8.5, fontweight='bold', color='#15803d',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='#dcfce7', edgecolor='#16a34a'))

    # Downstream Feature Filtering Output
    draw_operator_node(ax, 13.5, 2.0, r"$\bigodot$", radius=0.32, color='#e0e7ff', edgecolor='#4338ca', text_color='#3730a3', font_size=11)
    # Feed m_k down to multiplication node
    ax.plot([12.0, 12.0], [3.4, 2.0], color='#1e293b', lw=1.6, linestyle=':')
    ax.plot([12.0, 13.18], [2.0, 2.0], color='#1e293b', lw=1.6, linestyle=':')
    ax.annotate('', xy=(13.18, 2.0), xytext=(12.8, 2.0), arrowprops=dict(arrowstyle="->", color='#1e293b', lw=1.6))
    
    # Feed raw features bypass line from input to multiplication node
    ax.plot([1.2, 1.2], [5.0, 6.4], color='#0369a1', lw=1.4, linestyle=':')
    ax.plot([1.2, 13.5], [6.4, 6.4], color='#0369a1', lw=1.4, linestyle=':')
    ax.plot([13.5, 13.5], [6.4, 2.32], color='#0369a1', lw=1.4, linestyle=':')
    ax.annotate('', xy=(13.5, 2.32), xytext=(13.5, 2.8), arrowprops=dict(arrowstyle="->", color='#0369a1', lw=1.4))

    # Downstream model input
    ax.annotate('', xy=(14.8, 2.0), xytext=(13.82, 2.0),
                arrowprops=dict(arrowstyle="->", color='#4338ca', lw=2.0))
    ax.text(14.3, 1.45, r"$\mathbf{x}_{\mathrm{sparse}} \in \mathbb{R}^{10k}$", ha='center', va='top', fontsize=8.5, fontweight='bold', color='#4338ca')

    # Save outputs
    fig.savefig(FIG_DIR / "fig2_model_architecture.pdf", dpi=300, bbox_inches='tight')
    fig.savefig(FIG_DIR / "fig2_model_architecture.png", dpi=300, bbox_inches='tight')
    fig.savefig(TEX_FIG_DIR / "fig2_model_architecture.pdf", dpi=300, bbox_inches='tight')
    fig.savefig(TEX_FIG_DIR / "fig2_model_architecture.png", dpi=300, bbox_inches='tight')
    plt.close(fig)
    print("  [OK] Saved cell architecture fig2_model_architecture.pdf / fig2_model_architecture.png", flush=True)

if __name__ == "__main__":
    draw_cell_architecture()
