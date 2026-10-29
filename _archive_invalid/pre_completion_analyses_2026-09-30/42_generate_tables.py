"""Generate every LaTeX results table from result artifacts (no typed values).

Outputs manuscript/tables/*.tex. Fails (exit 1) if any input is missing.
Main manuscript:
  tab_sparse_ni.tex       H1 primary decision (delta = 0.02), lambda = 0, all k
  tab_h2.tex              H2 confirmatory family (both attribution rankings vs random mean)
  tab_stability.tex       ranking agreement (descriptive)
Supplementary material:
  tab_full_channel.tex    full-array classifier comparison
  tab_h1_holm.tex         H1: Holm, fixed sequence and sensitivity margins
  tab_selection_explor.tex exploratory selection-method contrasts (perm, geom, MI)
  tab_faithfulness.tex    H4 deletion with retraining, all contrasts
  tab_lambda.tex          H3
  tab_replication.tex     NinaPro DB5
  tab_cross_session.tex   CS1/CS2
  tab_bipolar.tex         derived bipolar pairs
Captions revised in the 2026-09-23 editorial revision are wrapped in \\chg{} (blue when marking is on).
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
A = ROOT / "artifacts"
S = A / "statistics"
OUT = ROOT / "manuscript" / "tables"


def p(x):
    return "$<$0.001" if x < 0.001 else f"{x:.3f}"


def pr(x):
    """p with its relation, for running text"""
    return "$<$ 0.001" if x < 0.001 else f"= {x:.3f}"


def d4(x):
    return f"{x:+.4f}".replace("-", "$-$")


def f3(x):
    return f"{x:.3f}"


def rb(x):
    return f"{x:+.2f}".replace("-", "$-$")


def C(x):
    """caption or cell revised in the 2026-09-23 editorial revision"""
    return f"\\chg{{{x}}}"


def seeds(frac, n):
    hits = int(round(frac * n))
    return f"{hits}/{n} ({100 * hits / n:.1f}\\%)"


def table(name, caption, label, colspec, header, rows, star=True, note=None, pos="t"):
    env = "table*" if star else "table"
    lines = [f"\\begin{{{env}}}[{pos}]", "\\centering", "\\small",
             f"\\caption{{{caption}}}", f"\\label{{{label}}}",
             "\\setlength{\\tabcolsep}{4pt}", "\\begin{adjustbox}{max width=\\textwidth}",
             f"\\begin{{tabular}}{{{colspec}}}", "\\toprule", header + " \\\\", "\\midrule"]
    lines += [" & ".join(r) + " \\\\" for r in rows]
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{adjustbox}"]
    if note:
        lines += [f"\\par\\smallskip\\parbox{{0.95\\linewidth}}{{\\footnotesize {note}}}"]
    lines += [f"\\end{{{env}}}", ""]
    (OUT / f"{name}.tex").write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {name}")


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    # ---------------- supplementary: full-array classifier comparison ----------------
    names = {"M_XGBoost": "XGBoost", "M_SVM": "RBF-SVM", "M_RandomForest": "Random forest"}
    xgb_windows = pd.read_csv(A / "metrics/loso_full_channel_subject_metrics_xgb.csv").n_train_windows
    if xgb_windows.nunique() != 1:
        raise ValueError("XGBoost training-window count differs between folds")
    budget = {"M_XGBoost": C(f"all ({int(xgb_windows.iloc[0]):,} per fold)".replace(",", "{,}")),
              "M_SVM": "40{,}000", "M_RandomForest": "200{,}000"}
    ms = pd.read_csv(S / "master_statistics.csv")
    full = ms[ms.quantity == "full_channel_macro_f1"].set_index("model")
    rows = [[names[m], budget[m], f3(r.estimate), f"{f3(r.lcb95)}--{f3(r.ucb95)}", f3(r.sd),
             f"{f3(r['min'])}--{f3(r['max'])}"]
            for m, r in full.loc[["M_XGBoost", "M_SVM", "M_RandomForest"]].iterrows()]
    mc = pd.read_csv(S / "model_comparisons.csv")
    note = "Paired comparisons (Wilcoxon signed-rank, Holm over 3): " + "; ".join(
        f"{names[r.model_a]} $-$ {names[r.model_b]} = {d4(r.mean_diff)} "
        f"(95\\% CI {d4(r.lcb95)} to {d4(r.ucb95)}), $p_{{\\mathrm{{Holm}}}}$ {pr(r.p_holm)}, "
        f"$r_{{rb}}$ = {rb(r.effect_size_rank_biserial)}" for _, r in mc.iterrows()) + "."
    table("tab_full_channel",
          C("Full-array (16-electrode) leave-one-subject-out performance of three classifiers on "
            "GRABMyo (43 participants, 16 active gestures; chance Macro-F1 $\\approx$ 0.063). "
            "CI: 95\\% participant cluster-bootstrap confidence interval. RBF-SVM: support vector "
            "machine with a radial basis function kernel. Training windows: windows used to fit "
            "each fold's model."),
          "tab:full_channel", "llcccc",
          "Model & Training windows & Macro-F1 & 95\\% CI & SD & Range", rows, note=note, pos="htbp")

    # ---------------- main: H1 primary decision ----------------
    ni = pd.read_csv(S / "non_inferiority_by_k.csv")
    ni = ni[np.isclose(ni["lambda"], 0.0)]
    cur = pd.read_csv(A / "metrics/sparse_curve_subject_metrics.csv")
    cur = cur[np.isclose(cur["lambda"], 0.0)].groupby("channels_k").macro_f1
    hh = pd.read_csv(S / "h1_holm.csv")
    h1 = hh[(hh.analysis == "H1") & np.isclose(hh["lambda"], 0.0)]
    kstar = int(ni[np.isclose(ni.margin, 0.02) & ni.is_non_inferior & (ni.k < 16)].k.min())
    rows = []
    for k in range(16, 0, -1):
        row = [str(k), f"{f3(cur.mean()[k])} $\\pm$ {f3(cur.std()[k])}"]
        if k == 16:
            row += ["reference", "", "", ""]
        else:
            r2 = ni[(ni.k == k) & np.isclose(ni.margin, 0.02)].iloc[0]
            hk = h1[(h1.k == k) & np.isclose(h1.margin, 0.02)].iloc[0]
            row += [d4(r2.mean_diff), f"{d4(r2.lcb_95)} to {d4(r2.ucb_95)}",
                    "yes" if r2.is_non_inferior else "no", "yes" if hk.ni_holm else "no"]
        if k == kstar:
            row = [f"\\textbf{{{c}}}" if c else c for c in row]
        if k == kstar - 1:
            row[0] = "\\midrule " + row[0]
        rows.append(row)
    table("tab_sparse_ni",
          C("Electrode-count performance curve and primary non-inferiority decision on GRABMyo "
            "(cross-fitted ranking, $\\lambda = 0$; 43 participants; every $k$ retrained from "
            "scratch on the same 200,000 training windows of each fold). $\\Delta_k$: mean "
            "paired difference from the $k = 16$ model of the same curve, with 95\\% "
            "participant cluster-bootstrap confidence interval (CI). Non-inferior: lower bound "
            "above $-\\delta$ with the primary margin $\\delta = 0.02$; Holm: the same decision "
            "after Holm correction over the 15 subset sizes. The smallest non-inferior subset "
            "($k^*$) is in bold; the rule below it marks the boundary. Decisions at the "
            "sensitivity margins $\\delta = 0.01$ and 0.03 are given in supplementary table S3."),
          "tab:sparse_ni", "rccccc",
          "$k$ & Macro-F1 (mean $\\pm$ SD) & $\\Delta_k$ & 95\\% CI & Non-inferior & "
          "Non-inferior (Holm)", rows)

    # ---------------- supplementary: H1 Holm, fixed sequence, sensitivity margins ----------------
    h = h1[np.isclose(h1.margin, 0.02)]
    rows = []
    for _, r in h.sort_values("k", ascending=False).iterrows():
        k = int(r.k)
        sens = []
        for mg in (0.01, 0.03):
            s = h1[(h1.k == k) & np.isclose(h1.margin, mg)].iloc[0]
            sens.append(f"{'yes' if s.ni_unadjusted else 'no'} / {'yes' if s.ni_holm else 'no'}")
        rows.append([str(k), d4(r.mean_delta), d4(r.lcb95), p(r.p_boot_one_sided), p(r.p_holm),
                     "yes" if r.ni_unadjusted else "no", "yes" if r.ni_holm else "no",
                     "yes" if r.ni_fixed_sequence_posthoc else "no"] + sens)
    ks = hh[hh.analysis == "H1"].groupby(["lambda", "margin"]).apply(
        lambda g: pd.Series({"u": g.k[g.ni_unadjusted].min(), "h": g.k[g.ni_holm].min(),
                             "f": g.k[g.ni_fixed_sequence_posthoc].min()}), include_groups=False)
    note = "$k^*$ (unadjusted / Holm / fixed sequence) at $\\lambda = 0$: " + "; ".join(
        f"$\\delta$ = {mg:g}: {int(ks.loc[(0.0, mg), 'u'])} / {int(ks.loc[(0.0, mg), 'h'])} / "
        f"{int(ks.loc[(0.0, mg), 'f'])}" for mg in (0.01, 0.02, 0.03))
    same = all(ks.xs(mg, level="margin").nunique().max() == 1 for mg in (0.01, 0.02, 0.03))
    note += ("; identical for all four $\\lambda$." if same
             else "; not identical across all $\\lambda$.")
    table("tab_h1_holm",
          C("H1 decisions under multiplicity correction and sensitivity margins (GRABMyo, 43 "
            "participants, $\\lambda = 0$). $\\bar\\Delta_k$ and lower 95\\% bound as in main "
            "table~1. $p$: one-sided cluster-bootstrap $p$ for $H_0\\colon \\bar\\Delta_k \\le "
            "-\\delta$ at the primary margin $\\delta = 0.02$ (10,000 resamples); Holm over the 15 "
            "subset sizes at $\\alpha = 0.025$. Fixed sequence (post-hoc sensitivity analysis): "
            "$k = 15, 14, \\ldots$ tested in order, stopping at the first failure. The last two "
            "columns give the non-inferiority decision (unadjusted / Holm) at the prespecified "
            "sensitivity margins."),
          "tab:h1_holm", "rcccccccccc",
          "$k$ & $\\bar\\Delta_k$ & Lower bound & $p$ & $p_{\\mathrm{Holm}}$ & Non-inf. & "
          "Non-inf. (Holm) & Fixed sequence & $\\delta = 0.01$ & $\\delta = 0.03$",
          rows, note=note, pos="htbp")

    # ---------------- main: H2 confirmatory family ----------------
    h2 = pd.read_csv(S / "h2_attribution_vs_random.csv")
    if len(h2) != 8 or set(h2.method) != {"SRCFA", "SHAP_lam0"}:
        raise ValueError("H2 family is not the documented 8 tests")
    lab = {"SHAP_lam0": "Cross-fitted SHAP ($\\lambda = 0$)", "SRCFA": "SR-CFA ($\\lambda = 0.5$)"}
    rows = []
    for k in (4, 6, 8, 12):
        for i, mt in enumerate(("SHAP_lam0", "SRCFA")):
            r = h2[(h2.method == mt) & (h2.k == k)].iloc[0]
            rows.append([(("\\midrule " if k != 4 else "") + str(k)) if i == 0 else "", lab[mt],
                         f3(r.mean_a), f3(r.mean_b), d4(r.mean_diff),
                         f"{d4(r.lcb95)} to {d4(r.ucb95)}",
                         f"{int(r.n_a_better)}/{int(r.n_b_better)}", p(r.p_holm), rb(r.rank_biserial)])
    table("tab_h2",
          C("H2: attribution-ranked subsets versus the mean of matched random subsets (GRABMyo, "
            "43 participants; secondary test family of 8 tests, Holm-corrected; the detailed family was specified after the underlying results were available). All subsets were "
            "evaluated with one comparison model (XGBoost, 50 trees, 150,000 training windows per "
            "fold), so absolute values are lower than in table~\\ref{tab:sparse_ni}. Random: "
            "participant's mean over 100 random subsets (500 at $k = 12$). Difference: mean paired "
            "difference (attribution minus random) with 95\\% participant cluster-bootstrap "
            "confidence interval (CI). Higher/lower: participants for whom the attribution subset "
            "scored above/below their random mean. $p_{\\mathrm{Holm}}$: Wilcoxon signed-rank, "
            "Holm-corrected; $r_{rb}$: matched-pairs rank-biserial correlation."),
          "tab:h2", "rlccccccc",
          "$k$ & Ranking & Attribution & Random & Difference & 95\\% CI & Higher/lower & "
          "$p_{\\mathrm{Holm}}$ & $r_{rb}$", rows)

    # ---------------- supplementary: exploratory selection-method contrasts ----------------
    bx = pd.read_csv(S / "baseline_pairwise_exploratory.csv")
    cl = {"PERM": "Permutation importance", "GEOM": "Geometric farthest-point",
          "MI": "Mutual information"}
    rows = []
    for k in (4, 6, 8, 12):
        for i, other in enumerate(("PERM", "GEOM", "MI")):
            r = bx[(bx.comparison == f"SRCFA vs {other}") & (bx.k == k)].iloc[0]
            rows.append([(("\\midrule " if k != 4 else "") + str(k)) if i == 0 else "", cl[other],
                         f3(r.mean_a), f3(r.mean_b), d4(r.mean_diff),
                         f"{d4(r.lcb95)} to {d4(r.ucb95)}", p(r.p_raw), rb(r.rank_biserial)])
    table("tab_selection_explor",
          C("Exploratory comparisons of SR-CFA ($\\lambda = 0.5$) with other electrode-selection "
            "methods (GRABMyo, 43 participants; same comparison model as main table~2). "
            "Difference: SR-CFA minus comparator, mean paired difference with 95\\% participant "
            "cluster-bootstrap confidence interval (CI). $p$: Wilcoxon signed-rank, uncorrected; "
            "$r_{rb}$: matched-pairs rank-biserial correlation. These contrasts are exploratory "
            "and were not corrected for multiplicity."),
          "tab:selection_explor", "rlcccccc",
          "$k$ & Comparator & SR-CFA & Comparator & Difference & 95\\% CI & $p$ & $r_{rb}$",
          rows, star=False, pos="htbp")

    # ---------------- supplementary: H4 ----------------
    h4 = pd.read_csv(S / "h4_faithfulness.csv")
    cn = {"remove_top - remove_bottom": "Top $-$ Bottom", "remove_top - remove_random": "Top $-$ Random",
          "remove_random - remove_bottom": "Random $-$ Bottom"}
    order = list(cn)
    h4 = h4.assign(o=h4.comparison.map(order.index)).sort_values(["k", "o"])
    rows, last = [], None
    for _, r in h4.iterrows():
        k = int(r.k)
        first = "" if k == last else (("\\midrule " if last is not None else "") + str(k))
        last = k
        rows.append([first, cn[r.comparison], f3(r.mean_a), f3(r.mean_b), d4(r.mean_diff),
                     f"{d4(r.lcb95)} to {d4(r.ucb95)}", p(r.p_holm), rb(r.rank_biserial)])
    table("tab_faithfulness",
          C("H4: deletion with retraining (GRABMyo, 43 participants). Retained: electrodes kept "
            "after deletion. Remove-Top, Remove-Bottom and Remove-Random delete the highest-ranked, "
            "lowest-ranked or randomly chosen electrodes; Remove-Random uses the random subsets of "
            "the H2 comparison and exists only where these were sampled. All orders use the same "
            "comparison model and training sample. Difference: mean paired difference (first "
            "minus second order) with 95\\% participant cluster-bootstrap confidence interval (CI); "
            "negative values follow the expected ordering. $p_{\\mathrm{Holm}}$: Wilcoxon "
            "signed-rank, Holm over the 15 contrasts; $r_{rb}$: matched-pairs rank-biserial "
            "correlation."),
          "tab:faithfulness", "rlcccccc",
          "Retained & Contrast & First & Second & Difference & 95\\% CI & $p_{\\mathrm{Holm}}$ & $r_{rb}$",
          rows, star=False, pos="htbp")

    # ---------------- main: ranking agreement ----------------
    st = pd.read_csv(A / "stability/stability_summary.csv").set_index("group")
    lab = [("per_subject_STRONGEST", "Individual participants"),
           ("inner_folds_group_level", "Inner folds (disjoint participant groups)"),
           ("outer_folds_UPPER_BOUND", "Outer folds (overlapping training sets$^*$)")]

    def ms_(g, m):
        return f"{f3(st.loc[g, m + '_mean'])} ({f3(st.loc[g, m + '_sd'])})"

    rows = [[l, str(int(st.loc[g, "n_pairs"])), ms_(g, "spearman_rho"), ms_(g, "kendall_tau"),
             ms_(g, "jaccard_top4"), ms_(g, "jaccard_top6"), ms_(g, "jaccard_top8")] for g, l in lab]
    table("tab_stability",
          C("Agreement of electrode rankings on GRABMyo ($\\lambda = 0$). Values are mean (SD) "
            "over all pairs of rankings in each group. They are descriptive summaries: pairwise "
            "observations share rankings and are not independent, so no inferential interval is "
            "given."),
          "tab:stability", "lcccccc",
          "Rankings compared & Pairs & Spearman $\\rho$ & Kendall $\\tau$ & Jaccard, top 4 & "
          "Jaccard, top 6 & Jaccard, top 8",
          rows, note="$^*$Outer training sets share about 98\\% of their participants, so their "
          "agreement is descriptive only and is not an estimate of between-participant stability.")

    # ---------------- supplementary: H3 ----------------
    h3 = pd.read_csv(S / "h3_lambda_vs_zero.csv")
    rows = [[f"{r['lambda']:g}", str(int(r.k)), d4(r.mean_diff), f"{d4(r.lcb95)} to {d4(r.ucb95)}",
             f"{int(r.n_tied)}/{int(r.n)}", p(r.p_holm),
             "--" if int(r.n_tied) == int(r.n) else rb(r.rank_biserial)] for _, r in h3.iterrows()]
    table("tab_lambda",
          C("H3: stability-regularised ranking ($\\lambda > 0$) minus magnitude-only ranking "
            "($\\lambda = 0$) on the electrode-count performance curve (GRABMyo, 43 participants). "
            "Mean paired difference with 95\\% participant cluster-bootstrap confidence interval "
            "(CI). Tied: participants for whom both rankings select the identical subset. "
            "$p_{\\mathrm{Holm}}$: Wilcoxon signed-rank, Holm over 12 tests. $r_{rb}$ is computed "
            "from untied participants only and is undefined (--) when all are tied; with most "
            "participants tied it is not informative about magnitude."),
          "tab:lambda", "rrccccc",
          "$\\lambda$ & $k$ & Mean difference & 95\\% CI & Tied & $p_{\\mathrm{Holm}}$ & $r_{rb}$",
          rows, star=False, pos="htbp")

    # ---------------- supplementary: DB5 ----------------
    db = pd.read_csv(S / "db5_non_inferiority_by_k.csv")
    dh = pd.read_csv(S / "h1_holm.csv")
    dh = dh[(dh.analysis == "DB5") & np.isclose(dh.margin, 0.02)].set_index("k")
    rob = pd.read_csv(S / "db5_bootstrap_seed_robustness.csv").set_index("k")
    rows = []
    for k in range(15, 0, -1):
        r = db[(db.k == k) & np.isclose(db.margin, 0.02)].iloc[0]
        rows.append([str(k), f3(r.mean_k), d4(r.mean_diff),
                     f"{r.lcb_95:+.6f}".replace("-", "$-$"),
                     "yes" if r.is_non_inferior else "no", "yes" if dh.loc[k, "ni_holm"] else "no",
                     seeds(rob.loc[k, "frac_seeds_non_inferior_0.02"], int(rob.loc[k, "n_seeds"]))])
    table("tab_replication",
          C("NinaPro DB5 channel-count performance curve (exploratory replication; cross-fitted "
            "ranking, $\\lambda = 0$; 10 subjects; reference $k = 16$, mean Macro-F1 "
            + f3(db.mean_ref.iloc[0]) + "; margin $\\delta = 0.02$). The lower 95\\% bound is "
            "shown to six decimals because the $k = 12$ decision lies at the margin. Non-inferior: "
            "lower bound above $-\\delta$, unadjusted and after Holm correction over 15 subset "
            "sizes. Bootstrap reruns: number of 200 reruns of the bootstrap with different random "
            "seeds in which the unadjusted decision was non-inferior. This is a Monte Carlo "
            "decision-stability diagnostic, not a probability that the hypothesis is true."),
          "tab:replication", "rcccccc",
          "$k$ & Macro-F1 & $\\Delta_k$ & Lower bound & Non-inf. & Non-inf. (Holm) & "
          "Non-inf. in bootstrap reruns",
          rows, star=False, pos="htbp")

    # ---------------- supplementary: cross-session ----------------
    cs = pd.read_csv(A / "cross_session/cross_session_metrics.csv")
    ct = pd.read_csv(S / "cross_session_tests.csv")
    rows = []
    for (dsg, t), g in cs.groupby(["design", "test_session"]):
        trs = "1" if dsg == "CS1" else "1+2"
        rows.append([dsg, trs, str(t), f"{int(g.n_train_windows.median()):,}".replace(",", "{,}"),
                     f"{f3(g.macro_f1.mean())} $\\pm$ {f3(g.macro_f1.std())}"])
    note = "Paired contrasts (exploratory, uncorrected): " + "; ".join(
        f"{r.comparison.replace('-', '$-$')}: {d4(r.mean_diff)} (95\\% CI {d4(r.lcb95)} to "
        f"{d4(r.ucb95)}), $p$ {pr(r.p_raw)}" for _, r in ct.iterrows()) + "."
    table("tab_cross_session",
          "Cross-session evaluation on GRABMyo (exploratory; full array). All conditions are also "
          "subject-independent: the test participant is never in training.", "tab:cross_session",
          "lcccc", "Design & Train sessions & Test session & Train windows & Macro-F1", rows,
          note=note, star=False, pos="htbp")

    # ---------------- supplementary: bipolar ----------------
    bp = pd.read_csv(S / "bipolar_non_inferiority_by_k.csv")
    bp = bp[np.isclose(bp["lambda"], 0.0)]
    brob = pd.read_csv(S / "bipolar_bootstrap_seed_robustness.csv").set_index("k")
    bfull = pd.read_csv(A / "bipolar/bipolar_full_channel_metrics.csv")
    bfull = bfull[bfull.channels_k == 8]
    if bfull.n_train_windows.nunique() != 1:
        raise ValueError("bipolar full-array training-window count differs between folds")
    rows = []
    for k in range(7, 0, -1):
        b = bp[(bp.k == k) & np.isclose(bp.margin, 0.02)].iloc[0]
        rows.append([str(k), f3(b.mean_k), d4(b.mean_diff), f"{d4(b.lcb_95)} to {d4(b.ucb_95)}",
                     "yes" if b.is_non_inferior else "no",
                     seeds(brob.loc[k, "frac_seeds_non_inferior_0.02"], int(brob.loc[k, "n_seeds"]))])
    table("tab_bipolar",
          C("GRABMyo derived bipolar pairs $F_j - F_{j+8}$ (exploratory; 43 participants; "
            "$\\lambda = 0$; count-feature threshold $4 \\times 10^{-3}$~mV; margin $\\delta = "
            "0.02$). Reference: the $k = 8$ model of the same curve, trained on the curve's "
            "200,000-window sample (mean Macro-F1 " + f3(bp.mean_ref.iloc[0]) + "). The full-array "
            "bipolar value reported in the main text (" + f3(bfull.macro_f1.mean()) + ") comes "
            "from a separate model trained on all "
            + f"{int(bfull.n_train_windows.iloc[0]):,}".replace(",", "{,}") + " training windows "
            "of each fold, as for the monopolar analysis. $\\Delta_k$: mean paired difference with "
            "95\\% participant cluster-bootstrap confidence interval (CI). Bootstrap reruns: as in "
            "supplementary table~S8."),
          "tab:bipolar", "rccccc",
          "$k$ & Macro-F1 & $\\Delta_k$ & 95\\% CI & Non-inf. & Non-inf. in bootstrap reruns",
          rows, star=False, pos="htbp")

    for stale in ("tab_baselines.tex",):
        f = OUT / stale
        if f.exists():
            f.unlink()
            print(f"removed superseded {stale} (archived copy in _archive_invalid)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
