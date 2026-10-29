"""Strict final result verification for the rebuilt study.

This is the repository's publication gate.  It deliberately refuses to invent defaults: missing
or incomplete artefacts are errors, not invitations to generate placeholder manuscript numbers.
The current macro implementation lives in ``scripts/40_generate_macros.py``; this script invokes
it only after validating the complete result graph required by the study.
"""

from __future__ import annotations

import json
import hashlib
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src.semg_sparse.xai.validation import (validate_attribution_tables,
    validate_sparse_subsets, require_grid, finite_values)
EXPECTED_GRABMYO = 43
EXPECTED_DB5 = 10


def fail(message: str) -> None:
    raise RuntimeError(message)


def require_file(relative: str) -> Path:
    path = ROOT / relative
    if not path.exists():
        fail(f"missing required result file: {relative}")
    return path


def read_csv(relative: str) -> pd.DataFrame:
    path = require_file(relative)
    try:
        df = pd.read_csv(path)
    except Exception as exc:  # noqa: BLE001
        fail(f"could not read {relative}: {exc}")
    if df.empty:
        fail(f"required result file is empty: {relative}")
    numeric = df.select_dtypes(include=[np.number])
    # Some result schemas intentionally use NaN for non-applicable summary fields (for example
    # fit_seconds on the aggregated RANDOM row).  Reject infinities, but leave schema-level
    # missingness to the phase-specific completeness checks below.
    if np.isinf(numeric.to_numpy(dtype=float)).any():
        fail(f"infinite numeric value in {relative}")
    return df


def require_participant_coverage(df: pd.DataFrame, column: str, expected: int, label: str) -> None:
    if column not in df:
        fail(f"{label} has no {column} column")
    actual = int(df[column].nunique())
    if actual != expected:
        fail(f"{label} covers {actual} {column} values; expected {expected}")


def verify_rankings() -> None:
    scores = read_csv("artifacts/rankings/cross_fitted_scores.csv")
    ranks = read_csv("artifacts/rankings/cross_fitted_rankings.csv")
    long = read_csv("artifacts/rankings/cross_fitted_importance_long.csv")
    per_subject = read_csv("artifacts/rankings/per_subject_attribution.csv")

    require_participant_coverage(scores, "outer_participant", EXPECTED_GRABMYO,
                                  "cross-fitted scores")
    require_participant_coverage(ranks, "outer_participant", EXPECTED_GRABMYO,
                                 "cross-fitted rankings")
    require_participant_coverage(long, "outer_participant", EXPECTED_GRABMYO,
                                 "cross-fitted importance")
    if set(scores.outer_participant) != set(ranks.outer_participant):
        fail("ranking and score participant sets differ")
    if len(scores) != EXPECTED_GRABMYO * 16:
        fail(f"cross-fitted scores have {len(scores)} rows; expected {EXPECTED_GRABMYO * 16}")
    if len(ranks) != EXPECTED_GRABMYO * 4:
        fail(f"cross-fitted rankings have {len(ranks)} rows; expected {EXPECTED_GRABMYO * 4}")
    for (pid, lam), g in ranks.groupby(["outer_participant", "lambda"]):
        channels = [int(x) for x in str(g.iloc[0].ranking).split(";")]
        if sorted(channels) != list(range(1, 17)):
            fail(f"ranking for participant {pid}, lambda {lam} is not a permutation of 1..16")
    require_participant_coverage(per_subject, "attributed_subject", EXPECTED_GRABMYO,
                                 "per-subject attribution")
    validate_attribution_tables(long, per_subject, scores, ranks, range(1, 44))


def verify_metrics() -> None:
    full = read_csv("artifacts/metrics/loso_full_channel_subject_metrics_svmrf.csv")
    xgb = read_csv("artifacts/metrics/loso_full_channel_subject_metrics_xgb.csv")
    for label, df in (("full-channel SVM/RF", full), ("full-channel XGBoost", xgb)):
        require_participant_coverage(df, "participant_id", EXPECTED_GRABMYO, label)
        if not (df["channels_k"] == 16).all():
            fail(f"{label} contains non-full-channel rows")

    sparse = read_csv("artifacts/metrics/sparse_curve_subject_metrics.csv")
    require_participant_coverage(sparse, "participant_id", EXPECTED_GRABMYO,
                                 "sparse sensor curve")
    if not set(sparse.channels_k).issuperset(set(range(1, 17))):
        fail("sparse sensor curve does not cover k=1..16")
    if set(np.round(sparse["lambda"].astype(float), 8)) != {0.0, 0.25, 0.5, 1.0}:
        fail("sparse sensor curve does not cover all four frozen lambda candidates")
    for (pid, lam), g in sparse.groupby(["participant_id", "lambda"]):
        if set(g.channels_k.astype(int)) != set(range(1, 17)):
            fail(f"sparse sensor curve incomplete for participant {pid}, lambda {lam}")
    validate_sparse_subsets(sparse, read_csv("artifacts/rankings/cross_fitted_rankings.csv"),
                            range(1, 44))
    for df, models in ((full, sorted(full.model.unique())), (xgb, sorted(xgb.model.unique()))):
        require_grid(df, ["participant_id", "model"], [range(1, 44), models], "full baseline")
        finite_values(df, ["macro_f1", "accuracy", "balanced_accuracy", "weighted_f1"],
                      "full baseline", bounded=True)


def verify_statistics() -> None:
    master = read_csv("artifacts/statistics/master_statistics.csv")
    ni = read_csv("artifacts/statistics/non_inferiority_by_k.csv")
    comparisons = read_csv("artifacts/statistics/model_comparisons.csv")
    provenance_path = require_file("artifacts/statistics/analysis_provenance.json")
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    if int(provenance.get("n_participants", -1)) != EXPECTED_GRABMYO:
        fail("statistics provenance does not record 43 participants")
    full = master[master.quantity == "full_channel_macro_f1"]
    if full.empty or not (full.n_participants == EXPECTED_GRABMYO).all():
        fail("master statistics lack complete full-channel participant results")
    if not set(ni.channels_k if "channels_k" in ni else ni.k).issuperset(set(range(1, 17))):
        fail("non-inferiority table does not cover k=1..16")
    if comparisons.empty:
        fail("model comparison table is empty")


def verify_extension(prefix="artifacts/participant_attribution/") -> None:
    """The upgraded method is reportable only with a complete, current result graph."""
    ranks = read_csv(prefix + "rankings.csv")
    curve = read_csv(prefix + "sparse_curve.csv")
    scores = read_csv(prefix + "scores.csv")
    validate_sparse_subsets(curve, ranks, range(1,44))
    original = read_csv("artifacts/metrics/sparse_curve_subject_metrics.csv")
    metrics = ["macro_f1", "accuracy", "balanced_accuracy", "weighted_f1"]
    if set(curve.evaluation_source) - {"original_p3", "new_p3_protocol_fit"}:
        fail("extension contains an unknown evaluation source")
    if not (curve.n_train_windows == 200000).all():
        fail("extension changed the fixed training budget")
    for _, row in curve[curve.evaluation_source == "original_p3"].iterrows():
        if not float(row.source_row).is_integer() or not 0 <= row.source_row < len(original):
            fail("extension reused fit has no valid source row")
        source = original.iloc[int(row.source_row)]
        if (int(source.participant_id) != int(row.participant_id)
                or set(str(source.channels).split(';')) != set(str(row.channels).split(';'))
                or not np.allclose(source[metrics].astype(float), row[metrics].astype(float), atol=1e-12, rtol=0)):
            fail("extension reused fit does not match its source participant, subset or metrics")
    expected_stamp = hashlib.sha256(require_file(
        "configs/statistics/participant_attribution_extension.json").read_bytes()).hexdigest()
    if not (curve.plan_sha256 == expected_stamp).all():
        fail("extension rows do not match the recorded protocol")
    require_grid(scores, ["outer_participant", "channel"], [range(1,44),range(1,17)], "person scores")
    people = read_csv("artifacts/rankings/per_subject_attribution.csv")
    for pid in range(1,44):
        mat = people[people.outer_participant == pid].pivot(
            index="attributed_subject", columns="channel", values="importance_norm").to_numpy()
        center = np.median(mat, axis=0)
        mad = np.median(abs(mat-center), axis=0)
        saved = scores[scores.outer_participant == pid].sort_values("channel")
        if not (np.allclose(saved.A_central,center) and np.allclose(saved.U_instability,mad)):
            fail("person-level score reconstruction failed")
        for _, row in ranks[ranks.outer_participant == pid].iterrows():
            expected = (np.lexsort((np.arange(16), -(center-float(row['lambda'])*mad)))+1).tolist()
            if [int(c) for c in row.ranking.split(';')] != expected:
                fail("person-level ranking reconstruction failed")
    comparisons = read_csv(prefix + "paired_comparisons.csv")
    require_grid(comparisons, ["lambda", "k"], [[0.,.25,.5,1.],range(1,16)], "extension comparisons")
    if not (comparisons.n == 43).all():
        fail("extension inference must use all 43 participants")
    finite_values(comparisons, ["mean_diff", "lcb95", "ucb95", "p_raw", "p_holm"], "extension comparisons")
    ni = read_csv(prefix + "non_inferiority.csv")
    require_grid(ni,["lambda","margin","k"], [[0.,.25,.5,1.],[.01,.02,.03],range(1,16)],"extension NI")
    penalty = read_csv(prefix + "penalty_gate.csv")
    require_grid(penalty,["lambda","k"],[[.25,.5,1.],[4,6,8,12]],"penalty diagnostic")
    if not (penalty.n == 43).all():
        fail("penalty diagnostic has an incomplete participant cohort")
    fingerprint = json.loads(require_file(prefix + "input_hashes.json").read_text())
    for relative, expected_hash in fingerprint.items():
        h = hashlib.sha256()
        with require_file(relative).open('rb') as f:
            for chunk in iter(lambda: f.read(1024*1024), b''):
                h.update(chunk)
        if h.hexdigest() != expected_hash:
            fail(f"extension input changed since fitting: {relative}")


def verify_phase_outputs() -> None:
    required = [
        "artifacts/selection_baselines/selection_baseline_metrics.csv",
        "artifacts/selection_baselines/random_subsets_raw.csv",
        "artifacts/selection_baselines/selection_baseline_summary.csv",
        "artifacts/selection_baselines/compute_budget.json",
        "artifacts/stability/inner_fold_agreement.csv",
        "artifacts/stability/stability_summary.csv",
        "artifacts/cross_session/cross_session_metrics.csv",
        "artifacts/cross_session/cross_session_summary.csv",
        "artifacts/faithfulness/deletion_curves.csv",
        "artifacts/faithfulness/faithfulness_summary.csv",
        "artifacts/db5/db5_full_channel_metrics.csv",
        "artifacts/db5/db5_rankings.csv",
        "artifacts/db5/db5_sparse_curve.csv",
        "artifacts/db5/db5_summary.csv",
        "artifacts/bipolar/bipolar_full_channel_metrics.csv",
        "artifacts/bipolar/bipolar_rankings.csv",
        "artifacts/bipolar/bipolar_scores.csv",
        "artifacts/bipolar/bipolar_sparse_curve.csv",
        "artifacts/bipolar/bipolar_summary.csv",
        "artifacts/bipolar/bipolar_provenance.json",
    ]
    for relative in required:
        require_file(relative)

    selection = read_csv("artifacts/selection_baselines/selection_baseline_metrics.csv")
    selection_raw = read_csv("artifacts/selection_baselines/random_subsets_raw.csv")
    require_participant_coverage(selection, "participant_id", EXPECTED_GRABMYO,
                                 "selection baseline metrics")
    selection_ks = set(selection.channels_k.astype(int))
    if not selection_ks.issuperset({4, 6, 8}):
        fail("selection baselines do not cover the frozen k={4,6,8} comparison set")
    fixed_methods = {"SRCFA", "SHAP_lam0", "PERM", "MI", "GEOM"}
    for method in fixed_methods:
        g = selection[selection.method == method]
        if len(g) != EXPECTED_GRABMYO * len(selection_ks):
            fail(f"selection baseline {method} is incomplete")
    require_participant_coverage(selection_raw, "participant_id", EXPECTED_GRABMYO,
                                 "random subset baseline")
    budget = json.loads(require_file(
        "artifacts/selection_baselines/compute_budget.json").read_text(encoding="utf-8"))
    if int(budget.get("actually_run", {}).get("n_subsets_per_k", 0)) <= 0:
        fail("selection baseline compute budget records no random subsets")
    require_grid(selection, ["participant_id", "method", "channels_k"],
                 [range(1,44), sorted(fixed_methods | {"RANDOM"}), sorted(selection_ks)], "selection baselines")
    finite_values(selection, ["macro_f1"], "selection baselines", bounded=True)
    for k in sorted(selection_ks):
        count = int(budget['actually_run']['n_subsets_by_k'][str(k)])
        g = selection_raw[selection_raw.channels_k == k]
        require_grid(g,["participant_id","draw"],[range(1,44),range(count)],"random subset draws")
        finite_values(g,["macro_f1"],"random subsets",bounded=True)
        expected = g.groupby('participant_id').macro_f1.mean().sort_index()
        saved = selection[(selection.method == 'RANDOM') & (selection.channels_k == k)].set_index('participant_id').macro_f1.sort_index()
        if not np.allclose(expected, saved):
            fail("random mean does not match the saved draw distribution")

    stability = read_csv("artifacts/stability/inner_fold_agreement.csv")
    if stability.outer_participant.nunique() != EXPECTED_GRABMYO:
        fail("inner-fold stability does not cover all outer participants")
    cross = read_csv("artifacts/cross_session/cross_session_metrics.csv")
    require_participant_coverage(cross, "participant_id", EXPECTED_GRABMYO,
                                 "cross-session results")
    for design,sessions in (("CS1", [1,2,3]), ("CS2", [3])):
        require_grid(cross[cross.design == design],["participant_id","test_session"],
                     [range(1,44),sessions],"cross-session")
    faith = read_csv("artifacts/faithfulness/deletion_curves.csv")
    require_participant_coverage(faith, "participant_id", EXPECTED_GRABMYO,
                                 "faithfulness deletion curves")
    for arm in ("remove_top", "remove_bottom"):
        if faith[faith.arm == arm].participant_id.nunique() != EXPECTED_GRABMYO:
            fail(f"faithfulness arm {arm} is incomplete")
        require_grid(faith[faith.arm == arm], ["participant_id", "n_kept"],
                     [range(1,44),range(2,16,2)],"faithfulness arm")
    finite_values(faith,["macro_f1"],"faithfulness",bounded=True)

    db5 = read_csv("artifacts/db5/db5_full_channel_metrics.csv")
    require_participant_coverage(db5, "participant_id", EXPECTED_DB5,
                                 "DB5 full-channel results")
    db5_curve = read_csv("artifacts/db5/db5_sparse_curve.csv")
    require_participant_coverage(db5_curve, "participant_id", EXPECTED_DB5,
                                 "DB5 sparse curve")
    if not set(db5_curve.channels_k.astype(int)).issuperset(set(range(1, 17))):
        fail("DB5 sparse curve does not cover k=1..16")
    db5_ranks = read_csv("artifacts/db5/db5_rankings.csv")
    require_participant_coverage(db5_ranks, "outer_participant", EXPECTED_DB5,
                                 "DB5 rankings")
    validate_sparse_subsets(db5_curve, db5_ranks, range(1,11), lambdas=(0.,))

    bipolar = read_csv("artifacts/bipolar/bipolar_full_channel_metrics.csv")
    require_participant_coverage(bipolar, "participant_id", EXPECTED_GRABMYO,
                                 "bipolar full-channel results")
    if not (bipolar.channels_k.astype(int) == 8).all():
        fail("bipolar full-channel results contain non-8-channel rows")
    bipolar_ranks = read_csv("artifacts/bipolar/bipolar_rankings.csv")
    bipolar_scores = read_csv("artifacts/bipolar/bipolar_scores.csv")
    bipolar_curve = read_csv("artifacts/bipolar/bipolar_sparse_curve.csv")
    require_participant_coverage(bipolar_ranks, "outer_participant", EXPECTED_GRABMYO,
                                 "bipolar rankings")
    require_participant_coverage(bipolar_scores, "outer_participant", EXPECTED_GRABMYO,
                                 "bipolar attribution scores")
    require_participant_coverage(bipolar_curve, "participant_id", EXPECTED_GRABMYO,
                                 "bipolar sparse curve")
    if len(bipolar_ranks) != EXPECTED_GRABMYO * 4:
        fail("bipolar rankings do not contain 43 x 4 lambda rows")
    if len(bipolar_scores) != EXPECTED_GRABMYO * 8:
        fail("bipolar attribution scores do not contain 43 x 8 channel rows")
    if not set(bipolar_curve.channels_k.astype(int)).issuperset(set(range(1, 9))):
        fail("bipolar sparse curve does not cover k=1..8")
    for (pid, lam), g in bipolar_ranks.groupby(["outer_participant", "lambda"]):
        channels = [int(x) for x in str(g.iloc[0].ranking).split(";")]
        if sorted(channels) != list(range(1, 9)):
            fail(f"bipolar ranking for participant {pid}, lambda {lam} is not a permutation of 1..8")
    validate_sparse_subsets(bipolar_curve, bipolar_ranks, range(1, 44), n_channels=8)


def verify_completion() -> None:
    """Completion analyses (decision log 24): exact grids, primary subsets, split disjointness."""
    import json
    build = json.loads(require_file("artifacts/completion_analyses/cache_build.json").read_text())
    if not build.get("builder_reproduces_primary") or build.get("spot_reextraction_max_rel_diff", 1) > 1e-4:
        fail("completion caches were not validated against the primary feature chain")
    for name, classes in (("rest17", 17), ("w150", 16), ("w500", 16)):
        if build[name]["participants"] != 43 or build[name]["classes"] != classes:
            fail(f"completion cache {name} has the wrong cohort or class count")
    prim = read_csv("artifacts/metrics/sparse_curve_subject_metrics.csv")
    prim = prim[prim["lambda"].astype(float) == 0.0].set_index(["participant_id", "channels_k"]).channels
    for name in ("rest17", "w150", "w500"):
        c = read_csv(f"artifacts/completion_analyses/{name}/sparse_curve_subject_metrics.csv")
        if c.duplicated(["participant_id", "channels_k"]).any() or len(c) != 43 * 16:
            fail(f"{name} curve is not an exact 43 x 16 grid")
        if not np.isfinite(c.macro_f1).all() or set(c.n_train_windows) != {200000}:
            fail(f"{name} curve has nonfinite scores or a different training budget")
        got = c.set_index(["participant_id", "channels_k"]).channels.sort_index()
        if not got.equals(prim.sort_index()):
            fail(f"{name} curve did not use the primary outer-fold electrode subsets")
    fx = json.loads(require_file("artifacts/completion_analyses/fixed_layout/summary.json").read_text())
    if not fx.get("original_lambda05_dropped_reproduced"):
        fail("fixed-layout rerun did not reproduce the original lambda = 0.5 layout")
    fl = read_csv("artifacts/completion_analyses/fixed_layout/per_participant.csv")
    for split, parity in (("dev_odd_test_even", 0), ("dev_even_test_odd", 1)):
        t = set(fl[fl.split == split].test_participant.astype(int))
        if t != {q for q in range(1, 44) if q % 2 == parity}:
            fail(f"fixed-layout split {split} has the wrong test participants")
    read_csv("artifacts/completion_analyses/completion_kstar.csv")


def main() -> int:
    if "--revision-dir" in sys.argv:
        i = sys.argv.index("--revision-dir")
        return subprocess.run([sys.executable, str(ROOT / "scripts/68_verify_revision.py"), "--revision-dir", sys.argv[i+1]], cwd=ROOT).returncode
    try:
        audit = subprocess.run([sys.executable, str(ROOT / "scripts/54_audit_predictions.py")], cwd=ROOT)
        if audit.returncode:
            fail("baseline prediction audit failed")
        verify_rankings()
        verify_metrics()
        verify_statistics()
        verify_phase_outputs()
        verify_extension()
        verify_completion()
    except (RuntimeError, ValueError, KeyError) as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        print("No manuscript macros were generated.", file=sys.stderr)
        return 1

    generator = ROOT / "scripts" / "40_generate_macros.py"
    result = subprocess.run([sys.executable, str(generator)], cwd=ROOT, check=False)
    if result.returncode != 0:
        print("[FAIL] macro generation refused the result graph", file=sys.stderr)
        return result.returncode
    provenance = ROOT / "manuscript" / "generated" / "macro_provenance.csv"
    if not provenance.exists() or provenance.stat().st_size == 0:
        print("[FAIL] macro provenance was not written", file=sys.stderr)
        return 1
    result = subprocess.run([sys.executable, str(ROOT / "scripts/56_extension_report.py")], cwd=ROOT)
    if result.returncode:
        return result.returncode
    print("[PASS] strict result verification and macro provenance completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
