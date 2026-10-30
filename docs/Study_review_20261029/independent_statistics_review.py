"""Read-only reconstruction of saved participant inference, independent of study functions.

Run with the scientific Python environment from the repository root.
All outputs are confined to this review folder; no fits or result edits occur.
"""
from pathlib import Path
import hashlib
import json

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
REV = ROOT / "manuscript_revision/20261014"
SEED, RESAMPLES = 20260728, 10000
sources = set()


def read(relative):
    path = ROOT / relative
    sources.add(path)
    return pd.read_csv(path)


def adjust_holm(values):
    order = np.argsort(values)
    ordered = np.asarray(values)[order]
    answer = np.empty(len(ordered))
    answer[order] = np.minimum(1, np.maximum.accumulate(ordered * np.arange(len(ordered), 0, -1)))
    return answer


def null_t_distribution(difference, indices):
    residual = difference - difference.mean()
    resampled = residual[indices]
    numerator = resampled.mean(axis=1)
    denominator = resampled.std(axis=1, ddof=1) / np.sqrt(len(difference))
    with np.errstate(divide="ignore", invalid="ignore"):
        statistic = numerator / denominator
    statistic[(denominator == 0) & (numerator == 0)] = 0
    return statistic


def main():
    curves = {}
    primary = read("artifacts/metrics/sparse_curve_subject_metrics.csv")
    extension = read("manuscript_revision/20261014/experiments/attribution_extension/sparse_curve.csv")
    for penalty in [0., .25, .5, 1.]:
        curves[f"primary_lambda{penalty:g}"] = primary[primary["lambda"] == penalty]
        curves[f"participant_lambda{penalty:g}"] = extension[extension["lambda"] == penalty]
    for name in ["rest17", "w150", "w500"]:
        curves[name] = read(f"artifacts/completion_analyses/{name}/sparse_curve_subject_metrics.csv")
    curves["geometric_primary"] = read("manuscript_revision/20261014/experiments/geometric_curve/sparse_curve_subject_metrics.csv")
    curves["db5"] = read("artifacts/db5/db5_sparse_curve.csv")
    bipolar = read("artifacts/bipolar/bipolar_sparse_curve.csv")
    curves["bipolar"] = bipolar[bipolar["lambda"] == 0]

    records, coverage = [], []
    for condition, curve in curves.items():
        n_expected = 10 if condition == "db5" else 43
        reference = 8 if condition == "bipolar" else 16
        assert not curve.duplicated(["participant_id", "channels_k"]).any(), condition
        assert len(curve) == n_expected * reference, condition
        assert set(curve.participant_id) == set(range(1, n_expected + 1)), condition
        wide = curve.pivot(index="participant_id", columns="channels_k", values="macro_f1").sort_index()
        assert set(wide.columns) == set(range(1, reference + 1)), condition
        assert np.isfinite(wide.to_numpy()).all() and ((wide >= 0) & (wide <= 1)).all().all(), condition
        coverage.append({"condition": condition, "participants": len(wide), "counts": reference, "rows": len(curve)})
        indices = np.random.default_rng(SEED).choice(len(wide), size=(RESAMPLES, len(wide)), replace=True)
        for k in range(1, reference):
            difference = (wide[k] - wide[reference]).to_numpy()
            bootstrap_means = difference[indices].mean(axis=1)
            lo, hi = np.percentile(bootstrap_means, [2.5, 97.5])
            se = difference.std(ddof=1) / np.sqrt(len(wide))
            null_t = None if se == 0 else null_t_distribution(difference, indices)
            for margin in [.01, .02, .03]:
                if se == 0:
                    p_null = 1 / (RESAMPLES + 1) if difference.mean() > -margin else 1.
                else:
                    p_null = (1 + np.count_nonzero(null_t >= (difference.mean() + margin) / se)) / (RESAMPLES + 1)
                records.append({"condition": condition, "margin": margin, "k": k, "n": len(wide),
                                "mean_k": wide[k].mean(), "mean_reference": wide[reference].mean(),
                                "mean_diff": difference.mean(), "lcb95": lo, "ucb95": hi,
                                "historical_percentile_tail": max(np.mean(bootstrap_means <= -margin), 1 / RESAMPLES),
                                "p_null_studentized": p_null, "ni_percentile_ci": lo > -margin})
    reconstructed = pd.DataFrame(records)
    for _, group in reconstructed.groupby(["condition", "margin"]):
        for raw, adjusted in [("historical_percentile_tail", "historical_tail_holm"), ("p_null_studentized", "p_null_holm")]:
            reconstructed.loc[group.index, adjusted] = adjust_holm(group[raw].to_numpy())
    reconstructed["ni_historical_holm"] = reconstructed.historical_tail_holm < .025
    reconstructed["ni_null_holm"] = reconstructed.p_null_holm < .025
    saved = read("manuscript_revision/20261014/tables/noninferiority_audit.csv")
    columns = list(saved.columns)
    a = reconstructed[columns].sort_values(["condition", "margin", "k"]).reset_index(drop=True)
    b = saved.sort_values(["condition", "margin", "k"]).reset_index(drop=True)
    pd.testing.assert_frame_equal(a, b, check_dtype=False, check_exact=False, rtol=1e-10, atol=1e-12)
    reconstructed.to_csv(OUT / "independently_recomputed_noninferiority.csv", index=False)
    pd.DataFrame(coverage).to_csv(OUT / "participant_grid_coverage.csv", index=False)

    minimum = []
    for (condition, margin), group in reconstructed.groupby(["condition", "margin"]):
        minimum.append({"condition": condition, "margin": margin, "n": int(group.n.iloc[0]),
                        "kstar_percentile": group.loc[group.ni_percentile_ci, "k"].min(),
                        "kstar_historical_holm": group.loc[group.ni_historical_holm, "k"].min(),
                        "kstar_null_studentized_holm": group.loc[group.ni_null_holm, "k"].min()})
    minimum = pd.DataFrame(minimum)
    saved_minimum = read("manuscript_revision/20261014/tables/kstar_audit.csv")
    pd.testing.assert_frame_equal(minimum, saved_minimum, check_dtype=False, check_exact=False, rtol=1e-10, atol=1e-12)
    minimum.to_csv(OUT / "independently_recomputed_minimum_counts.csv", index=False)

    matched = read("manuscript_revision/20261014/experiments/primary_predictions/participant_metrics.csv")
    assert len(matched) == 43 * 3 and not matched.duplicated(["participant_id", "condition"]).any()
    wide = matched.pivot(index="participant_id", columns="condition", values="macro_f1").sort_index()
    delta = wide.shap12 - wide.full16
    contrast = wide.shap12 - wide.geom12
    indices = np.random.default_rng(SEED).choice(43, size=(RESAMPLES, 43), replace=True)
    interval = np.percentile(delta.to_numpy()[indices].mean(axis=1), [2.5, 97.5])
    geometry_interval = np.percentile(contrast.to_numpy()[indices].mean(axis=1), [2.5, 97.5])
    shap_saved = read("manuscript_revision/20261014/tables/primary_matched_noninferiority.csv")
    shap_saved = shap_saved[(shap_saved.condition == "shap12") & (shap_saved.margin == .02)].iloc[0]
    np.testing.assert_allclose([delta.mean(), *interval], shap_saved[["mean_diff", "lcb95", "ucb95"]].to_numpy(float), rtol=1e-10, atol=1e-12)
    geometry_saved = read("manuscript_revision/20261014/tables/primary_selection_comparison.csv").iloc[0]
    np.testing.assert_allclose([contrast.mean(), *geometry_interval], geometry_saved[["mean_diff", "lcb95", "ucb95"]].to_numpy(float), rtol=1e-10, atol=1e-12)
    summary = {"status": "PASS", "scope": "Independent reconstruction from saved participant-level metrics; no model refitting.",
               "bootstrap_resamples": RESAMPLES, "bootstrap_seed": SEED, "conditions": len(curves),
               "count_margin_rows_recomputed": len(reconstructed), "minimum_count_rows_recomputed": len(minimum),
               "full16_mean": wide.full16.mean(), "shap12_mean": wide.shap12.mean(), "shap12_delta": delta.mean(),
               "shap12_interval": interval.tolist(), "participants_losing_more_than_002": int((delta < -.02).sum()),
               "participants_declining": int((delta < 0).sum()), "worst_participant": int(delta.idxmin()), "worst_delta": delta.min(),
               "shap_minus_geometry": contrast.mean(), "shap_minus_geometry_interval": geometry_interval.tolist(),
               "source_sha256": {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(sources)}}
    (OUT / "independent_statistics_verification.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "source_sha256"}, indent=2))


if __name__ == "__main__":
    main()
