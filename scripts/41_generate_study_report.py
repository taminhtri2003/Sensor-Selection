"""Generate the evidence-backed final study report from completed result files.

The report is deliberately data-driven: it refuses missing inputs and reads every reported metric
from an artifact rather than carrying manuscript constants.  It is a research handoff report, not
a publication layout; the strict publication gate remains scripts/16_verify_results.py.
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "reports" / "final_study_report.md"


def require(relative):
    path = ROOT / relative
    if not path.exists():
        raise SystemExit(f"FATAL: missing required report input {relative}")
    try:
        df = pd.read_csv(path)
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(f"FATAL: could not read {relative}: {exc}") from exc
    if df.empty:
        raise SystemExit(f"FATAL: empty report input {relative}")
    return df


def fmt(value, digits=3):
    if pd.isna(value):
        return "—"
    if isinstance(value, (bool, np.bool_)):
        return "yes" if value else "no"
    if isinstance(value, (int, np.integer)):
        return str(value)
    if isinstance(value, (int, float)):
        return f"{float(value):.{digits}f}"
    return str(value)


def markdown_table(frame, columns, headers=None):
    missing = set(columns) - set(frame.columns)
    if missing:
        raise ValueError(f"report columns missing: {sorted(missing)}")
    headers = headers or columns
    lines = ["| " + " | ".join(headers) + " |",
             "| " + " | ".join("---" for _ in columns) + " |"]
    for _, row in frame.iterrows():
        cells=[]
        for c in columns:
            value=row[c]
            if c in {'k','channels_k','n','n_participants','n_subjects','n_pairs','kstar_unadjusted','kstar_holm','n_kept'} and not pd.isna(value):
                cells.append(str(int(value)))
            else:
                cells.append(fmt(value))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def main():
    master = require("artifacts/statistics/master_statistics.csv")
    ni = require("artifacts/statistics/non_inferiority_by_k.csv")
    comparisons = require("artifacts/statistics/model_comparisons.csv")
    sparse = require("artifacts/metrics/sparse_curve_subject_metrics.csv")
    selection = require("artifacts/selection_baselines/selection_baseline_summary.csv")
    stability = require("artifacts/stability/stability_summary.csv")
    cross = require("artifacts/cross_session/cross_session_summary.csv")
    faith = require("artifacts/faithfulness/faithfulness_summary.csv")
    db5 = require("artifacts/db5/db5_summary.csv")
    bipolar = require("artifacts/bipolar/bipolar_summary.csv")
    extension = require("artifacts/participant_attribution/report_summary.csv")
    penalty_gate = require("artifacts/participant_attribution/penalty_gate.csv")
    extension_pairs = require("artifacts/participant_attribution/paired_comparisons.csv")
    literature_path = ROOT / "docs" / "literature" / "literature_matrix.csv"
    literature_count = len(pd.read_csv(literature_path)) if literature_path.exists() else 0
    budget_path = ROOT / "artifacts" / "selection_baselines" / "compute_budget.json"
    budget = json.loads(budget_path.read_text(encoding="utf-8"))

    full = master[master.quantity == "full_channel_macro_f1"].copy()
    curve = (sparse
             .groupby(["lambda", "channels_k"], as_index=False)
             .agg(n_participants=("participant_id", "nunique"),
                  mean_macro_f1=("macro_f1", "mean"), sd_macro_f1=("macro_f1", "std")))
    model_name = str(sparse.model.iloc[0])
    ni_primary = ni[(ni.model == model_name) & np.isclose(ni["margin"], 0.02)].copy()
    kstars = master[(master.quantity == "k_star") & np.isclose(master["margin"], 0.02)]

    lines = [
        "# Final study report — explainability-guided sparse sEMG selection",
        "",
        "This report was generated from the completed result graph on the run date.  It is intended "
        "as the handoff record for the study; numeric claims are not copied from the superseded "
        "manuscript.",
        "",
        "## Scope and validity rules",
        "",
        "- GRABMyo primary endpoint: participant-level Macro-F1 over 16 active gestures, 43 LOSO "
        "participants; Rest is excluded.",
        "- Current fitting, scaling and ranking exclude each outer participant. Historical "
        "training-budget calibration used test-fold outcomes and remains disclosed.",
        "- Confidence intervals and non-inferiority decisions use participant-level bootstrap "
        "resampling (N=43), never windows.",
        "- The full-channel reference and sparse-curve reference are kept separate because the "
        "sparse phases use the documented 200,000-window training budget.",
        "",
        "## Full-channel LOSO baseline",
        "",
        markdown_table(full.sort_values("model"),
                       ["model", "n_participants", "estimate", "lcb95", "ucb95", "sd"],
                       ["model", "N", "Macro-F1", "95% LCB", "95% UCB", "SD"]),
        "",
        "Paired model comparisons (Holm-adjusted within the prespecified family):",
        "",
        markdown_table(comparisons,
                       ["model_a", "model_b", "n_participants", "mean_diff", "lcb95", "ucb95",
                        "p_holm", "effect_size_rank_biserial"],
                       ["A", "B", "N", "mean A−B", "LCB", "UCB", "Holm p", "rank-biserial"]),
        "",
        "XGBoost was designated as the computational primary for the sparse "
        "phases, not a claim that it is significantly better than every baseline.",
        "",
        "## Cross-fitted sparse curve",
        "",
        "All four frozen λ candidates are shown; no λ is selected using an outer-test score.",
        "",
        markdown_table(curve.sort_values(["lambda", "channels_k"]),
                       ["lambda", "channels_k", "n_participants", "mean_macro_f1", "sd_macro_f1"],
                       ["λ", "k", "N", "mean Macro-F1", "SD"]),
        "",
        "Participant-level non-inferiority at the prespecified δ=0.02 margin:",
        "",
        markdown_table(ni_primary.sort_values(["lambda", "k", "margin"]),
                       ["lambda", "margin", "k", "n_participants", "mean_diff", "lcb_95",
                        "ucb_95", "is_non_inferior"],
                       ["λ", "δ", "k", "N", "Δ vs k=16", "95% LCB", "95% UCB",
                        "non-inferior"]),
        "",
        "Prespecified k* result:",
        "",
    ]
    if kstars.empty:
        lines.append("- No k* row was found for the primary λ and δ=0.02; inspect the statistics artifact.")
    else:
        for _, row in kstars.sort_values(["lambda", "margin"]).iterrows():
            lines.append(f"- {row.model}, λ={float(row['lambda']):g}, δ={float(row.margin):g}: "
                         f"{row.note}.")

    lines += [
        "",
        "## Participant-level attribution upgrade (post hoc)",
        "",
        "Each inner-held-out participant contributes one normalised electrode-attribution vector. "
        "The upgraded score uses the median minus lambda times MAD across these people, retaining "
        "outer-participant exclusion. This measures between-person heterogeneity more directly "
        "than pooling people into inner folds. The extension does not retrospectively replace H3.",
        "",
        markdown_table(extension,
                       ["lambda", "kstar_unadjusted", "kstar_holm", "delta_at_12", "lcb95", "ucb95", "p_holm"],
                       ["lambda", "k*", "k* Holm", "participant minus fold at k=12", "LCB", "UCB", "Holm p"]),
        "",
        f"Across all {len(extension_pairs)} paired aggregation comparisons, "
        f"{int(((extension_pairs.mean_diff > 0) & (extension_pairs.p_holm < .05)).sum())} "
        "favoured the upgrade and "
        f"{int(((extension_pairs.mean_diff < 0) & (extension_pairs.p_holm < .05)).sum())} "
        "favoured the original aggregation after family-wide Holm adjustment.",
        "",
        "The penalty gate compares every positive lambda with lambda zero within the upgraded "
        "aggregation. These are exploratory diagnostics with correction across the complete family:",
        "",
        markdown_table(penalty_gate,
                       ["lambda", "k", "n", "mean_diff", "lcb95", "ucb95", "p_holm",
                        "supports_penalty_benefit", "supports_penalty_harm"],
                       ["lambda", "k", "N", "penalty minus magnitude", "LCB", "UCB", "Holm p", "benefit", "harm"]),
        "",
        "All candidates are retained. A null or harmful comparison is not converted into a "
        "positive result by changing the gate or choosing a candidate from outer-test scores.",
        "",
        "## Selection baselines",
        "",
        f"The comparison used random-subset counts {budget['actually_run'].get('n_subsets_by_k', budget['actually_run'].get('n_subsets_per_k'))}. "
        f"The frozen plan requested at least 100 per k and 500 at k*; the run was "
        f"{'capped' if budget.get('capped') else 'not capped'} and this status must remain visible "
        "in any manuscript claim.",
        "",
        markdown_table(selection.sort_values(["channels_k", "mean_macro_f1"], ascending=[True, False]),
                       ["method", "channels_k", "n", "mean_macro_f1", "sd"],
                       ["method", "k", "N", "mean Macro-F1", "SD"]),
        "",
        "## Stability, sessions, and faithfulness",
        "",
        "Stability summary:",
        "",
        markdown_table(stability,
                       ["group", "n_pairs", "spearman_rho_mean", "kendall_tau_mean",
                        "jaccard_top4_mean", "jaccard_top6_mean", "jaccard_top8_mean"],
                       ["group", "pairs", "Spearman ρ", "Kendall τ", "Jaccard@4", "Jaccard@6",
                        "Jaccard@8"]),
        "",
        "Cross-session summary:",
        "",
        markdown_table(cross,
                       ["design", "train_sessions", "test_session", "matched_session",
                        "n_participants", "mean_macro_f1", "sd_macro_f1"],
                       ["design", "train", "test", "matched", "N", "mean Macro-F1", "SD"]),
        "",
        "Faithfulness deletion summary:",
        "",
        markdown_table(faith,
                       ["arm", "n_kept", "n_participants", "mean_macro_f1", "sd"],
                       ["arm", "kept", "N", "mean Macro-F1", "SD"]),
        "",
        "## External and bipolar sensitivity analyses",
        "",
        "NinaPro DB5 is a methodological replication only; its hardware, sampling rate, movement "
        "set, and feature units are not interchangeable with GRABMyo.",
        "",
        markdown_table(db5.sort_values("channels_k"),
                       ["channels_k", "n_subjects", "mean_macro_f1", "sd"],
                       ["DB5 k", "N", "mean Macro-F1", "SD"]),
        "",
        "Bipolar sensitivity (F_j − F_{j+8}):",
        "",
        markdown_table(bipolar.sort_values(["lambda", "channels_k"]),
                       ["lambda", "channels_k", "n_participants", "mean_macro_f1", "sd_macro_f1"],
        ["λ", "bipolar k", "N", "mean Macro-F1", "SD"]),
        "",
        "## Literature status",
        "",
        f"The current literature matrix contains {literature_count} screened entries. This "
        "matrix is a scoping resource with flagged registry mismatches, not a systematic review.",
        "",
        "## Reproducibility and limitations",
        "",
        "- The strict result gate is `scripts/16_verify_results.py`; it must pass before numeric "
        "manuscript macros are generated.",
        "- The 1D CNN/integrated-gradients phase is conditional in the frozen execution plan and is "
        "not represented as evidence unless its own artifacts exist.",
        "- Window-length sensitivity and the rest-inclusive task were not run; neither contributes "
        "evidence to the manuscript.",
        "- Ethics remains unresolved at the author's request. Funding, contributions, conflicts "
        "and the permanent archive identifier still require author confirmation.",
        "- Random-baseline capping, if present above, is a declared deviation rather than silently "
        "reported as full frozen-plan coverage.",
        "- mRMR is not included in the executed baseline set because the current pipeline does not "
        "contain a validated implementation; it is therefore reported as omitted, not as a null "
        "result.",
        "- Source artifacts: `artifacts/statistics/`, `artifacts/metrics/`, `artifacts/rankings/`, "
        "`artifacts/selection_baselines/`, `artifacts/stability/`, `artifacts/cross_session/`, "
        "`artifacts/faithfulness/`, `artifacts/db5/`, `artifacts/bipolar/`, and "
        "`artifacts/participant_attribution/`.",
        "",
    ]

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
