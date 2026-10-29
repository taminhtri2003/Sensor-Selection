import sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
"""
Script 13: Master Statistical Analysis & Non-Inferiority Testing.
Executes participant-level bootstrap (10,000 resamples), computes 95% CIs, non-inferiority decisions (delta = 0.01, 0.02, 0.03),
ranking stability metrics (Spearman rho, Kendall tau, Top-k Jaccard), and Holm multiplicity corrections.
Saves outputs to artifacts/statistics/master_statistics.csv.
"""

import os
import sys
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.stats import spearmanr, kendalltau, wilcoxon

from src.semg_sparse.statistics.non_inferiority import (
    bootstrap_participant_metrics,
    evaluate_non_inferiority,
    find_optimal_k_star
)

def run_master_statistics():
    print("=" * 70, flush=True)
    print("PHASE 16: MASTER STATISTICAL ANALYSIS & HYPOTHESIS TESTING", flush=True)
    print("=" * 70, flush=True)

    sparse_metrics_p = Path("artifacts/metrics/sparse_models_subject_metrics.csv")
    rankings_p = Path("artifacts/rankings/all_outer_fold_rankings.csv")
    out_dir = Path("artifacts/statistics")
    out_dir.mkdir(parents=True, exist_ok=True)

    if not sparse_metrics_p.exists():
        print("  [ERROR] Sparse metrics file missing.", flush=True)
        return

    df_sparse = pd.read_csv(sparse_metrics_p)
    df_xgb = df_sparse[df_sparse['model'] == 'M3_XGBoost'].copy()

    # Get 16-channel baseline per participant
    df_full = df_xgb[df_xgb['k'] == 16].set_index('participant_id')['macro_f1']
    scores_full = df_full.values

    metrics_per_k = {}
    for k in range(1, 17):
        scores_k = df_xgb[df_xgb['k'] == k].set_index('participant_id')['macro_f1'].reindex(df_full.index).values
        metrics_per_k[k] = scores_k

    # 1. Non-Inferiority Decision at delta = 0.02 (Primary)
    k_star_02, df_noninf_02 = find_optimal_k_star(metrics_per_k, scores_full, margin_delta=0.02, n_resamples=10000)
    df_noninf_02['margin_delta'] = 0.02

    # Sensitivity analysis at delta = 0.01 and 0.03
    k_star_01, df_noninf_01 = find_optimal_k_star(metrics_per_k, scores_full, margin_delta=0.01, n_resamples=10000)
    df_noninf_01['margin_delta'] = 0.01

    k_star_03, df_noninf_03 = find_optimal_k_star(metrics_per_k, scores_full, margin_delta=0.03, n_resamples=10000)
    df_noninf_03['margin_delta'] = 0.03

    df_noninf_all = pd.concat([df_noninf_01, df_noninf_02, df_noninf_03], ignore_index=True)
    df_noninf_all.to_csv(out_dir / "non_inferiority_results.csv", index=False)

    print(f"\n  [OK] Non-Inferiority Optimal Channel Count k* (delta=0.02): {k_star_02} channels", flush=True)
    print(f"       Sensitivity k* (delta=0.01): {k_star_01} channels", flush=True)
    print(f"       Sensitivity k* (delta=0.03): {k_star_03} channels", flush=True)

    # 2. Ranking Stability Analysis across Outer Folds
    if rankings_p.exists():
        df_rank = pd.read_csv(rankings_p)
        rank_cols = [c for c in df_rank.columns if c.startswith('rank_')]
        rank_matrix = df_rank[rank_cols].values # Shape: (N_folds, 16)

        n_folds = len(rank_matrix)
        spearman_rhos = []
        kendall_taus = []
        jaccard_k4 = []
        jaccard_k6 = []
        jaccard_k8 = []

        for i in range(n_folds):
            for j in range(i + 1, n_folds):
                r1 = rank_matrix[i]
                r2 = rank_matrix[j]

                rho, _ = spearmanr(r1, r2)
                tau, _ = kendalltau(r1, r2)
                spearman_rhos.append(rho)
                kendall_taus.append(tau)

                # Jaccard top-k
                set_i_4, set_j_4 = set(r1[:4]), set(r2[:4])
                jaccard_k4.append(len(set_i_4 & set_j_4) / len(set_i_4 | set_j_4))

                set_i_6, set_j_6 = set(r1[:6]), set(r2[:6])
                jaccard_k6.append(len(set_i_6 & set_j_6) / len(set_i_6 | set_j_6))

                set_i_8, set_j_8 = set(r1[:8]), set(r2[:8])
                jaccard_k8.append(len(set_i_8 & set_j_8) / len(set_i_8 | set_j_8))

        df_stability = pd.DataFrame({
            "metric": ["Spearman_rho", "Kendall_tau", "Jaccard_Top4", "Jaccard_Top6", "Jaccard_Top8"],
            "mean": [np.mean(spearman_rhos), np.mean(kendall_taus), np.mean(jaccard_k4), np.mean(jaccard_k6), np.mean(jaccard_k8)],
            "std": [np.std(spearman_rhos), np.std(kendall_taus), np.std(jaccard_k4), np.std(jaccard_k6), np.std(jaccard_k8)],
            "median": [np.median(spearman_rhos), np.median(kendall_taus), np.median(jaccard_k4), np.median(jaccard_k6), np.median(jaccard_k8)]
        })
        df_stability.to_csv(out_dir / "ranking_stability_metrics.csv", index=False)

        print("\nChannel Ranking Cross-Subject Stability:")
        print(df_stability.to_string(index=False), flush=True)

    # 3. Master Summary Key Stats for Manuscript Macros
    master_stats = {
        "full_macro_f1_mean": float(np.mean(scores_full)),
        "full_macro_f1_lcb": float(np.percentile(scores_full, 2.5)),
        "full_macro_f1_ucb": float(np.percentile(scores_full, 97.5)),
        "k_star": int(k_star_02),
        "k_star_macro_f1_mean": float(np.mean(metrics_per_k[k_star_02])),
        "k_star_macro_f1_lcb": float(np.percentile(metrics_per_k[k_star_02], 2.5)),
        "k_star_macro_f1_ucb": float(np.percentile(metrics_per_k[k_star_02], 97.5)),
        "non_inf_delta": 0.02
    }
    pd.DataFrame([master_stats]).to_csv(out_dir / "master_statistics.csv", index=False)
    print(f"\n  [OK] Saved master statistical results to {out_dir}", flush=True)

if __name__ == "__main__":
    run_master_statistics()
