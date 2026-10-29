# Statistical validation

The statistical unit is the participant: 43 in every GRABMyo LOSO analysis, ten in DB5, and 21/22 in the fixed-layout test halves. No confidence interval or hypothesis test uses windows as independent replicates.

The original percentile-interval decision is preserved. The historical unshifted bootstrap tail is identified as a percentile-tail calculation, not silently presented as a bootstrap null distribution. The new exploratory sensitivity resamples mean-centred paired differences, studentizes each resampled mean and compares its upper tail with (mean difference + margin)/standard error, using a plus-one probability. Holm covers the fifteen count tests per condition/margin/penalty. Both calculations use 10,000 resamples and the unchanged seed20260728. They are conditional on overlapping fitted LOSO models and do not propagate complete refitting uncertainty.

## Count decisions

| condition              |   margin |   n |   kstar_percentile |   kstar_historical_holm |   kstar_null_studentized_holm |
|:-----------------------|---------:|----:|-------------------:|------------------------:|------------------------------:|
| bipolar                | 0.010000 |  43 |         nan        |              nan        |                    nan        |
| bipolar                | 0.020000 |  43 |         nan        |              nan        |                    nan        |
| bipolar                | 0.030000 |  43 |           7.000000 |                7.000000 |                      7.000000 |
| db5                    | 0.010000 |  10 |         nan        |              nan        |                    nan        |
| db5                    | 0.020000 |  10 |          12.000000 |              nan        |                    nan        |
| db5                    | 0.030000 |  10 |          12.000000 |               12.000000 |                    nan        |
| geometric_primary      | 0.010000 |  43 |          15.000000 |               15.000000 |                     15.000000 |
| geometric_primary      | 0.020000 |  43 |          15.000000 |               15.000000 |                     15.000000 |
| geometric_primary      | 0.030000 |  43 |          11.000000 |               12.000000 |                     12.000000 |
| participant_lambda0    | 0.010000 |  43 |          14.000000 |               14.000000 |                     14.000000 |
| participant_lambda0    | 0.020000 |  43 |          12.000000 |               12.000000 |                     12.000000 |
| participant_lambda0    | 0.030000 |  43 |          11.000000 |               11.000000 |                     11.000000 |
| participant_lambda0.25 | 0.010000 |  43 |          14.000000 |               14.000000 |                     14.000000 |
| participant_lambda0.25 | 0.020000 |  43 |          12.000000 |               12.000000 |                     12.000000 |
| participant_lambda0.25 | 0.030000 |  43 |          11.000000 |               11.000000 |                     11.000000 |
| participant_lambda0.5  | 0.010000 |  43 |          14.000000 |               14.000000 |                     14.000000 |
| participant_lambda0.5  | 0.020000 |  43 |          12.000000 |               12.000000 |                     12.000000 |
| participant_lambda0.5  | 0.030000 |  43 |          11.000000 |               11.000000 |                     11.000000 |
| participant_lambda1    | 0.010000 |  43 |          14.000000 |               14.000000 |                     14.000000 |
| participant_lambda1    | 0.020000 |  43 |          12.000000 |               12.000000 |                     12.000000 |
| participant_lambda1    | 0.030000 |  43 |          11.000000 |               11.000000 |                     11.000000 |
| primary_lambda0        | 0.010000 |  43 |          14.000000 |               14.000000 |                     14.000000 |
| primary_lambda0        | 0.020000 |  43 |          12.000000 |               12.000000 |                     12.000000 |
| primary_lambda0        | 0.030000 |  43 |          11.000000 |               11.000000 |                     11.000000 |
| primary_lambda0.25     | 0.010000 |  43 |          14.000000 |               14.000000 |                     14.000000 |
| primary_lambda0.25     | 0.020000 |  43 |          12.000000 |               12.000000 |                     12.000000 |
| primary_lambda0.25     | 0.030000 |  43 |          11.000000 |               11.000000 |                     11.000000 |
| primary_lambda0.5      | 0.010000 |  43 |          14.000000 |               14.000000 |                     14.000000 |
| primary_lambda0.5      | 0.020000 |  43 |          12.000000 |               12.000000 |                     12.000000 |
| primary_lambda0.5      | 0.030000 |  43 |          11.000000 |               11.000000 |                     11.000000 |
| primary_lambda1        | 0.010000 |  43 |          14.000000 |               14.000000 |                     14.000000 |
| primary_lambda1        | 0.020000 |  43 |          12.000000 |               12.000000 |                     12.000000 |
| primary_lambda1        | 0.030000 |  43 |          11.000000 |               11.000000 |                     11.000000 |
| rest17                 | 0.010000 |  43 |          14.000000 |               14.000000 |                     14.000000 |
| rest17                 | 0.020000 |  43 |          12.000000 |               12.000000 |                     12.000000 |
| rest17                 | 0.030000 |  43 |          11.000000 |               11.000000 |                     11.000000 |
| w150                   | 0.010000 |  43 |          14.000000 |               14.000000 |                     14.000000 |
| w150                   | 0.020000 |  43 |          12.000000 |               12.000000 |                     12.000000 |
| w150                   | 0.030000 |  43 |          10.000000 |               11.000000 |                     11.000000 |
| w500                   | 0.010000 |  43 |          14.000000 |               14.000000 |                     14.000000 |
| w500                   | 0.020000 |  43 |          12.000000 |               12.000000 |                     12.000000 |
| w500                   | 0.030000 |  43 |          10.000000 |               11.000000 |                     11.000000 |

## Matched primary predictions

| condition   |   margin |   n |   mean_diff |     lcb95 |     ucb95 |    p_raw |   n_positive |   n_negative |   n_tied |   p_null_studentized | ni_percentile_ci   |
|:------------|---------:|----:|------------:|----------:|----------:|---------:|-------------:|-------------:|---------:|---------------------:|:-------------------|
| shap12      | 0.010000 |  43 |   -0.013304 | -0.016041 | -0.010598 | 0.000000 |            1 |           42 |        0 |             0.988901 | False              |
| shap12      | 0.020000 |  43 |   -0.013304 | -0.016041 | -0.010598 | 0.000000 |            1 |           42 |        0 |             0.000100 | True               |
| shap12      | 0.030000 |  43 |   -0.013304 | -0.016041 | -0.010598 | 0.000000 |            1 |           42 |        0 |             0.000100 | True               |
| geom12      | 0.010000 |  43 |   -0.019347 | -0.025365 | -0.013199 | 0.000000 |            7 |           36 |        0 |             0.997100 | False              |
| geom12      | 0.020000 |  43 |   -0.019347 | -0.025365 | -0.013199 | 0.000000 |            7 |           36 |        0 |             0.418158 | False              |
| geom12      | 0.030000 |  43 |   -0.019347 | -0.025365 | -0.013199 | 0.000000 |            7 |           36 |        0 |             0.000600 | True               |

## Direct SHAP12 minus geometric12

| comparison                      |   n |   mean_diff |     lcb95 |    ucb95 |    p_raw |   n_positive |   n_negative |   n_tied |
|:--------------------------------|----:|------------:|----------:|---------:|---------:|-------------:|-------------:|---------:|
| primary SHAP12 minus geometry12 |  43 |    0.006043 | -0.001019 | 0.012737 | 0.024033 |           30 |           13 |        0 |

The interval concerns the mean; Wilcoxon concerns signed ranks. A nominal rank-test result cannot establish a positive mean advantage when that mean interval crosses zero. SHAP's NI pass and geometry's NI failure do not constitute a direct between-method test. No equivalence inference is made.

## Participant and gesture limits

{
  "n": 43,
  "mean": -0.013303960715993532,
  "median": -0.01246981322073526,
  "sd": 0.00926339240442972,
  "min": -0.036071473188607595,
  "max": 0.014350688581827808,
  "n_improved": 1,
  "n_loss_over_margin002": 11,
  "baseline_difference_spearman": -0.04500151011778919,
  "interpretation": "descriptive; baseline is mathematically coupled to its difference; no individual non-inferiority guarantee",
  "worst_participant_id": 27,
  "q05": -0.025196133238263575,
  "q10": -0.024575297952071452,
  "q25": -0.020162005393481508,
  "q75": -0.0072828742889811116,
  "q90": -0.004050168859064484,
  "q95": -0.0019698515446250255
}

|   gesture_id |   mean_full16 |   mean_shap12 |         n |   mean_diff |     lcb95 |     ucb95 |    p_raw |   n_positive |   n_negative |   n_tied |   p_holm |
|-------------:|--------------:|--------------:|----------:|------------:|----------:|----------:|---------:|-------------:|-------------:|---------:|---------:|
|     1.000000 |      0.448690 |      0.436746 | 43.000000 |   -0.011944 | -0.020968 | -0.003510 | 0.008627 |    14.000000 |    29.000000 | 0.000000 | 0.086271 |
|     2.000000 |      0.307753 |      0.283505 | 43.000000 |   -0.024247 | -0.035645 | -0.013248 | 0.000193 |    10.000000 |    33.000000 | 0.000000 | 0.002707 |
|     3.000000 |      0.519174 |      0.516150 | 43.000000 |   -0.003024 | -0.011689 |  0.005447 | 0.537762 |    19.000000 |    24.000000 | 0.000000 | 1.000000 |
|     4.000000 |      0.347581 |      0.340640 | 43.000000 |   -0.006941 | -0.013651 | -0.000051 | 0.013418 |    14.000000 |    29.000000 | 0.000000 | 0.120758 |
|     5.000000 |      0.489580 |      0.483007 | 43.000000 |   -0.006574 | -0.017639 |  0.004480 | 0.261802 |    18.000000 |    25.000000 | 0.000000 | 1.000000 |
|     6.000000 |      0.603941 |      0.592419 | 43.000000 |   -0.011522 | -0.022189 | -0.000792 | 0.016575 |    17.000000 |    26.000000 | 0.000000 | 0.132600 |
|     7.000000 |      0.502834 |      0.503776 | 43.000000 |    0.000941 | -0.005886 |  0.008287 | 1.000000 |    21.000000 |    22.000000 | 0.000000 | 1.000000 |
|     8.000000 |      0.499220 |      0.489325 | 43.000000 |   -0.009896 | -0.021512 |  0.000579 | 0.157416 |    20.000000 |    23.000000 | 0.000000 | 0.787078 |
|     9.000000 |      0.387274 |      0.357242 | 43.000000 |   -0.030031 | -0.043625 | -0.016669 | 0.000123 |    11.000000 |    32.000000 | 0.000000 | 0.001838 |
|    10.000000 |      0.532966 |      0.513781 | 43.000000 |   -0.019185 | -0.029925 | -0.009384 | 0.000412 |    12.000000 |    31.000000 | 0.000000 | 0.005360 |
|    11.000000 |      0.939502 |      0.939159 | 43.000000 |   -0.000343 | -0.001771 |  0.001212 | 0.488139 |    20.000000 |    21.000000 | 2.000000 | 1.000000 |
|    12.000000 |      0.830083 |      0.819414 | 43.000000 |   -0.010669 | -0.020157 | -0.001441 | 0.006588 |    11.000000 |    32.000000 | 0.000000 | 0.079052 |
|    13.000000 |      0.813083 |      0.803749 | 43.000000 |   -0.009333 | -0.015642 | -0.003552 | 0.007694 |    14.000000 |    29.000000 | 0.000000 | 0.084633 |
|    14.000000 |      0.486816 |      0.441223 | 43.000000 |   -0.045594 | -0.059423 | -0.032284 | 0.000000 |     7.000000 |    36.000000 | 0.000000 | 0.000000 |
|    15.000000 |      0.542733 |      0.536090 | 43.000000 |   -0.006643 | -0.014191 |  0.001358 | 0.024033 |    14.000000 |    29.000000 | 0.000000 | 0.168230 |
|    16.000000 |      0.409783 |      0.391924 | 43.000000 |   -0.017860 | -0.032219 | -0.003405 | 0.024033 |    17.000000 |    26.000000 | 0.000000 | 0.168230 |

The sixteen gesture contrasts receive one Holm adjustment. Loss counts and extremes are descriptive, not individual NI tests. Baseline-difference correlation is mathematically coupled and is not used to infer causes. Near-boundary DB5 and reverse-layout results are retained at full precision. In DB5, even the0.03 margin yields no reduced count under the null-centred Holm sensitivity, whereas historical tail-Holm supports12 there. This disagreement is a small-cohort inference sensitivity, not a reason to select a favorable construction.

## Additional families

Resource-matched comparison: Holm over two counts. Participant-versus-fold extension: Holm over sixty comparisons. Penalty within person aggregation: Holm over twelve. Historical DB5 and bipolar seed diagnostics are recomputed for every reduced count using their original seeds1000-1199; no favorable seed is substituted. Cross-session contrasts remain explicitly exploratory and uncorrected. The post-hoc selector-activity audit reports every fixed penalty/count for fold and participant aggregation. It checks physical input identity and identical-set metric consistency; it adds no significance or equivalence test. Original H2/H3/H4 families contain eight/twelve/fifteen tests; their detailed families were determined post hoc and remain labeled secondary.

Six deterministic unit tests cover null-boundary centring, effect direction, location/scale invariance, invalid participant vectors and Holm monotonicity. Synthetic vectors are used only for tests and contribute no experimental metric. The complete current test suite passed 53 tests; the final QC report records the final run. Source: scripts/66_revision_statistics.py, tests/test_revision_statistics.py, scripts/16_verify_results.py --revision-dir manuscript_revision/20261014.
