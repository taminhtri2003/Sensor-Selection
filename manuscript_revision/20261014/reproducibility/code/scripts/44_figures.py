"""Result figures, drawn only from result artifacts (no typed values).

Every CI drawn here uses the same participant cluster bootstrap as the statistics
(10,000 resamples, seed 20260728). Participant-level points are shown wherever the figure can
carry them. Outputs go to manuscript/figures/ (PDF + PNG preview).

  fig3_full_channel.pdf        P1: participants per model; paired XGB-SVM differences
  fig4_sparse_curve.pdf        P3/H1: Macro-F1 vs k (all lambda); paired delta vs margins
  fig5_selection_baselines.pdf P4/H2: methods at matched k; SR-CFA percentile in random draws
  fig6_attribution.pdf         P2/P6: channel attribution on the 2x8 montage; rank dispersion
  fig7_faithfulness.pdf        P8/H4: deletion curves, one protocol for all arms
  fig8_generalisation.pdf      exploratory: cross-session, DB5 curve, bipolar curve
"""

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src.semg_sparse.plotting.style import (  # noqa: E402
    PAGE_WIDTH, PALETTE, SERIES, MARKERS, apply_style, panel_label, participant_strip, ci_band)
from src.semg_sparse.statistics.non_inferiority import bootstrap_participant_metrics  # noqa: E402

A = ROOT / "artifacts"
OUT = ROOT / "manuscript" / "figures"
LAMBDAS = (0.0, 0.25, 0.5, 1.0)


def ci(v):
    return bootstrap_participant_metrics(np.asarray(v, float), n_resamples=10000)


def save(fig, name):
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / f"{name}.pdf")
    fig.savefig(OUT / f"{name}.png", dpi=300)
    plt.close(fig)
    print(f"wrote {name}")


def fig3():
    x = pd.read_csv(A / "metrics/loso_full_channel_subject_metrics_xgb.csv")
    s = pd.read_csv(A / "metrics/loso_full_channel_subject_metrics_svmrf.csv")
    d = pd.concat([x, s])
    fig, (a, b) = plt.subplots(1, 2, figsize=(PAGE_WIDTH, 2.9), gridspec_kw={"width_ratios": [1.3, 1]})
    models = [("M_XGBoost", "XGBoost"), ("M_SVM", "RBF-SVM"), ("M_RandomForest", "Random\nforest")]
    wide = d.pivot(index="participant_id", columns="model", values="macro_f1")
    for i in wide.index:
        a.plot(range(3), [wide.loc[i, m] for m, _ in models], color=PALETTE["grey"], lw=0.3, alpha=0.5, zorder=1)
    for j, (mdl, lab) in enumerate(models):
        participant_strip(a, wide[mdl], x=j, color=SERIES[j], seed=j)
        mu, lo, hi = ci(wide[mdl])
        a.errorbar(j + 0.28, mu, yerr=[[mu - lo], [hi - mu]], fmt="D", color=PALETTE["black"], ms=3, capsize=2, lw=0.8)
    a.axhline(1 / 16, color=PALETTE["grey"], ls=":", lw=0.7)
    a.text(2.45, 1 / 16, "chance", fontsize=8, va="bottom", ha="right", color=PALETTE["grey"])
    a.set_xticks(range(3), [l for _, l in models])
    a.set_ylabel("Macro-F1 (held-out participant)")
    a.set_ylim(0, 0.8)
    panel_label(a, "a", dx=0, dy=1.08)
    diff = (wide["M_XGBoost"] - wide["M_SVM"]).sort_values()
    b.bar(range(len(diff)), diff, color=[SERIES[0] if v > 0 else SERIES[1] for v in diff], width=0.8)
    b.axhline(0, color=PALETTE["black"], lw=0.6)
    mu, lo, hi = ci(diff)
    b.axhspan(lo, hi, color=PALETTE["grey"], alpha=0.25, lw=0)
    b.set_xlabel("participant (sorted)")
    b.set_ylabel("XGBoost $-$ SVM Macro-F1")
    b.set_xticks([])
    panel_label(b, "b", dx=0, dy=1.08)
    fig.tight_layout()
    save(fig, "fig3_full_channel")


def fig4():
    c = pd.read_csv(A / "metrics/sparse_curve_subject_metrics.csv")
    fig, (a, b) = plt.subplots(1, 2, figsize=(PAGE_WIDTH, 2.9))
    ks = np.arange(1, 17)
    for j, lam in enumerate(LAMBDAS):
        g = c[np.isclose(c["lambda"], lam)].groupby("channels_k").macro_f1.mean().reindex(ks)
        a.plot(ks, g, marker=MARKERS[j], ms=2.2, lw=0.8, color=SERIES[j], label=f"$\\lambda$ = {lam:g}")
    c0 = c[np.isclose(c["lambda"], 0.0)]
    bands = np.array([ci(c0[c0.channels_k == k].macro_f1)[1:] for k in ks])
    ci_band(a, ks, bands[:, 0], bands[:, 1], color=SERIES[0])
    a.set_xlabel("electrodes retained, $k$")
    a.set_ylabel("Macro-F1 (mean, 95% CI for $\\lambda$=0)")
    a.set_xticks([1, 4, 8, 12, 16])
    a.legend(frameon=False, fontsize=8, loc="lower right")
    panel_label(a, "a", dx=-0.14)
    wide = c0.pivot(index="participant_id", columns="channels_k", values="macro_f1")
    kk = np.arange(1, 16)
    st = np.array([ci(wide[k] - wide[16]) for k in kk])
    b.errorbar(kk, st[:, 0], yerr=[st[:, 0] - st[:, 1], st[:, 2] - st[:, 0]], fmt="o", ms=2.5,
               color=SERIES[0], capsize=1.5, lw=0.8)
    # primary margin dominant; sensitivity margins thin grey with distinct dashes (audit C11)
    for mg, ls, col, lw, lab in ((0.01, ":", PALETTE["grey"], 0.6, "sensitivity"),
                                 (0.02, "--", PALETTE["vermillion"], 1.4, "primary"),
                                 (0.03, "-.", PALETTE["grey"], 0.6, "sensitivity")):
        b.axhline(-mg, color=col, ls=ls, lw=lw)
        b.text(15.6, -mg, f"$-\\delta$={mg:g}\n({lab})", fontsize=8, va="center", ha="left", color=col,
               fontweight="bold" if mg == 0.02 else "normal")
    b.axhline(0, color=PALETTE["black"], lw=0.5)
    b.set_xlim(7.5, 15.5)
    b.set_ylim(-0.06, 0.005)
    b.set_xlabel("electrodes retained, $k$")
    b.set_ylabel("$\\Delta_k$ = F1$_k$ $-$ F1$_{16}$ (95% CI)")
    panel_label(b, "b", dx=-0.16)
    fig.tight_layout()
    save(fig, "fig4_sparse_curve")


def fig5():
    bl = pd.read_csv(A / "selection_baselines/selection_baseline_metrics.csv")
    pc = pd.read_csv(A / "statistics/h2_srcfa_percentile_by_participant.csv")
    # grouped by type: attribution / model-based / data-free / random (audit G-Fig 4)
    methods = [("SRCFA", "SR-CFA ($\\lambda$=0.5)"),
               ("SHAP_lam0", "cross-fitted SHAP ($\\lambda$=0)"),
               ("PERM", "permutation importance"), ("MI", "mutual information"),
               ("GEOM", "geometric (data-free)"), ("RANDOM", "random subsets (mean)")]
    ks = [4, 6, 8, 12]
    fig, (a, b) = plt.subplots(1, 2, figsize=(PAGE_WIDTH, 3.6), gridspec_kw={"width_ratios": [1.5, 1]})
    for j, (mt, lab) in enumerate(methods):
        st = np.array([ci(bl[(bl.method == mt) & (bl.channels_k == k)].macro_f1) for k in ks])
        xs = np.arange(len(ks)) + (j - 2.5) * 0.11
        a.errorbar(xs, st[:, 0], yerr=[st[:, 0] - st[:, 1], st[:, 2] - st[:, 0]], fmt=MARKERS[j],
                   ms=3, color=SERIES[j], capsize=1.2, lw=0.7, label=lab)
    a.set_xticks(range(len(ks)), [str(k) for k in ks])
    a.set_xlabel("electrodes retained, $k$")
    a.set_ylabel("Macro-F1 (mean, 95% CI)")
    panel_label(a, "a", dx=-0.12)
    for j, k in enumerate(ks):
        v = pc[pc.k == k].percentile
        participant_strip(b, v, x=j, color=SERIES[0], seed=k)
    b.axhline(50, color=PALETTE["grey"], ls=":", lw=0.7)
    b.set_xticks(range(len(ks)), [str(k) for k in ks])
    b.set_xlabel("electrodes retained, $k$")
    b.set_ylabel("SR-CFA percentile within the\nparticipant's random subsets")
    b.set_ylim(0, 100)
    panel_label(b, "b", dx=-0.3)
    # one legend for the figure, above both panels, so it cannot squeeze panel a
    h, lab = a.get_legend_handles_labels()
    fig.legend(h, lab, frameon=False, fontsize=8.5, ncol=3, loc="upper center",
               bbox_to_anchor=(0.5, 1.0), columnspacing=1.2, handletextpad=0.3)
    fig.tight_layout(rect=(0, 0, 1, 0.86))
    save(fig, "fig5_selection_baselines")


def fig6():
    sc = pd.read_csv(A / "rankings/cross_fitted_scores.csv")
    fr = pd.read_csv(A / "stability/channel_selection_frequency.csv").set_index("channel")
    Am = sc.pivot(index="outer_participant", columns="channel", values="A_central")
    share = Am.div(Am.sum(axis=1), axis=0).mean() * 100
    fig, (a, b) = plt.subplots(1, 2, figsize=(PAGE_WIDTH, 2.8), gridspec_kw={"width_ratios": [1.2, 1]})
    grid = np.vstack([share.loc[1:8].to_numpy(), share.loc[9:16].to_numpy()])
    im = a.imshow(grid, cmap="Blues", aspect="auto", vmin=0)
    for r in range(2):
        for cc in range(8):
            ch = r * 8 + cc + 1
            a.text(cc, r, f"F{ch}\n{grid[r, cc]:.1f}%", ha="center", va="center", fontsize=7,
                   color="white" if im.norm(grid[r, cc]) > 0.55 else "black")
    a.set_yticks([0, 1], ["ring 1\n(F1-F8)", "ring 2\n(F9-F16)"])
    a.set_xticks(range(8), [str(i) for i in range(1, 9)])
    a.set_xlabel("circumferential position\n(rings shown unwrapped)")
    cb = fig.colorbar(im, ax=a, fraction=0.04, pad=0.02)
    cb.set_label("share of attribution, %", fontsize=8.5)
    panel_label(a, "a", dx=-0.1)
    order = fr.sort_values("median_rank").index
    y = np.arange(len(order))
    b.hlines(y, fr.loc[order, "rank_min"], fr.loc[order, "rank_max"], color=PALETTE["grey"], lw=1.2)
    b.plot(fr.loc[order, "median_rank"], y, "o", color=SERIES[0], ms=3)
    b.set_yticks(y, [f"F{c}" for c in order])
    b.invert_yaxis()
    b.set_xlabel("rank across inner folds\n(median and range)")
    b.set_xticks([1, 4, 8, 12, 16])
    panel_label(b, "b", dx=-0.16)
    fig.tight_layout()
    save(fig, "fig7_attribution")


def fig7():
    d = pd.read_csv(A / "faithfulness/deletion_curves.csv")
    fig, a = plt.subplots(figsize=(PAGE_WIDTH * 0.62, 2.7))
    arms = [("remove_top", "Remove-Top", 0), ("remove_random", "Remove-Random", 4),
            ("remove_bottom", "Remove-Bottom", 2)]
    for arm, lab, j in arms:
        sub = d[d.arm == arm]
        ks = sorted(sub.n_kept.unique())
        st = np.array([ci(sub[sub.n_kept == k].macro_f1) for k in ks])
        a.errorbar(ks, st[:, 0], yerr=[st[:, 0] - st[:, 1], st[:, 2] - st[:, 0]], marker=MARKERS[j],
                   ms=2.8, color=SERIES[j], capsize=1.5, lw=0.8, label=lab)
    a.set_xlabel("electrodes retained")
    a.set_ylabel("Macro-F1 (mean, 95% CI)")
    a.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    save(fig, "fig6_faithfulness")


def fig8():
    cs = pd.read_csv(A / "cross_session/cross_session_metrics.csv")
    db = pd.read_csv(A / "db5/db5_sparse_curve.csv")
    bp = pd.read_csv(A / "bipolar/bipolar_sparse_curve.csv")
    fig = plt.figure(figsize=(PAGE_WIDTH, 4.8))
    grid = fig.add_gridspec(2, 2, hspace=0.35, wspace=0.28)
    a = fig.add_subplot(grid[0, :])
    b = fig.add_subplot(grid[1, 0])
    c = fig.add_subplot(grid[1, 1])
    # (a) cross-session, paired per participant (audit C12)
    conds = [("CS1", 1, "train S1\ntest S1"), ("CS1", 2, "train S1\ntest S2"),
             ("CS1", 3, "train S1\ntest S3"), ("CS2", 3, "train S1+S2\ntest S3")]
    wide = pd.concat({j: cs[(cs.design == dsg) & (cs.test_session == t)].set_index("participant_id").macro_f1
                      for j, (dsg, t, _) in enumerate(conds)}, axis=1)
    for pid in wide.index:
        a.plot(range(3), wide.loc[pid, [0, 1, 2]], color=PALETTE["grey"], lw=0.3, alpha=0.5, zorder=1)
        a.plot([2, 3], wide.loc[pid, [2, 3]], color=PALETTE["grey"], lw=0.3, alpha=0.5, ls="--", zorder=1)
    for j, (dsg, t, lab) in enumerate(conds):
        participant_strip(a, wide[j], x=j, color=SERIES[0 if dsg == "CS1" else 1], seed=j)
    a.set_xticks(range(4), [l for *_, l in conds], fontsize=8)
    a.set_ylabel("Macro-F1 (held-out participant)")
    a.set_title("a", loc="left", fontsize=10, fontweight="bold")
    a.set_title("GRABMyo sessions ($n = 43$)", loc="center", fontsize=8.5)
    # (b-d) paired Delta_k to the same-curve reference with 95% CI vs the primary margin
    for ax, df, ref, title, lab in ((b, db, 16, "NinaPro DB5 ($n = 10$), reference $k = 16$", "b"),
                                    (c, bp[np.isclose(bp["lambda"], 0.0)], 8,
                                     "GRABMyo bipolar pairs ($n = 43$), reference $k = 8$", "c")):
        w = df.pivot(index="participant_id", columns="channels_k", values="macro_f1")
        kk = np.arange(1, ref)
        st = np.array([ci(w[k] - w[ref]) for k in kk])
        ok = st[:, 1] > -0.02
        ax.errorbar(kk, st[:, 0], yerr=[st[:, 0] - st[:, 1], st[:, 2] - st[:, 0]], fmt="none",
                    ecolor=SERIES[0], capsize=1.2, lw=0.7)
        ax.plot(kk[ok], st[ok, 0], "o", ms=3, color=SERIES[0], label="lower bound > $-\\delta$")
        ax.plot(kk[~ok], st[~ok, 0], "o", ms=3, mfc="white", color=SERIES[0], label="lower bound $\\leq -\\delta$")
        ax.axhline(-0.02, color=PALETTE["vermillion"], ls="--", lw=1.4)
        ax.axhline(0, color=PALETTE["black"], lw=0.5)
        lo = max(1, ref // 2 - 1)
        ax.set_xlim(lo - 0.5, ref - 0.5)
        sel = kk >= lo
        ax.set_ylim(min(-0.06, st[sel, 1].min() - 0.005), 0.01)
        ax.set_xlabel("bipolar pairs retained, $k$" if ref == 8 else ("channels retained, $k$" if ref == 16 and lab == "b" else "electrodes retained, $k$"))
        ax.set_ylabel("$\\Delta_k$ (95% CI)")
        ax.set_title(lab, loc="left", fontsize=10, fontweight="bold")
        ax.set_title(title, loc="center", fontsize=8.5)
    c.legend(frameon=False, fontsize=8, loc="lower right")
    fig.tight_layout()
    save(fig, "fig8_generalisation")


def main():
    apply_style()
    figs = {"3": fig3, "4": fig4, "5": fig5, "6": fig6, "7": fig7, "8": fig8}
    only = sys.argv[1:] or list(figs)
    for k in only:
        figs[k]()
    return 0


if __name__ == "__main__":
    sys.exit(main())
