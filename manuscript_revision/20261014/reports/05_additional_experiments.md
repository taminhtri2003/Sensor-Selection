# Additional experiment validation

| Priority   | Experiment                         | Coverage                                             | Protocol                                                                                        | Interpretation                                                                         |
|:-----------|:-----------------------------------|:-----------------------------------------------------|:------------------------------------------------------------------------------------------------|:---------------------------------------------------------------------------------------|
| A          | full primary geometric count curve | completed, 43 participants x16 counts                | 300 boosting rounds / 200000 train windows; exact same outer sample; count12/full16 exact reuse | Minimum count 15 (CI), 15 (null Holm) at0.02; direct12-site mean superiority uncertain |
| B          | gesture degradation                | completed, 43 paired participants                    | canonical prediction rows, all16 gestures                                                       | Holm16; no window-level inference                                                      |
| C          | participant degradation            | completed, 43 paired participants                    | primary full16 and SHAP12 predictions                                                           | Descriptive heterogeneity; mean NI is not individual preservation                      |
| D          | shared-resource attribution        | completed, 43 participants x2methods x2counts        | same5models and validation observations; 3group permutations                                    | Grouping and resource changes confounded; results below                                |
| E          | Rest17                             | completed, 43 x16counts                              | raw-derived cache; unchanged primary rankings                                                   | Within-task full16 reference                                                           |
| E          | 150/500ms                          | completed, each43 x16counts                          | raw re-extraction; unchanged rankings                                                           | same window count differs in recorded duration                                         |
| E          | random forest                      | completed, 43 x2counts                               | pre-existing RF parameters; XGB-selected layouts                                                | No RF minimum count or reranking claim                                                 |
| E          | participant aggregation            | fresh provenance-compatible isolated refit completed | all4penalties x16counts x43participants                                                         | Unselected fixed penalties; exact original subset reuse tagged                         |
| F          | independent fixed-layout cohort    | not available                                        | no new same-montage recordings                                                                  | Cannot complete external/prospective layout validation from existing data              |

## Shared-resource performance

|         k |   mean_shap |   mean_permutation |         n |   mean_diff |     lcb95 |    ucb95 |    p_raw |   n_positive |   n_negative |   n_tied |   p_holm |
|----------:|------------:|-------------------:|----------:|------------:|----------:|---------:|---------:|-------------:|-------------:|---------:|---------:|
|  6.000000 |    0.480333 |           0.449402 | 43.000000 |    0.030931 |  0.021063 | 0.041032 | 0.000003 |    31.000000 |     4.000000 | 8.000000 | 0.000006 |
| 12.000000 |    0.528210 |           0.527970 | 43.000000 |    0.000240 | -0.002925 | 0.003413 | 0.976168 |    22.000000 |    21.000000 | 0.000000 | 0.976168 |

## Measured costs

| Unnamed: 0                    |       mean |      std |        min |        max |
|:------------------------------|-----------:|---------:|-----------:|-----------:|
| shared_training_seconds       | 117.138471 | 3.691192 | 114.700987 | 136.403887 |
| shap_selection_seconds        |   3.965254 | 0.163559 |   3.806626 |   4.307044 |
| permutation_selection_seconds |  10.633331 | 1.063830 |   9.846648 |  13.303973 |

## Participant-aggregation penalty

|   lambda |   k |   n |   mean_diff |     lcb95 |    ucb95 |    p_raw |   n_positive |   n_negative |   n_tied |   p_holm | supports_benefit   | supports_harm   |
|---------:|----:|----:|------------:|----------:|---------:|---------:|-------------:|-------------:|---------:|---------:|:-------------------|:----------------|
| 0.250000 |   4 |  43 |    0.000000 |  0.000000 | 0.000000 | 1.000000 |            0 |            0 |       43 | 1.000000 | False              | False           |
| 0.250000 |   6 |  43 |    0.000000 |  0.000000 | 0.000000 | 1.000000 |            0 |            0 |       43 | 1.000000 | False              | False           |
| 0.250000 |   8 |  43 |    0.000182 | -0.000759 | 0.001071 | 1.000000 |            2 |            1 |       40 | 1.000000 | False              | False           |
| 0.250000 |  12 |  43 |    0.000000 |  0.000000 | 0.000000 | 1.000000 |            0 |            0 |       43 | 1.000000 | False              | False           |
| 0.500000 |   4 |  43 |    0.000118 |  0.000000 | 0.000354 | 0.317311 |            1 |            0 |       42 | 1.000000 | False              | False           |
| 0.500000 |   6 |  43 |    0.000000 |  0.000000 | 0.000000 | 1.000000 |            0 |            0 |       43 | 1.000000 | False              | False           |
| 0.500000 |   8 |  43 |    0.000045 | -0.001066 | 0.001103 | 0.892738 |            3 |            2 |       38 | 1.000000 | False              | False           |
| 0.500000 |  12 |  43 |    0.000000 |  0.000000 | 0.000000 | 1.000000 |            0 |            0 |       43 | 1.000000 | False              | False           |
| 1.000000 |   4 |  43 |    0.002995 |  0.000648 | 0.006010 | 0.027708 |            6 |            0 |       37 | 0.332494 | False              | False           |
| 1.000000 |   6 |  43 |    0.000000 |  0.000000 | 0.000000 | 1.000000 |            0 |            0 |       43 | 1.000000 | False              | False           |
| 1.000000 |   8 |  43 |    0.000530 | -0.000762 | 0.001800 | 0.612090 |            5 |            2 |       36 | 1.000000 | False              | False           |
| 1.000000 |  12 |  43 |    0.000000 |  0.000000 | 0.000000 | 1.000000 |            0 |            0 |       43 | 1.000000 | False              | False           |

## Fixed-count classifier sensitivity

| condition       |   margin |   k |   n |   mean_k |   mean_reference |   mean_diff |     lcb95 |     ucb95 |   historical_percentile_tail |   p_null_studentized | ni_percentile_ci   |   historical_tail_holm |   p_null_holm | ni_historical_holm   | ni_null_holm   |
|:----------------|---------:|----:|----:|---------:|-----------------:|------------:|----------:|----------:|-----------------------------:|---------------------:|:-------------------|-----------------------:|--------------:|:---------------------|:---------------|
| RF_fixed_counts | 0.010000 |  12 |  43 | 0.493606 |         0.501443 |   -0.007837 | -0.010446 | -0.005238 |                     0.055300 |             0.055594 | False              |               0.055300 |      0.055594 | False                | False          |
| RF_fixed_counts | 0.020000 |  12 |  43 | 0.493606 |         0.501443 |   -0.007837 | -0.010446 | -0.005238 |                     0.000100 |             0.000100 | True               |               0.000100 |      0.000100 | True                 | True           |
| RF_fixed_counts | 0.030000 |  12 |  43 | 0.493606 |         0.501443 |   -0.007837 | -0.010446 | -0.005238 |                     0.000100 |             0.000100 | True               |               0.000100 |      0.000100 | True                 | True           |

Primary score reproduction is verified from saved predictions, not merely read from old tables. Current metrics match historical full16/SHAP12 at floating precision; original predictions were not archived, so prediction-level identity to the old run is not claimed. Shared-method and extension fits that reused an original identical channel set are explicitly tagged and verified against source rows.

The first500ms completion invocation saved the last fold then failed a runner assertion because its requested one-participant set was compared with the complete resumed cohort. The queue was corrected to request the full cohort without modifying the fingerprinted curve runner. A subsequent full-cohort resume passed; both logs are retained. No missing fold was invented or excluded.

The historical extension manifest still has a source-hash failure. A current isolated refit supplies provenance-compatible results; the old fingerprint was not rewritten. The final revision gate verifies the isolated result tree. Current protocols and amendments distinguish these exploratory checks from original primary and secondary tracks. Early shared-model folds ran while CPU RF jobs were active; later folds did not. Recorded times therefore describe the executed workstation load and are not an isolated runtime benchmark.
