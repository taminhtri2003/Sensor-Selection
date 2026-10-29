"""Generate every LaTeX results table from result artifacts (no typed values).

Outputs manuscript/tables/*.tex. Fails (exit 1) if any input is missing.
  tab_full_channel.tex    P1 per model + paired comparisons
  tab_sparse_ni.tex       P3/H1 (lambda = 0) all k, verdict under each margin
  tab_baselines.tex       P4/H2 at matched k (comparison model)
  tab_faithfulness.tex    P8/H4
  tab_stability.tex       P6
  tab_lambda.tex          H3 (supplementary)
  tab_replication.tex     DB5 and bipolar non-inferiority by k (supplementary)
  tab_cross_session.tex   CS1/CS2 (exploratory)
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


def B(x):
    """revised cell (blue when highlighting is on)"""
    return f"\\rev{{{x}}}"


def table(name, caption, label, colspec, header, rows, star=True, note=None):
    env = "table*" if star else "table"
    lines = [f"\\begin{{{env}}}[t]", "\\centering", "\\small",
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
    names = {"M_XGBoost": "XGBoost", "M_SVM": "RBF-SVM", "M_RandomForest": "Random forest"}
    budget = {"M_XGBoost": B("all"), "M_SVM": B("40{,}000"), "M_RandomForest": B("200{,}000")}

    ms = pd.read_csv(S / "master_statistics.csv")
    full = ms[ms.quantity == "full_channel_macro_f1"].set_index("model")
    rows = [[names[m], budget[m], f3(r.estimate), f"{f3(r.lcb95)}--{f3(r.ucb95)}", f3(r.sd),
             f"{f3(r['min'])}--{f3(r['max'])}"]
            for m, r in full.loc[["M_XGBoost", "M_SVM", "M_RandomForest"]].iterrows()]
    mc = pd.read_csv(S / "model_comparisons.csv")
    note = "Paired comparisons (Wilcoxon signed-rank, Holm over 3): " + "; ".join(
        f"{names[r.model_a]} $-$ {names[r.model_b]} = {d4(r.mean_diff)} "
        f"(95\\% CI {d4(r.lcb95)} to {d4(r.ucb95)}), $p_{{\\mathrm{{Holm}}}}$ {pr(r.p_holm)}, "
        f"$r_{{rb}}$ = {r.effect_size_rank_biserial:+.2f}" for _, r in mc.iterrows()) + "."
    table("tab_full_channel",
          "Full 16-channel leave-one-subject-out performance on GRABMyo (43 participants, 16 active "
          "gestures; chance Macro-F1 $\\approx$ 0.063). CI: 95\\% confidence interval from a "
          "participant cluster bootstrap. RBF-SVM: support vector machine with a radial basis "
          "function kernel.",
          "tab:full_channel", "llcccc",
          "Model & Training windows & Macro-F1 & 95\\% CI & SD & Range", rows, note=note)

    ni = pd.read_csv(S / "non_inferiority_by_k.csv")
    ni = ni[np.isclose(ni["lambda"], 0.0)]
    cur = pd.read_csv(A / "metrics/sparse_curve_subject_metrics.csv")
    cur = cur[np.isclose(cur["lambda"], 0.0)].groupby("channels_k").macro_f1
    hh = pd.read_csv(S / "h1_holm.csv")
    hh = hh[(hh.analysis == "H1") & np.isclose(hh["lambda"], 0.0)]
    rows = []
    for k in range(16, 0, -1):
        row = [str(k), f"{f3(cur.mean()[k])} $\\pm$ {f3(cur.std()[k])}"]
        if k == 16:
            row += ["reference", "", "", "", "", ""]
        else:
            r2 = ni[(ni.k == k) & np.isclose(ni.margin, 0.02)].iloc[0]
            row += [d4(r2.mean_diff), f"{d4(r2.lcb_95)} to {d4(r2.ucb_95)}"]
            for mg in (0.01, 0.02, 0.03):
                ok = ni[(ni.k == k) & np.isclose(ni.margin, mg)].iloc[0].is_non_inferior
                txt = "yes" if ok else "no"
                row.append(f"\\textbf{{{txt}}}" if mg == 0.02 else txt)
            hk = hh[(hh.k == k) & np.isclose(hh.margin, 0.02)].iloc[0]
            row.append(B("yes" if hk.ni_holm else "no"))
        rows.append(row)
    table("tab_sparse_ni",
          "Electrode-count performance curve and non-inferiority on GRABMyo (cross-fitted ranking, "
          "$\\lambda = 0$; 43 "
          "participants; every $k$ retrained from scratch on the same 200,000 training windows of "
          "each fold). $\\Delta_k$ = paired difference to the $k = 16$ model of the same curve. "
          "Non-inferior when the lower 95\\% bound exceeds $-\\delta$; $\\delta = 0.02$ is primary "
          "(bold). " + B("Holm: non-inferiority at $\\delta = 0.02$ after Holm correction over the 15 subset "
          "sizes (supplementary table S1). CI: 95\\% confidence interval."),
          "tab:sparse_ni", "rccccccc",
          "$k$ & Macro-F1 (mean $\\pm$ SD) & $\\Delta_k$ & 95\\% CI & $\\delta$=0.01 & "
          "\\textbf{$\\delta$=0.02 (primary)} & $\\delta$=0.03 & " + B("Holm (0.02)"), rows)

    bl = pd.read_csv(A / "selection_baselines/selection_baseline_summary.csv")
    h2 = pd.read_csv(S / "h2_attribution_vs_random.csv")
    bx = pd.read_csv(S / "baseline_pairwise_exploratory.csv")
    pc = pd.read_csv(S / "h2_srcfa_percentile.csv").set_index("k")
    ks = [4, 6, 8, 12]
    meth = [("SRCFA", "SR-CFA ($\\lambda$=0.5)"), ("SHAP_lam0", "Cross-fitted SHAP ($\\lambda$=0)"),
            ("PERM", "Permutation importance"), ("GEOM", "Geometric farthest-point"),
            ("MI", "Mutual information"), ("RANDOM", "Random subsets (mean)")]
    rows = []
    for mt, lab in meth:
        row = [lab]
        for k in ks:
            r = bl[(bl.method == mt) & (bl.channels_k == k)].iloc[0]
            row.append(f"{f3(r.mean_macro_f1)} $\\pm$ {f3(r.sd)}")
        rows.append(row)
    rows.append(["\\midrule SR-CFA $-$ random (H2)"] + [
        "\\makecell{" + d4(r.mean_diff) + " \\\\ " + B(f"$p$ {pr(r.p_holm)}") + "}" for k in ks
        for r in [h2[(h2.method == 'SRCFA') & (h2.k == k)].iloc[0]]])
    for other in ("PERM", "GEOM"):
        rows.append([f"SR-CFA $-$ {other.lower()}$^\\dagger$"] + [
            "\\makecell{" + d4(r.mean_diff) + " \\\\ " + B(f"$p$ {pr(r.p_raw)}") + "}" for k in ks
            for r in [bx[(bx.comparison == f'SRCFA vs {other}') & (bx.k == k)].iloc[0]]])
    rows.append([B("SR-CFA percentile among random subsets (median)")] + [
        f"{pc.loc[k, 'median_percentile']:.0f} (" + B(f"{int(pc.loc[k, 'n_draws'])} subsets") + ")"
        for k in ks])
    table("tab_baselines",
          "Channel-selection methods at matched $k$ (43 participants). All methods use one "
          "comparison model (XGBoost, 50 trees, 150,000 training windows per fold), so values "
          "are comparable within the table but lower than table~\\ref{tab:sparse_ni}. SR-CFA: "
          "stability-regularised cross-fitted attribution. "
          "H2 $p$ values Holm-corrected over 8 tests; $^\\dagger$exploratory, uncorrected.",
          "tab:baselines", "lcccc", "Method & $k$ = 4 & $k$ = 6 & $k$ = 8 & $k$ = 12", rows)

    h4 = pd.read_csv(S / "h4_faithfulness.csv")
    fs = pd.read_csv(A / "faithfulness/faithfulness_summary.csv")
    rows = []
    for k in sorted(fs.n_kept.unique()):
        g = fs[fs.n_kept == k].set_index("arm").mean_macro_f1
        tb = h4[(h4.k == k) & (h4.comparison == "remove_top - remove_bottom")].iloc[0]
        tr = h4[(h4.k == k) & (h4.comparison == "remove_top - remove_random")]
        rb = h4[(h4.k == k) & (h4.comparison == "remove_random - remove_bottom")]
        rows.append([str(k), f3(g["remove_top"]),
                     f3(g["remove_random"]) if "remove_random" in g else "--",
                     f3(g["remove_bottom"]),
                     f"{d4(tb.mean_diff)} ({p(tb.p_holm)})",
                     f"{d4(tr.iloc[0].mean_diff)} ({p(tr.iloc[0].p_holm)})" if len(tr) else "--",
                     f"{d4(rb.iloc[0].mean_diff)} ({p(rb.iloc[0].p_holm)})" if len(rb) else "--"])
    table("tab_faithfulness",
          "Deletion (remove-and-retrain) faithfulness test (H4; 43 participants). " + B("All deletion "
          "orders use the same comparison model and training sample; Remove-Random averages 100 "
          "random subsets per participant (500 at 12 channels) and is available only where these "
          "were sampled. ")
          + "Differences are paired means with Holm-corrected $p$ in parentheses.",
          "tab:faithfulness", "rcccccc",
          B("Retained") + " & " + B("Remove-Top") + " & " + B("Remove-Random") + " & "
          + B("Remove-Bottom") + " & Top$-$Bottom & Top$-$Random & Random$-$Bottom", rows)

    st = pd.read_csv(A / "stability/stability_summary.csv").set_index("group")
    lab = [("per_subject_STRONGEST", "Per-subject attribution (between people)"),
           ("inner_folds_group_level", "Inner folds (disjoint subject groups)"),
           ("outer_folds_UPPER_BOUND", "Outer folds (overlapping training$^*$)")]
    rows = [[l, str(int(st.loc[g, "n_pairs"])),
             f"{f3(st.loc[g, 'spearman_rho_mean'])} $\\pm$ {f3(st.loc[g, 'spearman_rho_sd'])}",
             f3(st.loc[g, "kendall_tau_mean"]), f3(st.loc[g, "jaccard_top4_mean"]),
             f3(st.loc[g, "jaccard_top6_mean"]), f3(st.loc[g, "jaccard_top8_mean"])] for g, l in lab]
    table("tab_stability", "Agreement of electrode rankings on GRABMyo ($\\lambda = 0$). Values are means over pairs.",
          "tab:stability", "lcccccc",
          "Comparison & Pairs & Spearman $\\rho$ & Kendall $\\tau$ & " + " & ".join(B(f"Jaccard, top {t}") for t in (4, 6, 8)),
          rows, note="$^*$Outer training sets share about 98\\% of their participants, so their "
          "agreement is descriptive, not an independent estimate of between-subject stability.")

    h3 = pd.read_csv(S / "h3_lambda_vs_zero.csv")
    rows = [[f"{r['lambda']:g}", str(int(r.k)), d4(r.mean_diff), f"{d4(r.lcb95)} to {d4(r.ucb95)}",
             f"{int(r.n_tied)}/{int(r.n)}", p(r.p_holm)] for _, r in h3.iterrows()]
    table("tab_lambda", "Stability regularisation versus attribution magnitude alone on GRABMyo (H3): "
          "$Q(\\lambda)$ ranking minus $Q(0)$ ranking on the sparse curve. Tied = participants "
          "for whom both rankings select the identical subset. Holm over 12 tests.",
          "tab:lambda", "rrcccc", "$\\lambda$ & $k$ & Mean diff & 95\\% CI & Tied & $p_{\\mathrm{Holm}}$",
          rows, star=False)

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
          "Cross-session evaluation (exploratory). All conditions are also subject-independent: "
          "the test participant is never in training.", "tab:cross_session", "lcccc",
          "Design & Train sessions & Test session & Train windows & Macro-F1", rows, note=note)
    db = pd.read_csv(S / "db5_non_inferiority_by_k.csv")
    dh = pd.read_csv(S / "h1_holm.csv")
    dh = dh[(dh.analysis == "DB5") & np.isclose(dh.margin, 0.02)].set_index("k")
    rob = pd.read_csv(S / "db5_bootstrap_seed_robustness.csv").set_index("k")
    rows = []
    for k in range(15, 0, -1):
        r = db[(db.k == k) & np.isclose(db.margin, 0.02)].iloc[0]
        rows.append([str(k), f3(r.mean_k), d4(r.mean_diff),
                     B(f"{r.lcb_95:+.6f}".replace("-", "$-$")),
                     "yes" if r.is_non_inferior else "no", B("yes" if dh.loc[k, "ni_holm"] else "no"),
                     f"{100 * rob.loc[k, 'frac_seeds_non_inferior_0.02']:.0f}\\%"])
    table("tab_replication",
          B("NinaPro DB5 channel-count performance curve (exploratory; cross-fitted ranking, $\\lambda = 0$; 10 subjects; "
            "reference $k = 16$, mean Macro-F1 " + f3(db.mean_ref.iloc[0]) + "; margin $\\delta = 0.02$). "
            "Lower 95\\% bound shown to six decimals because the $k = 12$ decision lies at the margin. "
            "Non-inferior: lower bound above $-\\delta$ (uncorrected), and after Holm correction over "
            "15 subset sizes; bootstrap seeds: share of 200 alternative seeds under which $k$ is "
            "non-inferior."),
          "tab:replication", "rcccccc",
          "$k$ & Macro-F1 & $\\Delta_k$ & Lower bound & Non-inf. & Non-inf. (Holm) & Bootstrap seeds",
          rows, star=False)

    bp = pd.read_csv(S / "bipolar_non_inferiority_by_k.csv")
    bp = bp[np.isclose(bp["lambda"], 0.0)]
    brob = pd.read_csv(S / "bipolar_bootstrap_seed_robustness.csv").set_index("k")
    rows = []
    for k in range(7, 0, -1):
        b = bp[(bp.k == k) & np.isclose(bp.margin, 0.02)].iloc[0]
        rows.append([str(k), f3(b.mean_k), d4(b.mean_diff), f"{d4(b.lcb_95)} to {d4(b.ucb_95)}",
                     "yes" if b.is_non_inferior else "no",
                     f"{100 * brob.loc[k, 'frac_seeds_non_inferior_0.02']:.0f}\\%"])
    table("tab_bipolar",
          B("GRABMyo derived bipolar pairs $F_j - F_{j+8}$ (exploratory; 43 participants; "
            "$\\lambda = 0$; count-feature threshold $4 \\times 10^{-3}$~mV). Reference = $k = 8$ "
            "model of the same curve (200,000 training windows), "
            "mean Macro-F1 " + f3(bp.mean_ref.iloc[0]) + "; margin $\\delta = 0.02$; bootstrap "
            "seeds: share of 200 alternative seeds under which $k$ is non-inferior."),
          "tab:bipolar", "rccccc",
          "$k$ & Macro-F1 & $\\Delta_k$ & 95\\% CI & Non-inf. & Bootstrap seeds", rows, star=False)

    # H1 with the plan's Holm correction (post hoc) and fixed sequence (post-hoc sensitivity)
    hh = pd.read_csv(S / "h1_holm.csv")
    h = hh[(hh.analysis == "H1") & np.isclose(hh["lambda"], 0.0) & np.isclose(hh.margin, 0.02)]
    rows = [[str(int(r.k)), d4(r.mean_delta), d4(r.lcb95), p(r.p_boot_one_sided), p(r.p_holm),
             "yes" if r.ni_unadjusted else "no", "yes" if r.ni_holm else "no",
             "yes" if r.ni_fixed_sequence_posthoc else "no"]
            for _, r in h.sort_values("k", ascending=False).iterrows()]
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
          B("H1 with Holm correction over the 15 subset sizes (43 participants, $\\lambda = 0$, "
            "$\\delta = 0.02$). $p$ = one-sided cluster-bootstrap $p$ for $H_0\\colon "
            "\\bar\\Delta_k \\le -\\delta$ (10,000 resamples); Holm over the 15 tested $k$ at "
            "$\\alpha = 0.025$. Fixed sequence (sensitivity analysis): $k = 15, 14, \\ldots$ tested "
            "in order, stopping at the first failure."),
          "tab:h1_holm", "rccccccc",
          "$k$ & $\\bar\\Delta_k$ & Lower bound & $p$ & $p_{\\mathrm{Holm}}$ & Non-inf. & "
          "Non-inf. (Holm) & Fixed sequence",
          rows, star=False, note=B(note))

    return 0


if __name__ == "__main__":
    sys.exit(main())
