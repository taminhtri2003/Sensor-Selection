"""Secondary and remaining confirmatory statistics (H2, H3, H4) plus exploratory analyses.

Every rule is taken from configs/statistics/frozen_analysis_plan.yaml:
  - unit = participant; paired Wilcoxon signed-rank + matched-pairs rank-biserial
  - 10,000-resample participant cluster bootstrap, percentile 95% CI
  - Holm within each confirmatory family (H2, H3, H4); exploratory families are NOT corrected
    and are labelled exploratory

Families and how the plan's under-specified items were resolved (recorded in decision_log.md,
Decision 13, as post-hoc specifications made without reference to which option favoured the
method):
  H2  SR-CFA vs mean of random subsets at every k where random subsets were sampled
      (k = 4, 6, 8, 12). Reported for both attribution rankings that entered P4 (lambda = 0.5 and
      lambda = 0). Also: percentile of SR-CFA within each participant's random distribution.
      The other baselines (PERM, MI, GEOM) are compared descriptively with the same paired test,
      as a separate exploratory family.
  H3  Each lambda > 0 vs lambda = 0 at matched k in the P3 sparse curve (full training budget),
      k in {4, 6, 8, 12}. No lambda* was selected (see Decision 13); all are reported.
  H4  Faithfulness: remove_top < remove_random and remove_random < remove_bottom at the k where
      all three arms exist, plus remove_top < remove_bottom at every k.

Exploratory:
  CS  cross-session: CS1 S1->S2 and S1->S3 vs S1->S1; CS2 (S1+S2 -> S3) vs CS1 (S1 -> S3)
  DB5 non-inferiority at every k against the DB5 k=16 reference, all three margins
  BIP bipolar non-inferiority at every k against the bipolar k=8 curve reference

Outputs (artifacts/statistics/):
  h2_attribution_vs_random.csv, h2_srcfa_percentile.csv, baseline_pairwise_exploratory.csv
  h3_lambda_vs_zero.csv, h4_faithfulness.csv, cross_session_tests.csv,
  db5_non_inferiority_by_k.csv, bipolar_non_inferiority_by_k.csv (when bipolar exists)
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.semg_sparse.statistics.non_inferiority import (  # noqa: E402
    bootstrap_participant_metrics,
    evaluate_non_inferiority,
)

A = ROOT / "artifacts"
OUT = A / "statistics"
N_BOOT = 10000
MARGINS = (0.01, 0.02, 0.03)


def holm(p):
    p = np.asarray(p, float)
    order = np.argsort(p)
    adj = np.empty(len(p))
    running = 0.0
    for rank, idx in enumerate(order):
        running = max(running, (len(p) - rank) * p[idx])
        adj[idx] = min(1.0, running)
    return adj


def rank_biserial(d):
    d = np.asarray(d, float)
    d = d[d != 0]
    if len(d) == 0:
        return 0.0
    r = pd.Series(np.abs(d)).rank().to_numpy()
    return float((r[d > 0].sum() - r[d < 0].sum()) / r.sum())


def paired(a: pd.Series, b: pd.Series, **labels):
    """a - b, aligned on participant id; raises if the participant sets differ."""
    if set(a.index) != set(b.index):
        raise ValueError(f"participant sets differ for {labels}")
    idx = sorted(a.index)
    d = a.loc[idx].to_numpy() - b.loc[idx].to_numpy()
    mean, lcb, ucb = bootstrap_participant_metrics(d, n_resamples=N_BOOT)
    if np.all(d == 0):
        stat, p = np.nan, 1.0
    else:
        stat, p = wilcoxon(d)
    return {**labels, "n": len(d), "mean_a": float(a.loc[idx].mean()),
            "mean_b": float(b.loc[idx].mean()), "mean_diff": mean, "lcb95": lcb, "ucb95": ucb,
            "n_a_better": int((d > 0).sum()), "n_b_better": int((d < 0).sum()),
            "n_tied": int((d == 0).sum()), "wilcoxon_W": float(stat), "p_raw": float(p),
            "rank_biserial": rank_biserial(d)}


def finish(rows, family, correct):
    df = pd.DataFrame(rows)
    df["family"] = family
    if correct:
        df["p_holm"] = holm(df.p_raw)
        df["significant_holm_005"] = df.p_holm < 0.05
    else:
        df["p_holm"] = np.nan
        df["significant_holm_005"] = np.nan
        df["note"] = "exploratory; uncorrected"
    return df


def series(df, **eq):
    sel = df
    for k, v in eq.items():
        sel = sel[np.isclose(sel[k], v)] if isinstance(v, float) else sel[sel[k] == v]
    s = sel.set_index("participant_id").macro_f1
    if s.index.duplicated().any():
        raise ValueError(f"duplicate participant rows for {eq}")
    return s


def h2_and_baselines():
    bl = pd.read_csv(A / "selection_baselines" / "selection_baseline_metrics.csv")
    raw = pd.read_csv(A / "selection_baselines" / "random_subsets_raw.csv")
    rows, expl, pct = [], [], []
    for k in sorted(bl.channels_k.unique()):
        rnd = series(bl, method="RANDOM", channels_k=k)
        for m in ("SRCFA", "SHAP_lam0"):
            rows.append(paired(series(bl, method=m, channels_k=k), rnd,
                               comparison=f"{m} vs RANDOM", method=m, k=int(k)))
        srcfa = series(bl, method="SRCFA", channels_k=k)
        for other in ("PERM", "GEOM", "MI"):
            expl.append(paired(srcfa, series(bl, method=other, channels_k=k),
                               comparison=f"SRCFA vs {other}", method="SRCFA", k=int(k)))
        # percentile of SR-CFA within each participant's own random distribution
        r = raw[raw.channels_k == k]
        for pid, g in r.groupby("participant_id"):
            v = srcfa.loc[pid]
            pct.append({"participant_id": int(pid), "k": int(k), "n_draws": len(g),
                        "srcfa_macro_f1": float(v),
                        "percentile": float((g.macro_f1 < v).mean() * 100
                                            + (g.macro_f1 == v).mean() * 50)})
    h2 = finish(rows, "H2", True)
    ex = finish(expl, "baselines_exploratory", False)
    pct = pd.DataFrame(pct)
    pct_sum = (pct.groupby("k").agg(n_participants=("participant_id", "nunique"),
                                    n_draws=("n_draws", "first"),
                                    median_percentile=("percentile", "median"),
                                    mean_percentile=("percentile", "mean"),
                                    n_above_p50=("percentile", lambda x: int((x > 50).sum())),
                                    n_above_p95=("percentile", lambda x: int((x >= 95).sum())))
               .reset_index())
    h2.to_csv(OUT / "h2_attribution_vs_random.csv", index=False)
    ex.to_csv(OUT / "baseline_pairwise_exploratory.csv", index=False)
    pct.to_csv(OUT / "h2_srcfa_percentile_by_participant.csv", index=False)
    pct_sum.to_csv(OUT / "h2_srcfa_percentile.csv", index=False)
    print("H2\n", h2[["comparison", "k", "mean_diff", "lcb95", "ucb95", "p_holm",
                      "rank_biserial"]].round(4).to_string(index=False))
    print(pct_sum.round(1).to_string(index=False))


def h3():
    cur = pd.read_csv(A / "metrics" / "sparse_curve_subject_metrics.csv")
    rows = []
    for lam in (0.25, 0.5, 1.0):
        for k in (4, 6, 8, 12):
            rows.append(paired(series(cur, **{"lambda": lam}, channels_k=k),
                               series(cur, **{"lambda": 0.0}, channels_k=k),
                               comparison=f"lambda={lam} vs lambda=0", **{"lambda": lam}, k=k))
    df = finish(rows, "H3", True)
    df.to_csv(OUT / "h3_lambda_vs_zero.csv", index=False)
    print("H3\n", df[["lambda", "k", "mean_diff", "lcb95", "ucb95", "n_tied", "p_holm"]]
          .round(4).to_string(index=False))


def h4():
    path = A / "faithfulness" / "deletion_curves.csv"
    if not path.exists():
        print("H4 skipped: faithfulness not computed")
        return
    d = pd.read_csv(path)
    if not (d[d.arm != "remove_random"].source == "computed_p4_protocol").all():
        raise SystemExit("FATAL: faithfulness arms not all computed under the P4 protocol")
    rows = []
    for k in sorted(d.n_kept.unique()):
        top = series(d, arm="remove_top", n_kept=k)
        bot = series(d, arm="remove_bottom", n_kept=k)
        rows.append(paired(top, bot, comparison="remove_top - remove_bottom", k=int(k)))
        if ((d.arm == "remove_random") & (d.n_kept == k)).any():
            rnd = series(d, arm="remove_random", n_kept=k)
            rows.append(paired(top, rnd, comparison="remove_top - remove_random", k=int(k)))
            rows.append(paired(rnd, bot, comparison="remove_random - remove_bottom", k=int(k)))
    df = finish(rows, "H4", True)
    df.to_csv(OUT / "h4_faithfulness.csv", index=False)
    print("H4\n", df[["comparison", "k", "mean_a", "mean_b", "mean_diff", "lcb95", "ucb95",
                      "p_holm"]].round(4).to_string(index=False))


def cross_session():
    cs = pd.read_csv(A / "cross_session" / "cross_session_metrics.csv")
    s11 = series(cs, design="CS1", test_session=1)
    s12 = series(cs, design="CS1", test_session=2)
    s13 = series(cs, design="CS1", test_session=3)
    s23 = series(cs, design="CS2", test_session=3)
    rows = [paired(s12, s11, comparison="CS1: test S2 - test S1"),
            paired(s13, s11, comparison="CS1: test S3 - test S1"),
            paired(s23, s13, comparison="S3 test: CS2 (train S1+S2) - CS1 (train S1)")]
    df = finish(rows, "cross_session_exploratory", False)
    tw = cs.groupby(["design", "test_session"]).n_train_windows.median().to_dict()
    df["train_windows_note"] = f"median outer-training windows {tw}"
    df.to_csv(OUT / "cross_session_tests.csv", index=False)
    print("CS\n", df[["comparison", "mean_diff", "lcb95", "ucb95", "wilcoxon_W", "p_raw",
                      "rank_biserial"]].round(4).to_string(index=False))


def ni_curve(curve, ref_k, tag, lam=None):
    rows = []
    sel = curve if lam is None else curve[np.isclose(curve["lambda"], lam)]
    ref = series(sel, channels_k=ref_k)
    for m in MARGINS:
        for k in sorted(sel.channels_k.unique()):
            if k == ref_k:
                continue
            sk = series(sel, channels_k=k)
            idx = sorted(ref.index)
            res = evaluate_non_inferiority(sk.loc[idx].to_numpy(), ref.loc[idx].to_numpy(),
                                           margin_delta=m, n_resamples=N_BOOT,
                                           participants_k=np.array(idx),
                                           participants_full=np.array(idx))
            rows.append({"analysis": tag, "lambda": lam, "k": int(k), "margin": m,
                         "mean_k": float(sk.mean()), "mean_ref": float(ref.mean()), **res})
    df = pd.DataFrame(rows)
    kstar = (df[df.is_non_inferior].groupby("margin").k.min()
             .reindex(list(MARGINS)))
    print(f"{tag} lambda={lam}: k* by margin = {kstar.to_dict()}  (NaN = no k met the margin)")
    return df


def db5_and_bipolar():
    db5 = pd.read_csv(A / "db5" / "db5_sparse_curve.csv")
    ni_curve(db5, 16, "DB5", lam=0.0).to_csv(OUT / "db5_non_inferiority_by_k.csv", index=False)
    # Robustness of the DB5 decision to the bootstrap seed. The frozen-plan decision uses the
    # plan seed only; this describes how close to the margin each k sits with n = 10.
    ref = series(db5, channels_k=16)
    idx = sorted(ref.index)
    rob = []
    for k in range(1, 16):
        d = series(db5, channels_k=k).loc[idx].to_numpy() - ref.loc[idx].to_numpy()
        lcbs = np.array([bootstrap_participant_metrics(d, n_resamples=N_BOOT, seed=s)[1]
                         for s in range(1000, 1200)])
        rob.append({"k": k, "n_seeds": len(lcbs), "lcb_min": lcbs.min(),
                    "lcb_median": float(np.median(lcbs)), "lcb_max": lcbs.max(),
                    "frac_seeds_non_inferior_0.02": float((lcbs > -0.02).mean())})
    rob = pd.DataFrame(rob)
    rob.to_csv(OUT / "db5_bootstrap_seed_robustness.csv", index=False)
    print(rob.round(4).to_string(index=False))
    bp = A / "bipolar" / "bipolar_sparse_curve.csv"
    if bp.exists():
        b = pd.read_csv(bp)
        if b.participant_id.nunique() != 43:
            print(f"bipolar skipped: {b.participant_id.nunique()}/43 participants")
            return
        out = pd.concat([ni_curve(b, 8, "bipolar", lam=l) for l in sorted(b["lambda"].unique())])
        out.to_csv(OUT / "bipolar_non_inferiority_by_k.csv", index=False)
        # same seed-robustness description as DB5, lambda = 0, reference k = 8
        b0 = b[np.isclose(b["lambda"], 0.0)]
        ref = series(b0, channels_k=8)
        idx = sorted(ref.index)
        rob = []
        for k in range(1, 8):
            d = series(b0, channels_k=k).loc[idx].to_numpy() - ref.loc[idx].to_numpy()
            lcbs = np.array([bootstrap_participant_metrics(d, n_resamples=N_BOOT, seed=s)[1]
                             for s in range(1000, 1200)])
            rob.append({"k": k, "n_seeds": len(lcbs), "lcb_min": lcbs.min(),
                        "lcb_median": float(np.median(lcbs)), "lcb_max": lcbs.max(),
                        "frac_seeds_non_inferior_0.02": float((lcbs > -0.02).mean())})
        rob = pd.DataFrame(rob)
        rob.to_csv(OUT / "bipolar_bootstrap_seed_robustness.csv", index=False)
        print(rob.round(4).to_string(index=False))
    else:
        print("bipolar skipped: not computed")


def boot_p_one_sided(d, margin, seed=20260728):
    """Share of cluster-bootstrap means at or below -margin (H0: mean Delta <= -margin).

    Uses exactly the resampling of bootstrap_participant_metrics, so p < 0.025 corresponds to the
    percentile LCB lying above -margin (up to the discreteness of the 10,000 resamples)."""
    rng = np.random.default_rng(seed)
    idx = rng.choice(len(d), size=(N_BOOT, len(d)), replace=True)
    b = d[idx].mean(axis=1)
    return max(float((b <= -margin).mean()), 1.0 / N_BOOT)


def holm_ni(curve, ref_k, tag, lam=0.0):
    """Holm-adjusted non-inferiority over all k < ref_k (the plan's multiplicity rule, H1).

    Also reports, as a separate post-hoc sensitivity analysis, a fixed-sequence procedure that
    tests k = ref_k - 1, ref_k - 2, ... at one-sided alpha 0.025 and stops at the first failure."""
    sel = curve if lam is None else curve[np.isclose(curve["lambda"], lam)]
    ref = series(sel, channels_k=ref_k)
    idx = sorted(ref.index)
    rows = []
    for m in MARGINS:
        part = []
        for k in range(1, ref_k):
            d = series(sel, channels_k=k).loc[idx].to_numpy() - ref.loc[idx].to_numpy()
            mean, lcb, ucb = bootstrap_participant_metrics(d, n_resamples=N_BOOT)
            part.append({"analysis": tag, "lambda": lam, "margin": m, "k": k, "n": len(d),
                         "mean_delta": mean, "lcb95": lcb, "ucb95": ucb,
                         "p_boot_one_sided": boot_p_one_sided(d, m)})
        p = pd.DataFrame(part)
        p["p_holm"] = holm(p.p_boot_one_sided)
        p["ni_unadjusted"] = p.lcb95 > -m
        p["ni_holm"] = p.p_holm < 0.025
        fs, stop = [], False
        for k in range(ref_k - 1, 0, -1):
            ok = (not stop) and bool(p.loc[p.k == k, "p_boot_one_sided"].iloc[0] < 0.025)
            stop = stop or not ok
            fs.append((k, ok))
        p["ni_fixed_sequence_posthoc"] = p.k.map(dict(fs))
        rows.append(p)
    df = pd.concat(rows, ignore_index=True)
    ks = df.groupby("margin").apply(lambda g: pd.Series({
        "kstar_unadjusted": g.k[g.ni_unadjusted].min(), "kstar_holm": g.k[g.ni_holm].min(),
        "kstar_fixed_sequence": g.k[g.ni_fixed_sequence_posthoc].min()}), include_groups=False)
    print(f"{tag} lambda={lam} k*:\n{ks.to_string()}")
    return df


def h1_holm():
    c = pd.read_csv(A / "metrics" / "sparse_curve_subject_metrics.csv")
    out = [holm_ni(c, 16, "H1", lam=l) for l in sorted(c["lambda"].unique())]
    db5 = pd.read_csv(A / "db5" / "db5_sparse_curve.csv")
    out.append(holm_ni(db5, 16, "DB5", lam=0.0))
    pd.concat(out, ignore_index=True).to_csv(OUT / "h1_holm.csv", index=False)


def putemg():
    P = A / "putemg"
    curve = pd.read_csv(P / "sparse_curve.csv")
    n = curve.participant_id.nunique()
    if n != 44:
        raise SystemExit(f"putEMG incomplete: {n}/44 participants")
    ni = holm_ni(curve, 24, "putEMG", lam=0.0)
    ni.to_csv(OUT / "putemg_non_inferiority_by_k.csv", index=False)
    ref = series(curve, channels_k=24)
    idx = sorted(ref.index)
    rob = []
    for k in range(1, 24):
        d = series(curve, channels_k=k).loc[idx].to_numpy() - ref.loc[idx].to_numpy()
        lcbs = np.array([bootstrap_participant_metrics(d, n_resamples=N_BOOT, seed=s)[1]
                         for s in range(1000, 1200)])
        rob.append({"k": k, "n_seeds": len(lcbs), "lcb_min": lcbs.min(),
                    "lcb_median": float(np.median(lcbs)), "lcb_max": lcbs.max(),
                    "frac_seeds_non_inferior_0.02": float((lcbs > -0.02).mean())})
    pd.DataFrame(rob).to_csv(OUT / "putemg_bootstrap_seed_robustness.csv", index=False)
    rnd = pd.read_csv(P / "random_subsets.csv")
    rows = []
    for k in sorted(rnd.channels_k.unique()):
        rmean = rnd[rnd.channels_k == k].groupby("participant_id").macro_f1.mean()
        rows.append(paired(series(curve, channels_k=int(k)), rmean,
                           comparison=f"ranked vs mean random k={k}", k=int(k)))
    df = finish(rows, "putEMG_vs_random", correct=True)
    df.to_csv(OUT / "putemg_vs_random.csv", index=False)
    print(df[["comparison", "mean_diff", "lcb95", "ucb95", "p_raw", "p_holm"]].round(4).to_string())


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    only = set(sys.argv[1:])
    steps = {"h2": h2_and_baselines, "h3": h3, "h4": h4, "cs": cross_session,
             "ni": db5_and_bipolar, "h1holm": h1_holm, "put": putemg}
    for name, fn in steps.items():
        if not only or name in only:
            fn()
    return 0


if __name__ == "__main__":
    sys.exit(main())
