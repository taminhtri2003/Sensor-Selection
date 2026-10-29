"""Figure style and primitives for publication figures.

Design rules encoded here rather than repeated per figure:
  - vector output (PDF + SVG), text never rasterised
  - column widths in millimetres, so figures are authored at final printed size and legibility
    can be judged honestly instead of from an oversized development PNG
  - colour-blind-safe palette, and colour is never the ONLY channel carrying a distinction —
    markers and line styles vary too
  - no rainbow colormaps, no 3D, no drop shadows, no chart junk
  - participant-level data shown as individual points wherever feasible, because this study's
    central empirical fact is the spread ACROSS people (Macro-F1 0.385-0.702); a bar with an
    error bar would hide exactly what matters most
"""

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

MM = 1 / 25.4
SINGLE_COL = 90 * MM      # ~3.54 in
DOUBLE_COL = 180 * MM     # ~7.09 in
# IOP (Physiological Measurement) is single-column; figures are authored at the text width so
# that the fonts below are the printed sizes (>= 7 pt everywhere).
PAGE_WIDTH = 153 * MM   # iopjournal.cls text width

# Okabe-Ito: colour-blind safe, widely recommended
PALETTE = {
    "blue": "#0072B2", "orange": "#E69F00", "green": "#009E73", "vermillion": "#D55E00",
    "sky": "#56B4E9", "yellow": "#F0E442", "purple": "#CC79A7", "black": "#000000",
    "grey": "#999999",
}
SERIES = [PALETTE[k] for k in ("blue", "orange", "green", "vermillion", "purple", "sky")]
MARKERS = ["o", "s", "^", "D", "v", "P"]
LINESTYLES = ["-", "--", "-.", ":", (0, (3, 1, 1, 1)), (0, (5, 1))]


def apply_style():
    """Install the house style. Call once before creating figures."""
    mpl.rcParams.update({
        "figure.dpi": 150,
        "savefig.dpi": 600,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.01,
        "pdf.fonttype": 42,          # embed as TrueType, keep text selectable/editable
        "ps.fonttype": 42,
        "svg.fonttype": "none",      # never rasterise text in SVG
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
        "font.size": 9,              # final printed size (journal requires 8-12 pt)
        "axes.labelsize": 9,
        "axes.titlesize": 9,
        "xtick.labelsize": 8.5,
        "ytick.labelsize": 8.5,
        "legend.fontsize": 8.5,
        "mathtext.fontset": "custom",   # math in the same typeface as the text
        "mathtext.rm": "Arial",
        "mathtext.it": "Arial:italic",
        "mathtext.bf": "Arial:bold",
        "mathtext.sf": "Arial",
        "axes.linewidth": 0.6,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": False,
        "xtick.major.width": 0.6,
        "ytick.major.width": 0.6,
        "xtick.major.size": 2.5,
        "ytick.major.size": 2.5,
        "lines.linewidth": 1.0,
        "lines.markersize": 3,
        "legend.frameon": False,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
    })


def figure(width=SINGLE_COL, height=None, **kw):
    """Create a figure at final printed width."""
    return plt.subplots(figsize=(width, height or width * 0.72), **kw)


def panel_label(ax, letter, dx=-0.18, dy=1.04):
    """Panel label in a consistent position across every figure."""
    ax.text(dx, dy, letter, transform=ax.transAxes, fontsize=10, fontweight="bold",
            va="top", ha="left")


def participant_strip(ax, values, x=0.0, color=PALETTE["blue"], jitter=0.06, seed=0,
                      show_median=True):
    """Individual participants as jittered points, with the median marked.

    Deliberately not a bar chart: the point of this study's baseline figure is that participants
    span 0.385-0.702, and a mean +/- SD bar conceals that. Jitter is seeded so the figure is
    reproducible.
    """
    rng = np.random.default_rng(seed)
    v = np.asarray(values, dtype=float)
    xs = x + rng.uniform(-jitter, jitter, size=len(v))
    ax.plot(xs, v, "o", color=color, markersize=3, alpha=0.65, markeredgewidth=0,
            zorder=2, clip_on=False)
    if show_median:
        med = float(np.median(v))
        ax.plot([x - 0.18, x + 0.18], [med, med], "-", color=PALETTE["black"],
                linewidth=1.2, zorder=3, solid_capstyle="butt")
    return float(np.median(v))


def ci_band(ax, x, lower, upper, color=PALETTE["blue"], alpha=0.18, label=None):
    ax.fill_between(x, lower, upper, color=color, alpha=alpha, linewidth=0, label=label,
                    zorder=1)


def margin_line(ax, y, label="non-inferiority margin", color=PALETTE["vermillion"]):
    """Draw the prespecified margin. Always labelled so no reader mistakes it for data."""
    ax.axhline(y, color=color, linestyle="--", linewidth=0.8, zorder=1)
    ax.text(ax.get_xlim()[1], y, f" {label}", color=color, fontsize=8,
            va="center", ha="left")


def save(fig, path_stem, formats=("pdf", "svg", "png")):
    """Write vector formats plus a raster preview. Returns the paths written."""
    written = []
    for ext in formats:
        p = f"{path_stem}.{ext}"
        fig.savefig(p, format=ext)
        written.append(p)
    return written


def caption_stats(n, unit="participants", centre="median", spread="individual points shown"):
    """Standard caption fragment so every figure states n, the statistical unit and what is drawn."""
    return (f"n = {n} {unit}; the statistical unit is the {unit[:-1]}. "
            f"Centre line is the {centre}; {spread}.")
