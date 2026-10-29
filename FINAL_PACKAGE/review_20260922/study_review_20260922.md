# Whole-study review and completion audit

Date: 2026-09-22. Status: core analysis and attribution upgrade complete; strict verification and PDF visual review passed.

## Findings and actions

| Severity | Finding | Action |
|---|---|---|
| Critical | The latest corrected bipolar artifacts were incomplete despite COMPLETE status. | Resume the corrected protocol; require full grids before publication. |
| High | Fold-pooled attribution MAD measures between-group variation and hides person-level heterogeneity. | Add equal-person median/MAD ranking as an explicitly post-hoc extension, with all candidate penalties reported. |
| High | Identical selected sets had inconsistent saved scores for one outer participant. | Recompute that participant using the shared-fit protocol; archive prior curve and regenerate downstream inference. |
| High | Result gate checked marginal counts but not all key combinations, score reconstruction or selected-set provenance. | Enforce exact grids, finite metrics, outer exclusion and score/ranking/subset reconstruction. |
| High | Leakage audit hard-coded PASS and incorrectly asserted lambda 0.5 was prespecified. | Replace with artifact-based checks and explicit historical limitations. |
| High | Main README claimed a superseded six-electrode result; old build entry points called obsolete scripts. | Remove unsupported headline and replace build entry points with a strict current pipeline. |
| High | Original training budgets were calibrated using held-out folds. | Disclose development contamination. A later rerun does not turn those participants into a pristine development-independent test set. |
| Medium | Saved baseline predictions had not been part of the publication gate. | Reconstruct every classifier/participant metric and generate per-gesture summaries with participant-level intervals. |
| Medium | PutEMG appears in the manuscript despite current instructions limiting experiments to GRABMyo and DB5. | Removed it from the active manuscript and generators under the two-dataset instruction; preserved historical files. |
| Medium | Author declarations and repository DOI remain placeholders. | Preserve unresolved declarations; never invent institutional approval, funding or author roles. |

## Methodological interpretation

The original procedure correctly excludes the outer participant before grouped inner fitting.
The new score uses the same out-of-fold person vectors, normalises each person across electrodes,
and then takes the median and unscaled MAD across people. It preserves the original TreeSHAP
semantics and sampling, so it is a targeted test of aggregation rather than an unrelated model.
The MAD describes heterogeneity; it is not a standard error, because person vectors share inner
models. All four penalties and all electrode counts are evaluated. No outer outcome selects a
penalty or a preferred method.

TreeSHAP feature attribution is model-dependent. Summing absolute feature attributions within
an electrode is not the Shapley value of an electrode coalition, nor evidence of causal muscle
importance. Correlated features can redistribute attribution. See the official TreeExplainer
[documentation](https://shap.readthedocs.io/en/latest/generated/shap.TreeExplainer.html).

Participant-level resampling avoids window pseudoreplication, but LOSO training sets overlap.
The intervals describe variation in the observed out-of-fold participant scores; they do not
fully propagate variation from retraining on a new cohort. See Bengio and Grandvalet,
[No Unbiased Estimator of the Variance of K-Fold Cross-Validation](https://www.jmlr.org/papers/volume5/grandvalet04a/grandvalet04a.pdf).

A failed scientific gate is not a software defect: if the upgraded penalty does not improve
held-out participant performance, retain the negative result. Do not relax the margin, choose
a favourable test participant subset, or choose lambda using outer scores.

## Completion and remaining limits

The corrected bipolar evaluation, statistics, macros, tables, figures and both manuscript PDFs
are complete. Strict verification passed, and every final PDF page was visually inspected.
Conditional CNN/IG, window-length and rest-inclusive experiments are not currently evidence.
They must remain explicitly omitted unless executed on the downloaded data.

The participant-level attribution extension is complete and independently verified through the
extension checks in `scripts/16_verify_results.py`. Its complete corrected comparison family
does not establish a penalty benefit. This is a scientific negative result, not an incomplete
software gate. Exact results and fingerprints are in `artifacts/participant_attribution/`.
