"""Generate Figure 2 in the canonical Transformer architecture visual style.

Adheres strictly to the reference image:
- Clean vertical flow with two paired columnar containers
- Soft pastel palette: Pink (Inputs/Embeddings), Yellow (Norm), Peach (Core/SHAP),
  Blue (Ensemble/Feed Forward), Purple (Linear/Ranking), Green (Softmax/Selection Gate)
- Outer rounded container boxes with lateral annotations (N x layer / K_in x cross-fitted folds)
- Small circular arithmetic nodes (+, -, x) with crisp orthogonal bypass routing
- Professional typography, clear dimensional annotations, zero clutter
"""

from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches

ROOT = Path(__file__).resolve().parent.parent
FIG_DIR = ROOT / "artifacts" / "figures"
TEX_FIG_DIR = ROOT / "manuscript" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)
TEX_FIG_DIR.mkdir(parents=True, exist_ok=True)

# Publication typography & styling
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']
plt.rcParams['font.size'] = 9.0

# Transformer canonical color palette (from reference image)
C_PINK_BG = '#FCE4EC'     # Input / Embedding
C_PINK_BORDER = '#C27D7D'
C_YELLOW_BG = '#FEF9E7'   # Norm
C_YELLOW_BORDER = '#C9B037'
C_PEACH_BG = '#FDEBD0'    # Attention / SHAP Engine
C_PEACH_BORDER = '#DC7633'
C_BLUE_BG = '#D4E6F1'     # Feed Forward / Trees / Central Tendency
C_BLUE_BORDER = '#5499C7'
C_PURPLE_BG = '#E8DAEF'   # Linear / Ranking
C_PURPLE_BORDER = '#8E44AD'
C_GREEN_BG = '#D5F5E3'    # Softmax / Selection Gate
C_GREEN_BORDER = '#27AE60'
C_CONTAINER_BG = '#F8F9FA'
C_CONTAINER_BORDER = '#7F8C8D'
C_WIRE = '#1A1A1A'


def draw_box(ax, x, y, w, h, text, subtext="", bg_color=C_PINK_BG, border_color=C_PINK_BORDER,
             text_color='#111111', font_size=8.5, radius=0.08, bold=True):
    """Draw a rounded rectangular block exactly matching Transformer diagrams."""
    box = patches.FancyBboxPatch(
        (x - w / 2.0, y - h / 2.0), w, h,
        boxstyle=f"round,pad={radius}",
        facecolor=bg_color, edgecolor=border_color, linewidth=1.2, zorder=4
    )
    ax.add_patch(box)
    weight = 'bold' if bold else 'normal'
    if subtext:
        ax.text(x, y + 0.12, text, ha='center', va='center', fontsize=font_size,
                fontweight=weight, color=text_color, zorder=5)
        ax.text(x, y - 0.16, subtext, ha='center', va='center', fontsize=font_size - 1.2,
                color='#4A4A4A', zorder=5)
    else:
        ax.text(x, y, text, ha='center', va='center', fontsize=font_size,
                fontweight=weight, color=text_color, zorder=5)


def draw_circle_op(ax, x, y, symbol="+", radius=0.18, bg_color='#FFFFFF',
                   border_color=C_WIRE, text_color='#111111', font_size=9.5):
    """Draw circular arithmetic node (+, -, x, ~)."""
    circle = patches.Circle((x, y), radius, facecolor=bg_color, edgecolor=border_color,
                            linewidth=1.1, zorder=6)
    ax.add_patch(circle)
    ax.text(x, y, symbol, ha='center', va='center', fontsize=font_size,
            fontweight='bold', color=text_color, zorder=7)


def draw_arrow(ax, x1, y1, x2, y2, color=C_WIRE, lw=1.2, dashed=False):
    """Draw a crisp vertical/horizontal arrow."""
    ls = '--' if dashed else '-'
    ax.annotate(
        '', xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(arrowstyle="->", color=color, lw=lw, linestyle=ls,
                        shrinkA=0, shrinkB=0, mutation_scale=11),
        zorder=3
    )


def generate_transformer_style_fig2():
    fig = plt.figure(figsize=(8.2, 11.5), dpi=300)
    ax = fig.add_subplot(1, 1, 1)
    ax.axis('off')
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 14.2)

    # Column centerlines
    x_enc = 2.8   # Left column: Gesture Classifier Pipeline
    x_dec = 7.2   # Right column: SR-CFA Selection Engine

    # -------------------------------------------------------------------------
    # LEFT COLUMN: Subject-Independent sEMG Classifier
    # -------------------------------------------------------------------------

    # Bottom Input Text
    ax.text(x_enc, 0.4, "Multi-Channel sEMG Stream", ha='center', va='center',
            fontsize=9.0, fontweight='bold', color='#2C3E50')
    ax.text(x_enc, 0.15, r"16 Monopolar Channels ($2048\text{ Hz}$)", ha='center', va='center',
            fontsize=7.5, color='#7F8C8D')
    draw_arrow(ax, x_enc, 0.6, x_enc, 1.0)

    # Input Embedding Box (Feature Extraction)
    draw_box(ax, x_enc, 1.35, 2.4, 0.65, "Feature Extraction",
             r"$\mathbf{x} \in \mathbb{R}^{160}$ (10 TD/FD features)",
             bg_color=C_PINK_BG, border_color=C_PINK_BORDER, font_size=8.5)

    # Positional / Windowing Encoding Circle
    draw_circle_op(ax, x_enc, 2.3, symbol=r"$\oplus$", radius=0.18)
    draw_arrow(ax, x_enc, 1.7, x_enc, 2.1)

    # Windowing symbol on the side
    draw_circle_op(ax, x_enc - 1.1, 2.3, symbol=r"$\sim$", radius=0.18)
    ax.text(x_enc - 1.45, 2.3, "Sliding Window\n($250\\text{ms}, 50\\%$)", ha='right',
            va='center', fontsize=7.2, color='#2C3E50')
    draw_arrow(ax, x_enc - 0.9, 2.3, x_enc - 0.2, 2.3)

    # Outer Container Box: Classifier Layer
    enc_container = patches.FancyBboxPatch(
        (x_enc - 1.6, 2.7), 3.2, 5.8, boxstyle="round,pad=0.2",
        facecolor=C_CONTAINER_BG, edgecolor=C_CONTAINER_BORDER, linewidth=1.2, zorder=1
    )
    ax.add_patch(enc_container)
    ax.text(x_enc - 1.85, 5.6, "Subject-\nIndependent\nClassifier\nModule",
            ha='right', va='center', fontsize=8.2, fontweight='bold', color='#34495E')

    # Arrow entering container
    draw_arrow(ax, x_enc, 2.5, x_enc, 3.2)

    # Block 1 inside Left: Spatial Normalization (Norm)
    draw_box(ax, x_enc, 3.5, 2.2, 0.55, "Outer Training Norm", "Z-Score ($R_{-p}$)",
             bg_color=C_YELLOW_BG, border_color=C_YELLOW_BORDER, font_size=8.0)

    # Add Node 1
    draw_circle_op(ax, x_enc, 4.45, symbol=r"$\oplus$", radius=0.18)
    draw_arrow(ax, x_enc, 3.8, x_enc, 4.25)

    # Residual Bypass 1 (around norm & trees)
    ax.plot([x_enc - 1.3, x_enc - 1.3], [2.9, 4.45], color=C_WIRE, lw=1.1, zorder=2)
    ax.plot([x_enc - 1.3, x_enc - 0.2], [4.45, 4.45], color=C_WIRE, lw=1.1, zorder=2)
    draw_arrow(ax, x_enc - 0.2, 4.45, x_enc - 0.2, 4.45)
    ax.plot([x_enc, x_enc - 1.3], [2.9, 2.9], color=C_WIRE, lw=1.1, zorder=2)

    # Block 2 inside Left: Gradient Boosted Trees (XGBoost)
    draw_box(ax, x_enc, 5.45, 2.3, 0.75, "Tree Ensemble",
             r"XGBoost ($M$ trees, depth $D$)",
             bg_color=C_BLUE_BG, border_color=C_BLUE_BORDER, font_size=8.5)
    draw_arrow(ax, x_enc, 4.65, x_enc, 5.05)

    # Add Node 2
    draw_circle_op(ax, x_enc, 6.5, symbol=r"$\oplus$", radius=0.18)
    draw_arrow(ax, x_enc, 5.85, x_enc, 6.3)

    # Residual Bypass 2
    ax.plot([x_enc - 1.3, x_enc - 1.3], [4.8, 6.5], color=C_WIRE, lw=1.1, zorder=2)
    ax.plot([x_enc - 1.3, x_enc - 0.2], [6.5, 6.5], color=C_WIRE, lw=1.1, zorder=2)
    ax.plot([x_enc, x_enc - 1.3], [4.8, 4.8], color=C_WIRE, lw=1.1, zorder=2)

    # Block 3 inside Left: Norm
    draw_box(ax, x_enc, 7.5, 2.2, 0.55, "Layer Norm", "Confidence Calibration",
             bg_color=C_YELLOW_BG, border_color=C_YELLOW_BORDER, font_size=8.0)
    draw_arrow(ax, x_enc, 6.7, x_enc, 7.2)

    # Arrow leaving left container
    draw_arrow(ax, x_enc, 7.8, x_enc, 8.8)

    # Head 1 (Top Left): Linear Projection
    draw_box(ax, x_enc, 9.15, 2.1, 0.55, "Linear Projection", r"$\mathbf{z} \in \mathbb{R}^{16}$",
             bg_color=C_PURPLE_BG, border_color=C_PURPLE_BORDER, font_size=8.2)
    draw_arrow(ax, x_enc, 9.45, x_enc, 9.9)

    # Head 2 (Top Left): Softmax Classifier
    draw_box(ax, x_enc, 10.25, 2.1, 0.55, "Softmax Classifier", r"$\hat{y} = \operatorname{argmax} P(y|\mathbf{x})$",
             bg_color=C_GREEN_BG, border_color=C_GREEN_BORDER, font_size=8.2)
    draw_arrow(ax, x_enc, 10.55, x_enc, 11.2)

    # Top Output Left
    ax.text(x_enc, 11.45, "Gesture Probabilities", ha='center', va='center',
            fontsize=9.0, fontweight='bold', color='#1E8449')
    ax.text(x_enc, 11.2, r"$\hat{\mathbf{y}} \in \mathbb{R}^{16}$ Active Gestures", ha='center',
            va='center', fontsize=7.5, color='#27AE60')

    # -------------------------------------------------------------------------
    # RIGHT COLUMN: SR-CFA Explainability & Sensor Selection Engine
    # -------------------------------------------------------------------------

    # Bottom Input Right
    ax.text(x_dec, 0.4, "Inner-Fold Partition", ha='center', va='center',
            fontsize=9.0, fontweight='bold', color='#2C3E50')
    ax.text(x_dec, 0.15, r"$K_{\text{in}}=5$ GroupKFold on $R_{-p}$", ha='center', va='center',
            fontsize=7.5, color='#7F8C8D')
    draw_arrow(ax, x_dec, 0.6, x_dec, 1.0)

    # Input Box Right
    draw_box(ax, x_dec, 1.35, 2.4, 0.65, "Inner Split Encoder",
             r"Disjoint Cohorts $\{R_{-p,-j}\}_{j=1}^5$",
             bg_color=C_PINK_BG, border_color=C_PINK_BORDER, font_size=8.5)

    # Circle Positional encoding for fold ID
    draw_circle_op(ax, x_dec, 2.3, symbol=r"$\oplus$", radius=0.18)
    draw_arrow(ax, x_dec, 1.7, x_dec, 2.1)

    draw_circle_op(ax, x_dec + 1.1, 2.3, symbol=r"$\sim$", radius=0.18)
    ax.text(x_dec + 1.45, 2.3, "Subject ID\nGrouping", ha='left', va='center',
            fontsize=7.2, color='#2C3E50')
    draw_arrow(ax, x_dec + 0.9, 2.3, x_dec + 0.2, 2.3)

    # Outer Container Box Right: Cross-Fitted Attribution Layer
    dec_container = patches.FancyBboxPatch(
        (x_dec - 1.65, 2.7), 3.3, 8.4, boxstyle="round,pad=0.2",
        facecolor=C_CONTAINER_BG, edgecolor=C_CONTAINER_BORDER, linewidth=1.2, zorder=1
    )
    ax.add_patch(dec_container)
    ax.text(x_dec + 1.95, 6.9, "$K_{\\text{in}} \\times$\nCross-Fitted\nAttribution\nLayer",
            ha='left', va='center', fontsize=8.2, fontweight='bold', color='#34495E')

    draw_arrow(ax, x_dec, 2.5, x_dec, 3.2)

    # Block 1 Right: Exact TreeSHAP Engine
    draw_box(ax, x_dec, 3.65, 2.4, 0.85, "Exact TreeSHAP",
             r"$\phi_{i,(c,f)} \in \mathbb{R}^{16 \times 10}\ (\mathcal{O}(TLD^2))$",
             bg_color=C_PEACH_BG, border_color=C_PEACH_BORDER, font_size=8.5)

    # Three-prong branch into TreeSHAP (Q, K, V analog)
    ax.text(x_dec - 0.65, 3.0, r"$X$", fontsize=7.5, fontweight='bold', color='#8E44AD')
    ax.text(x_dec, 3.0, r"$M$", fontsize=7.5, fontweight='bold', color='#8E44AD')
    ax.text(x_dec + 0.65, 3.0, r"$T$", fontsize=7.5, fontweight='bold', color='#8E44AD')

    # CROSS-ATTENTION STYLE WIRE: Connect Trained Tree Ensemble from Left into Right TreeSHAP
    ax.plot([x_enc + 1.15, 4.8], [5.45, 5.45], color=C_WIRE, lw=1.2, zorder=2)
    ax.plot([4.8, 4.8], [5.45, 4.2], color=C_WIRE, lw=1.2, zorder=2)
    ax.plot([4.8, x_dec - 1.25], [4.2, 4.2], color=C_WIRE, lw=1.2, zorder=2)
    draw_arrow(ax, x_dec - 1.25, 4.2, x_dec - 1.22, 4.2)
    ax.text(5.0, 4.4, "Trained Ensemble $M_{-p,-j}$", fontsize=7.0, color='#2C3E50',
            fontweight='bold')

    # Add Node Right 1 (Channel Feature Pooling)
    draw_circle_op(ax, x_dec, 4.8, symbol=r"$\oplus$", radius=0.18)
    draw_arrow(ax, x_dec, 4.1, x_dec, 4.6)
    ax.text(x_dec + 0.3, 4.8, r"$\Phi_{i,c} = \sum_{f=1}^{10} |\phi_{i,(c,f)}|$",
            fontsize=7.2, color='#B7950B', va='center', fontweight='bold')

    # Block 2 Right: Magnitude Normalization
    draw_box(ax, x_dec, 5.7, 2.2, 0.55, "Channel Norm", r"$I_{j,c} = \bar{\Phi}_{j,c} / \sum \bar{\Phi}$",
             bg_color=C_YELLOW_BG, border_color=C_YELLOW_BORDER, font_size=8.0)
    draw_arrow(ax, x_dec, 5.0, x_dec, 5.4)

    # Add Node Right 2
    draw_circle_op(ax, x_dec, 6.6, symbol=r"$\oplus$", radius=0.18)
    draw_arrow(ax, x_dec, 6.0, x_dec, 6.4)

    # Residual connection around channel norm
    ax.plot([x_dec + 1.25, x_dec + 1.25], [5.1, 6.6], color=C_WIRE, lw=1.1, zorder=2)
    ax.plot([x_dec + 1.25, x_dec + 0.2], [6.6, 6.6], color=C_WIRE, lw=1.1, zorder=2)
    ax.plot([x_dec, x_dec + 1.25], [5.1, 5.1], color=C_WIRE, lw=1.1, zorder=2)

    # Block 3 Right: Central Tendency & Dispersion Penalty
    draw_box(ax, x_dec, 7.65, 2.4, 0.85, "Cross-Subject Statistics",
             r"$A_c = \operatorname{median}(I_{j,c}),\ U_c = \operatorname{MAD}(I_{j,c})$",
             bg_color=C_BLUE_BG, border_color=C_BLUE_BORDER, font_size=8.2)
    draw_arrow(ax, x_dec, 6.8, x_dec, 7.2)

    # Add Node Right 3: Stability Penalty Multiplier & Subtraction
    # Circle multiplier for lambda
    draw_circle_op(ax, x_dec - 0.65, 8.85, symbol=r"$\otimes$", radius=0.16,
                   bg_color='#FFEDD5', border_color='#EA580C')
    ax.text(x_dec - 1.35, 8.85, r"$\lambda=0.50$", fontsize=7.5, color='#C2410C',
            fontweight='bold', va='center', ha='right')
    draw_arrow(ax, x_dec - 1.25, 8.85, x_dec - 0.83, 8.85)

    # Subtraction Node: Ac - lambda * Uc
    draw_circle_op(ax, x_dec, 8.85, symbol=r"$\ominus$", radius=0.18,
                   bg_color='#EDE9FE', border_color='#7C3AED')
    draw_arrow(ax, x_dec, 8.1, x_dec, 8.65)
    ax.plot([x_dec - 0.52, x_dec - 0.2], [8.85, 8.85], color=C_WIRE, lw=1.1)
    ax.plot([x_dec, x_dec - 0.7], [8.1, 8.1], color=C_WIRE, lw=1.1)
    ax.plot([x_dec - 0.7, x_dec - 0.7], [8.1, 8.67], color=C_WIRE, lw=1.1)

    ax.text(x_dec + 0.3, 8.85, r"$Q_c(\lambda) = A_c - \lambda U_c$",
            fontsize=7.8, color='#6D28D9', va='center', fontweight='bold')

    # Block 4 Right: Norm
    draw_box(ax, x_dec, 9.85, 2.2, 0.55, "Stability Norm", "Ranking Normalization",
             bg_color=C_YELLOW_BG, border_color=C_YELLOW_BORDER, font_size=8.0)
    draw_arrow(ax, x_dec, 9.05, x_dec, 9.55)

    # Arrow leaving Right Container
    draw_arrow(ax, x_dec, 10.15, x_dec, 11.4)

    # Head 1 Right: Top-k Ranking & Masking
    draw_box(ax, x_dec, 11.75, 2.4, 0.65, "Top-$k$ Channel Selector",
             r"$\operatorname{argsort}(-Q_c) \to \mathbf{m}_k \in \{0,1\}^{16}$",
             bg_color=C_PURPLE_BG, border_color=C_PURPLE_BORDER, font_size=8.2)
    draw_arrow(ax, x_dec, 12.1, x_dec, 12.6)

    # Head 2 Right: Pre-Registered Non-Inferiority Testing Gate
    draw_box(ax, x_dec, 12.95, 2.5, 0.65, "Non-Inferiority Decision",
             r"$\text{LCB}_{95\%}(\Delta_k) > -\delta\ (\delta=0.02)$",
             bg_color=C_GREEN_BG, border_color=C_GREEN_BORDER, font_size=8.2)
    draw_arrow(ax, x_dec, 13.3, x_dec, 13.7)

    # Top Output Right
    ax.text(x_dec, 14.05, "Minimal Sparse Topology", ha='center', va='center',
            fontsize=9.0, fontweight='bold', color='#1E8449')
    ax.text(x_dec, 13.78, r"Optimal $k^* = 12$ Channels ($25\%$ Reduction)", ha='center',
            va='center', fontsize=7.5, fontweight='bold', color='#27AE60')

    # Save to artifacts and manuscript figure directories
    fig.savefig(FIG_DIR / "fig2_model_architecture.pdf", dpi=300, bbox_inches='tight')
    fig.savefig(FIG_DIR / "fig2_model_architecture.png", dpi=300, bbox_inches='tight')
    fig.savefig(TEX_FIG_DIR / "fig2_model_architecture.pdf", dpi=300, bbox_inches='tight')
    fig.savefig(TEX_FIG_DIR / "fig2_model_architecture.png", dpi=300, bbox_inches='tight')
    plt.close(fig)
    print("Successfully generated Transformer-style Figure 2 (fig2_model_architecture.pdf/.png)!", flush=True)


if __name__ == "__main__":
    generate_transformer_style_fig2()
