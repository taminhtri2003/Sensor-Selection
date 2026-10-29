"""Attribution stability: do channel rankings actually agree across people?

A methodological warning this script exists to enforce:

The 43 outer-fold rankings R_{-p} each derive from 42 of the same 43 participants, so any two of
them share ~98% of their training data. Correlating R_{-p} against R_{-q} therefore measures
almost nothing about between-subject variability -- it is near-guaranteed to look "highly stable",
and reporting it as evidence of cross-subject stability would be misleading. The literature
routinely does exactly this.

The honest substrate is the INNER-fold importance matrix from P2: within one outer fold, each
inner fold attributes on a disjoint set of held-out participants. Variation across those folds is
genuine between-subject variation.

This script computes both and labels them accordingly:
  - inner-fold agreement  -> the real cross-subject stability estimate (primary)
  - outer-fold agreement  -> reported only as an upper bound / sanity check, explicitly caveated

Outputs:
  artifacts/stability/inner_fold_agreement.csv     primary
  artifacts/stability/outer_fold_agreement.csv     caveated upper bound
  artifacts/stability/channel_selection_frequency.csv
  artifacts/stability/stability_summary.csv
"""

import sys
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import kendalltau, spearmanr

ROOT = Path(__file__).resolve().parent.parent
RANK = ROOT / "artifacts" / "rankings"
OUT = ROOT / "artifacts" / "stability"
TOP_KS = (4, 6, 8)
N_CHANNELS = 16


def ranking_from_scores(values):
    """Channel ids (1-based) ordered most to least important, deterministic tie-break."""
    v = np.asarray(values, dtype=float)
    return [int(c) + 1 for c in np.lexsort((np.arange(len(v)), -v))]


def jaccard(a, b):
    sa, sb = set(a), set(b)
    return len(sa & sb) / len(sa | sb) if (sa | sb) else np.nan


def pairwise_agreement(rankings, label):
    """Spearman/Kendall on rank vectors, plus Jaccard of the top-k sets."""
    rows = []
    for (i, ri), (j, rj) in combinations(list(enumerate(rankings)), 2):
        # rank position per channel, so correlation is over channels not over positions
        pos_i = np.empty(N_CHANNELS)
        pos_j = np.empty(N_CHANNELS)
        for pos, ch in enumerate(ri):
            pos_i[ch - 1] = pos
        for pos, ch in enumerate(rj):
            pos_j[ch - 1] = pos
        rho = spearmanr(pos_i, pos_j).statistic
        tau = kendalltau(pos_i, pos_j).statistic
        row = {"group": label, "a": i, "b": j, "spearman_rho": float(rho),
               "kendall_tau": float(tau)}
        for k in TOP_KS:
            row[f"jaccard_top{k}"] = jaccard(ri[:k], rj[:k])
        rows.append(row)
    return rows


def main():
    long_p = RANK / "cross_fitted_importance_long.csv"
    scores_p = RANK / "cross_fitted_scores.csv"
    if not long_p.exists() or not scores_p.exists():
        print(f"FATAL: {long_p.name} / {scores_p.name} missing — run scripts/25 first")
        return 2

    OUT.mkdir(parents=True, exist_ok=True)
    long = pd.read_csv(long_p)
    scores = pd.read_csv(scores_p)

    # ---- PRIMARY: agreement across inner folds (disjoint held-out subject groups) -------------
    inner_rows = []
    for pid, g in long.groupby("outer_participant"):
        mat = (g.pivot(index="inner_fold", columns="channel", values="importance_norm")
                .sort_index())
        rankings = [ranking_from_scores(mat.loc[f].to_numpy()) for f in mat.index]
        for r in pairwise_agreement(rankings, "inner"):
            r["outer_participant"] = int(pid)
            inner_rows.append(r)
    inner = pd.DataFrame(inner_rows)
    inner.to_csv(OUT / "inner_fold_agreement.csv", index=False)

    # ---- Reported only as an upper bound: agreement across outer folds -----------------------
    outer_rankings = []
    for pid, g in scores.groupby("outer_participant"):
        g = g.sort_values("channel")
        outer_rankings.append(ranking_from_scores(g["A_central"].to_numpy()))
    outer = pd.DataFrame(pairwise_agreement(outer_rankings, "outer"))
    outer["caveat"] = "training sets overlap ~98%; NOT a cross-subject stability estimate"
    outer.to_csv(OUT / "outer_fold_agreement.csv", index=False)

    # ---- STRONGEST TEST: agreement between individual people ---------------------------------
    # Fold-level agreement compares groups of 8-9 held-out subjects; group averaging smooths
    # individual variation, so it answers "do groups agree?" rather than "do people agree?".
    # A fixed sparse electrode layout for an unseen individual needs the second answer.
    subj_p = RANK / "per_subject_attribution.csv"
    per_subj = pd.DataFrame()
    if subj_p.exists():
        ps = pd.read_csv(subj_p)
        # One vector per attributed subject; a subject is attributed once per outer fold it
        # appears in, so average over outer folds to get one profile per person.
        prof = (ps.groupby(["attributed_subject", "channel"]).importance_norm.mean()
                  .unstack("channel").sort_index())
        rankings = [ranking_from_scores(prof.loc[s].to_numpy()) for s in prof.index]
        per_subj = pd.DataFrame(pairwise_agreement(rankings, "per_subject"))
        per_subj["subject_a"] = [prof.index[i] for i in per_subj.a]
        per_subj["subject_b"] = [prof.index[i] for i in per_subj.b]
        per_subj.to_csv(OUT / "per_subject_agreement.csv", index=False)

        prof.to_csv(OUT / "per_subject_profiles.csv")
        disp = pd.DataFrame({
            "channel": prof.columns,
            "between_subject_sd": prof.std(axis=0).to_numpy(),
            "between_subject_mean": prof.mean(axis=0).to_numpy(),
        })
        disp["cv"] = disp.between_subject_sd / disp.between_subject_mean
        disp.to_csv(OUT / "per_subject_dispersion.csv", index=False)
    else:
        print(f"NOTE: {subj_p.name} not found — per-subject agreement skipped. "
              f"Re-run scripts/25 to produce it.", flush=True)

    # ---- Channel-level selection frequency and rank dispersion --------------------------------
    freq_rows = []
    all_inner = []
    for pid, g in long.groupby("outer_participant"):
        mat = g.pivot(index="inner_fold", columns="channel", values="importance_norm").sort_index()
        for f in mat.index:
            all_inner.append(ranking_from_scores(mat.loc[f].to_numpy()))
    positions = np.zeros((len(all_inner), N_CHANNELS))
    for i, r in enumerate(all_inner):
        for pos, ch in enumerate(r):
            positions[i, ch - 1] = pos + 1
    for ch in range(1, N_CHANNELS + 1):
        p = positions[:, ch - 1]
        row = {"channel": ch, "median_rank": float(np.median(p)),
               "rank_mad": float(np.median(np.abs(p - np.median(p)))),
               "rank_min": float(p.min()), "rank_max": float(p.max())}
        for k in TOP_KS:
            row[f"selected_top{k}_frac"] = float(np.mean(p <= k))
        freq_rows.append(row)
    freq = pd.DataFrame(freq_rows).sort_values("median_rank")
    freq.to_csv(OUT / "channel_selection_frequency.csv", index=False)

    # ---- Summary -----------------------------------------------------------------------------
    def describe(df, label):
        d = {"group": label, "n_pairs": len(df)}
        for col in ["spearman_rho", "kendall_tau"] + [f"jaccard_top{k}" for k in TOP_KS]:
            d[f"{col}_mean"] = float(df[col].mean())
            d[f"{col}_sd"] = float(df[col].std())
        return d

    parts = []
    if not per_subj.empty:
        parts.append(describe(per_subj, "per_subject_STRONGEST"))
    parts.append(describe(inner, "inner_folds_group_level"))
    parts.append(describe(outer, "outer_folds_UPPER_BOUND"))
    summary = pd.DataFrame(parts)
    summary.to_csv(OUT / "stability_summary.csv", index=False)

    print("\n=== cross-subject attribution stability ===", flush=True)
    print(summary.to_string(index=False), flush=True)
    print("\nchannel rank dispersion (inner folds):", flush=True)
    print(freq.to_string(index=False), flush=True)
    print("\nNOTE: the inner-fold row is the cross-subject stability estimate. The outer-fold row "
          "is inflated by ~98% training-set overlap and must not be quoted as stability.",
          flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
