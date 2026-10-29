# Final study report — explainability-guided electrode reduction for subject-independent sEMG

Date: 2026-09-21. Every number below is taken from `manuscript/generated/macro_provenance.csv`,
which maps each value to the result file it comes from.

## Deliverable
- `manuscript/main_elsevier.pdf` (11 pages, Elsevier `elsarticle` 5p two-column), sources in
  `manuscript/`. Rebuild: `bash scripts/build_manuscript.sh`.
- Package: `FINAL_PACKAGE/`.

## Confirmatory results (frozen plan, GRABMyo, 43 participants, LOSO)
| Hypothesis | Result |
|---|---|
| Baseline | XGBoost Macro-F1 0.542 (95% CI 0.517–0.567); SVM 0.538 (lower bound, 40k windows); RF 0.502. XGBoost vs SVM not different (p_Holm = 0.154). |
| H1 non-inferiority | **Supported.** k* = 12 of 16 electrodes at δ = 0.02 (Δ = −0.0132, LCB −0.0160); k = 11 fails (LCB −0.0245). k* = 14 at δ = 0.01, 11 at δ = 0.03. Identical for all λ; survives fixed-sequence testing. |
| H2 vs random | **Supported** at k = 4, 6, 8, 12 (largest +0.0370 at k = 6, p_Holm < 0.001). |
| H3 stability penalty | **Not supported.** 0/12 contrasts significant; U_c/A_c median 2.4%; the top-12 set changes in at most 1/43 folds. |
| H4 faithfulness | **Supported.** Top-removed < random < bottom-removed at every retained size; 14/15 contrasts significant. |

## Exploratory results
- A geometric (data-free, evenly spread) layout matched attribution at k = 4, 8 and 12 (p = 0.986, 0.267, 0.058); attribution was better only at k = 6.
- Cross-session: no additional cross-day loss on top of the cross-user gap. The CS2 gain (+0.0210) is confounded with doubled training data.
- **Bipolar pairs (after fixing the feature threshold): no pair removable at δ = 0.02** (k = 7 LCB −0.0203, failing under all 200 bootstrap seeds). This reverses the invalid earlier claim of k* = 7.
- DB5 (n = 10): k = 12 formally passes (LCB −0.01999, 95.5% of seeds) but k = 13–15 fail; there is no k* under fixed-sequence testing. Reported as fragile.
- Fixed 12-electrode layout (post hoc, one split): Δ = −0.0124 (CI −0.0179 to −0.0077).
- IEMG redundancy: removing it changed Macro-F1 by −0.0005; channel-rank ρ = 0.994.

## What the 2026-09-21 audit changed (Decisions 11–16)
1. P8 faithfulness had mixed training budgets across arms; recomputed under one protocol.
2. P11 bipolar used features with a suppressed count threshold; re-extracted and recomputed.
3. λ was never selected; all four reported, and the "SR-CFA is the method" framing was dropped.
4. The previous manuscript contained numbers matching no artifact, named-muscle claims with invented
   frequencies, a macro generator with literal values, and a 3-participant result reported as 43.
   It was rewritten from generated macros, and a checker now blocks typed-in numbers.
5. 14 of 30 citations had non-existent or wrong DOIs; the bibliography was rebuilt from Crossref /
   arXiv (35 entries), and the literature matrix now flags 14 bad rows.
6. Superseded deliverables archived under `_archive_invalid/` with READMEs.

## Not done (disclosed in the manuscript)
- P10 CNN / cross-model attribution, window-length sensitivity, 17-class task.
- λ selection rule (the plan left it unspecified).
- Physical-bipolar or amputee data; online evaluation.

## Items for the authors
- `\journal{Physiological Measurement}` is an IOP journal, while the requested template is
  Elsevier `elsarticle`. Confirm the target journal before submission.
- Author list, affiliations and corresponding-author e-mail were kept from the previous draft
  unchanged; please verify them.
- The H2–H4 test families and the faithfulness protocol-check tolerance were specified after
  results existed. They are declared as deviations; decide whether to keep that framing.
