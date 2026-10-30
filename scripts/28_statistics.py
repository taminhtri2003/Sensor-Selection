"""Confirmatory statistics: implements configs/statistics/frozen_analysis_plan.yaml.

Produces the numbers the manuscript is allowed to cite. Every rule here (statistical unit,
margin, bootstrap, multiplicity, k* definition) comes from the frozen plan and is read from it at
runtime rather than restated, so the code cannot silently drift from the pre-registered analysis.

Design commitments that exist to prevent the previous study's failure mode:
  - k* is None when no channel count meets the margin. A null result is reported as a null result.
  - Paired comparisons are aligned by participant id and raise on mismatch.
  - The margin is read from the plan; there is no code path that adjusts it after seeing results.
  - If an input file is missing, this script exits non-zero. It never emits a placeholder value.

Outputs:
  artifacts/statistics/master_statistics.csv    one row per primary quantity
  artifacts/statistics/non_inferiority_by_k.csv
  artifacts/statistics/model_comparisons.csv
  artifacts/statistics/analysis_provenance.json
"""

import hashlib
import json
import sys
from itertools import combinations
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
from src.semg_sparse.xai.validation import finite_values, require_grid

PLAN = ROOT / "configs" / "statistics" / "frozen_analysis_plan.yaml"
METRICS = ROOT / "artifacts" / "metrics"
OUT = ROOT / "artifacts" / "statistics"
METRIC = "macro_f1"
EXPECTED_PARTICIPANTS = 43   # GRABMyo cohort; set to 0 to disable the check
FULL_MODELS = ('M_XGBoost', 'M_SVM', 'M_RandomForest')
LAMBDAS = (0., .25, .5, 1.)


def full_input_paths(directory):
    """Only the two primary files may enter the confirmatory model family."""
    return [directory / name for name in ('loso_full_channel_subject_metrics_svmrf.csv',
                                          'loso_full_channel_subject_metrics_xgb.csv')
            if (directory / name).exists()]


def validate_inputs(full, curve, allow_partial=False):
    """Reject invalid rows always; incomplete grids are provisional only when requested."""
    participants = list(range(1, EXPECTED_PARTICIPANTS + 1))
    problems = []
    for label, frame, keys, levels in (
        ('full baselines', full, ['participant_id', 'model', 'channels_k'],
         [participants, FULL_MODELS, [16]]),
        ('primary sparse curve', curve, ['participant_id', 'model', 'lambda', 'channels_k'],
         [participants, ['M_XGB'], LAMBDAS, range(1, 17)]),
    ):
        if frame is None or frame.empty:
            problems.append(f'{label}: missing input')
            continue
        if not set(keys + [METRIC]).issubset(frame.columns):
            raise ValueError(f'{label}: missing required columns')
        if frame.duplicated(keys).any():
            raise ValueError(f'{label}: duplicate participant result keys')
        finite_values(frame, [METRIC], label, bounded=True)
        for column, allowed in zip(keys, levels):
            if not frame[column].isin(allowed).all():
                raise ValueError(f'{label}: unexpected {column}')
        try:
            require_grid(frame, keys, levels, label)
        except ValueError as exc:
            problems.append(str(exc))
    if problems and not allow_partial:
        raise ValueError('; '.join(problems))
    return problems


def load_plan():
    """Read the frozen plan. Parsed with a minimal reader to avoid a yaml dependency; only the
    handful of scalars we need are extracted, and each is echoed into the provenance file."""
    text = PLAN.read_text(encoding="utf-8")
    plan = {
        "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "primary_margin": None, "sensitivity_margins": [], "n_resamples": None,
        "ci_level": None, "multiplicity": None,
    }
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("primary_margin:"):
            plan["primary_margin"] = float(s.split(":", 1)[1])
        elif s.startswith("sensitivity_margins:"):
            plan["sensitivity_margins"] = [
                float(x) for x in s.split("[", 1)[1].rstrip("]").split(",")
            ]
        elif s.startswith("n_resamples:"):
            plan["n_resamples"] = int(s.split(":", 1)[1])
        elif s.startswith("ci_level:"):
            plan["ci_level"] = float(s.split(":", 1)[1])
        elif s.startswith("method: Holm"):
            plan["multiplicity"] = "Holm"
    missing = [k for k, v in plan.items() if v is None]
    if missing:
        raise SystemExit(f"FATAL: could not read {missing} from the frozen plan {PLAN}")
    return plan


def holm(pvals):
    """Holm-Bonferroni adjusted p-values, order preserved."""
    p = np.asarray(pvals, dtype=float)
    n = len(p)
    order = np.argsort(p)
    adj = np.empty(n)
    running = 0.0
    for rank, idx in enumerate(order):
        val = (n - rank) * p[idx]
        running = max(running, val)
        adj[idx] = min(1.0, running)
    return adj


def rank_biserial(diffs):
    """Matched-pairs rank-biserial correlation: effect size for the Wilcoxon signed-rank test."""
    d = np.asarray(diffs, dtype=float)
    d = d[d != 0]
    if len(d) == 0:
        return 0.0
    ranks = pd.Series(np.abs(d)).rank().to_numpy()
    total = ranks.sum()
    return float((ranks[d > 0].sum() - ranks[d < 0].sum()) / total)


def paired_frame(df, model, k):
    sub = df[(df.model == model) & (df.channels_k == k)]
    return sub.set_index("participant_id")[METRIC].sort_index()


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--allow-partial', action='store_true',
                    help='compute provisional values from an unfinished run; outputs are suffixed _PARTIAL and must never be quoted in the manuscript')
    args = ap.parse_args()
    allow_partial = args.allow_partial
    suffix = '_PARTIAL' if allow_partial else ''
    plan = load_plan()
    n_boot = plan["n_resamples"]
    margin = plan["primary_margin"]

    full_files = full_input_paths(METRICS)
    if not full_files:
        print("FATAL: no full-channel metrics found. Run scripts/24 first.")
        return 2
    full = pd.concat([pd.read_csv(f) for f in full_files], ignore_index=True)
    primary_curve = METRICS / 'sparse_curve_subject_metrics.csv'
    curve_files = [primary_curve] if primary_curve.exists() else []
    curve = pd.read_csv(primary_curve) if curve_files else None
    try:
        input_problems = validate_inputs(full, curve, allow_partial=allow_partial)
    except ValueError as exc:
        print(f'INVALID OR INCOMPLETE INPUT — refusing confirmatory statistics: {exc}')
        return 3
    n_participants = full.participant_id.nunique()
    print(f"full-channel: {len(full)} rows, {n_participants} participants, "
          f"models={sorted(full.model.unique())}", flush=True)

    # --- Completeness gate --------------------------------------------------------------------
    # Refuse to emit confirmatory statistics from an incomplete run. Without this, a half-finished
    # LOSO sweep yields a confident-looking mean and CI over whichever participants happened to
    # finish first, and models get compared on different cohorts. That is exactly how the
    # superseded study came to report 43 participants while having computed 15.
    per_model = full[full.channels_k == 16].groupby("model").participant_id.nunique()
    sets = {m: set(g.participant_id) for m, g in full[full.channels_k == 16].groupby("model")}
    problems = list(input_problems)
    if EXPECTED_PARTICIPANTS and n_participants != EXPECTED_PARTICIPANTS:
        problems.append(f"cohort has {n_participants} participants, expected {EXPECTED_PARTICIPANTS}")
    if per_model.nunique() > 1:
        problems.append(f"models cover different participant counts: {per_model.to_dict()}")
    common = set.intersection(*sets.values()) if sets else set()
    for m, s in sets.items():
        if s != common:
            problems.append(f"{m} covers {len(s)} participants; {len(s - common)} not shared")
    if problems:
        print("\nINCOMPLETE INPUT — refusing to write confirmatory statistics:", flush=True)
        for p in problems:
            print(f"  - {p}", flush=True)
        if not allow_partial:
            print("\nRe-run once the LOSO sweep has finished, or pass --allow-partial to compute "
                  "provisional values (which are written to a *_PARTIAL suffix and must never be "
                  "quoted in the manuscript).", flush=True)
            return 3
        print("\n--allow-partial set: writing PROVISIONAL values only.", flush=True)

    OUT.mkdir(parents=True, exist_ok=True)
    master = []

    # --- Per-model full-channel performance with participant-level bootstrap CIs ---------------
    for model in sorted(full.model.unique()):
        s = paired_frame(full, model, 16)
        mean, lcb, ucb = bootstrap_participant_metrics(s.to_numpy(), n_resamples=n_boot)
        master.append({
            "quantity": "full_channel_macro_f1", "model": model, "k": 16,
            "n_participants": int(len(s)), "estimate": mean, "lcb95": lcb, "ucb95": ucb,
            "sd": float(s.std()), "min": float(s.min()), "max": float(s.max()),
        })
        print(f"  {model}: {mean:.4f} (95% CI {lcb:.4f}-{ucb:.4f}) n={len(s)}", flush=True)

    # --- Paired model comparisons, Holm-corrected within the family ----------------------------
    comparisons, pvals = [], []
    for a, b in combinations(sorted(full.model.unique()), 2):
        sa, sb = paired_frame(full, a, 16), paired_frame(full, b, 16)
        common = sa.index.intersection(sb.index)
        if len(common) < 3:
            continue
        d = (sa.loc[common] - sb.loc[common]).to_numpy()
        stat, p = wilcoxon(d)
        mean, lcb, ucb = bootstrap_participant_metrics(d, n_resamples=n_boot)
        comparisons.append({
            "model_a": a, "model_b": b, "n_participants": int(len(common)),
            "mean_diff": mean, "lcb95": lcb, "ucb95": ucb,
            "wilcoxon_stat": float(stat), "p_raw": float(p),
            "effect_size_rank_biserial": rank_biserial(d),
        })
        pvals.append(p)
    if comparisons:
        for row, adj in zip(comparisons, holm(pvals)):
            row["p_holm"] = float(adj)
            row["significant_holm_005"] = bool(adj < 0.05)
        pd.DataFrame(comparisons).to_csv(OUT / f"model_comparisons{suffix}.csv", index=False)
        print(f"  wrote {len(comparisons)} paired model comparisons (Holm-corrected)", flush=True)

    # --- Non-inferiority over the sparse curve, if it exists -----------------------------------
    # The confirmatory run is the untagged primary file.  Tagged files are
    # reserved for benchmarks/partial reruns and must not silently enter the
    # participant-level paired analysis.
    ni_rows, k_star_by_margin = [], {}
    if curve_files:
        for model in sorted(curve.model.unique()):
            for lam in sorted(curve["lambda"].unique()):
                sel = curve[(curve.model == model) & (np.isclose(curve["lambda"], lam))]
                ref = paired_frame(sel, model, 16)
                if ref.empty:
                    print(f"  WARNING: no k=16 reference for {model} lambda={lam}; skipped")
                    continue
                for m in sorted(set([margin] + plan["sensitivity_margins"])):
                    found = None
                    for k in sorted(sel.channels_k.unique()):
                        sk = paired_frame(sel, model, k)
                        common = sk.index.intersection(ref.index)
                        if set(sk.index) != set(ref.index) or (not allow_partial and len(common) != EXPECTED_PARTICIPANTS):
                            raise ValueError(f"incomplete paired cohort at lambda={lam}, k={k}")
                        res = evaluate_non_inferiority(
                            sk.loc[common].to_numpy(), ref.loc[common].to_numpy(),
                            margin_delta=m, n_resamples=n_boot,
                            participants_k=common.to_numpy(),
                            participants_full=common.to_numpy(),
                        )
                        res.update(model=model, **{"lambda": lam}, k=int(k), margin=m)
                        ni_rows.append(res)
                        if res["is_non_inferior"] and found is None and k < 16:
                            found = int(k)
                    k_star_by_margin[(model, lam, m)] = found
        if ni_rows:
            pd.DataFrame(ni_rows).to_csv(OUT / f"non_inferiority_by_k{suffix}.csv", index=False)
        for (model, lam, m), ks in k_star_by_margin.items():
            master.append({
                "quantity": "k_star", "model": model, "lambda": lam, "margin": m,
                "estimate": ks if ks is not None else np.nan,
                "k_star_found": ks is not None,
                # Explicitly distinguishable from "k*=16": None means NO channel count met the
                # margin, which is a finding, not a fallback.
                "note": ("no k met the margin" if ks is None else f"smallest non-inferior k={ks}"),
            })
            print(f"  k* [{model} lambda={lam} margin={m}]: "
                  f"{ks if ks is not None else 'NONE MET THE MARGIN'}", flush=True)
    else:
        print("  (sparse curve not yet computed; non-inferiority skipped)", flush=True)

    pd.DataFrame(master).to_csv(OUT / f"master_statistics{suffix}.csv", index=False)
    (OUT / f"analysis_provenance{suffix}.json").write_text(json.dumps({
        "frozen_plan": str(PLAN.relative_to(ROOT)).replace("\\", "/"),
        "frozen_plan_sha256": plan["sha256"],
        "primary_margin": margin, "sensitivity_margins": plan["sensitivity_margins"],
        "n_bootstrap_resamples": n_boot, "ci_level": plan["ci_level"],
        "multiplicity": plan["multiplicity"], "metric": METRIC,
        "n_participants": int(n_participants),
        "inputs": [str(f.relative_to(ROOT)).replace("\\", "/")
                   for f in full_files + curve_files],
    }, indent=2))

    print(f"\nwrote {OUT/'master_statistics.csv'} ({len(master)} quantities)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
