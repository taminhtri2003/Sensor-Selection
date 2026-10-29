# Final study report — explainability-guided sparse sEMG selection

This report was generated from the completed result graph on the run date.  It is intended as the handoff record for the study; numeric claims are not copied from the superseded manuscript.

## Scope and validity rules

- GRABMyo primary endpoint: participant-level Macro-F1 over 16 active gestures, 43 LOSO participants; Rest is excluded.
- Current fitting, scaling and ranking exclude each outer participant. Historical training-budget calibration used test-fold outcomes and remains disclosed.
- Confidence intervals and non-inferiority decisions use participant-level bootstrap resampling (N=43), never windows.
- The full-channel reference and sparse-curve reference are kept separate because the sparse phases use the documented 200,000-window training budget.

## Full-channel LOSO baseline

| model | N | Macro-F1 | 95% LCB | 95% UCB | SD |
| --- | --- | --- | --- | --- | --- |
| M_RandomForest | 43 | 0.502 | 0.475 | 0.528 | 0.090 |
| M_SVM | 43 | 0.538 | 0.513 | 0.562 | 0.085 |
| M_XGBoost | 43 | 0.542 | 0.517 | 0.567 | 0.085 |

Paired model comparisons (Holm-adjusted within the prespecified family):

| A | B | N | mean A−B | LCB | UCB | Holm p | rank-biserial |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M_RandomForest | M_SVM | 43 | -0.036 | -0.044 | -0.028 | 0.000 | -0.968 |
| M_RandomForest | M_XGBoost | 43 | -0.041 | -0.048 | -0.034 | 0.000 | -0.979 |
| M_SVM | M_XGBoost | 43 | -0.005 | -0.011 | 0.002 | 0.154 | -0.252 |

XGBoost was designated as the computational primary for the sparse phases, not a claim that it is significantly better than every baseline.

## Cross-fitted sparse curve

All four frozen λ candidates are shown; no λ is selected using an outer-test score.

| λ | k | N | mean Macro-F1 | SD |
| --- | --- | --- | --- | --- |
| 0.000 | 1 | 43 | 0.181 | 0.040 |
| 0.000 | 2 | 43 | 0.299 | 0.057 |
| 0.000 | 3 | 43 | 0.340 | 0.057 |
| 0.000 | 4 | 43 | 0.397 | 0.071 |
| 0.000 | 5 | 43 | 0.428 | 0.075 |
| 0.000 | 6 | 43 | 0.480 | 0.084 |
| 0.000 | 7 | 43 | 0.500 | 0.085 |
| 0.000 | 8 | 43 | 0.505 | 0.085 |
| 0.000 | 9 | 43 | 0.510 | 0.086 |
| 0.000 | 10 | 43 | 0.515 | 0.083 |
| 0.000 | 11 | 43 | 0.521 | 0.084 |
| 0.000 | 12 | 43 | 0.528 | 0.084 |
| 0.000 | 13 | 43 | 0.530 | 0.083 |
| 0.000 | 14 | 43 | 0.535 | 0.083 |
| 0.000 | 15 | 43 | 0.538 | 0.083 |
| 0.000 | 16 | 43 | 0.541 | 0.084 |
| 0.250 | 1 | 43 | 0.184 | 0.043 |
| 0.250 | 2 | 43 | 0.299 | 0.057 |
| 0.250 | 3 | 43 | 0.340 | 0.057 |
| 0.250 | 4 | 43 | 0.397 | 0.071 |
| 0.250 | 5 | 43 | 0.427 | 0.074 |
| 0.250 | 6 | 43 | 0.480 | 0.084 |
| 0.250 | 7 | 43 | 0.500 | 0.085 |
| 0.250 | 8 | 43 | 0.505 | 0.085 |
| 0.250 | 9 | 43 | 0.509 | 0.086 |
| 0.250 | 10 | 43 | 0.516 | 0.083 |
| 0.250 | 11 | 43 | 0.521 | 0.084 |
| 0.250 | 12 | 43 | 0.528 | 0.084 |
| 0.250 | 13 | 43 | 0.530 | 0.083 |
| 0.250 | 14 | 43 | 0.535 | 0.083 |
| 0.250 | 15 | 43 | 0.538 | 0.083 |
| 0.250 | 16 | 43 | 0.541 | 0.084 |
| 0.500 | 1 | 43 | 0.183 | 0.044 |
| 0.500 | 2 | 43 | 0.299 | 0.059 |
| 0.500 | 3 | 43 | 0.340 | 0.057 |
| 0.500 | 4 | 43 | 0.397 | 0.071 |
| 0.500 | 5 | 43 | 0.427 | 0.074 |
| 0.500 | 6 | 43 | 0.480 | 0.084 |
| 0.500 | 7 | 43 | 0.500 | 0.085 |
| 0.500 | 8 | 43 | 0.505 | 0.085 |
| 0.500 | 9 | 43 | 0.508 | 0.085 |
| 0.500 | 10 | 43 | 0.515 | 0.083 |
| 0.500 | 11 | 43 | 0.520 | 0.084 |
| 0.500 | 12 | 43 | 0.528 | 0.084 |
| 0.500 | 13 | 43 | 0.530 | 0.083 |
| 0.500 | 14 | 43 | 0.535 | 0.083 |
| 0.500 | 15 | 43 | 0.538 | 0.083 |
| 0.500 | 16 | 43 | 0.541 | 0.084 |
| 1.000 | 1 | 43 | 0.185 | 0.046 |
| 1.000 | 2 | 43 | 0.298 | 0.059 |
| 1.000 | 3 | 43 | 0.340 | 0.057 |
| 1.000 | 4 | 43 | 0.398 | 0.071 |
| 1.000 | 5 | 43 | 0.425 | 0.071 |
| 1.000 | 6 | 43 | 0.480 | 0.084 |
| 1.000 | 7 | 43 | 0.500 | 0.085 |
| 1.000 | 8 | 43 | 0.506 | 0.085 |
| 1.000 | 9 | 43 | 0.508 | 0.085 |
| 1.000 | 10 | 43 | 0.515 | 0.083 |
| 1.000 | 11 | 43 | 0.521 | 0.083 |
| 1.000 | 12 | 43 | 0.528 | 0.083 |
| 1.000 | 13 | 43 | 0.530 | 0.083 |
| 1.000 | 14 | 43 | 0.535 | 0.083 |
| 1.000 | 15 | 43 | 0.537 | 0.083 |
| 1.000 | 16 | 43 | 0.541 | 0.084 |

Participant-level non-inferiority at the prespecified δ=0.02 margin:

| λ | δ | k | N | Δ vs k=16 | 95% LCB | 95% UCB | non-inferior |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0.000 | 0.020 | 1 | 43 | -0.360 | -0.383 | -0.337 | no |
| 0.000 | 0.020 | 2 | 43 | -0.242 | -0.260 | -0.223 | no |
| 0.000 | 0.020 | 3 | 43 | -0.202 | -0.221 | -0.182 | no |
| 0.000 | 0.020 | 4 | 43 | -0.144 | -0.159 | -0.131 | no |
| 0.000 | 0.020 | 5 | 43 | -0.113 | -0.128 | -0.099 | no |
| 0.000 | 0.020 | 6 | 43 | -0.061 | -0.071 | -0.051 | no |
| 0.000 | 0.020 | 7 | 43 | -0.041 | -0.049 | -0.033 | no |
| 0.000 | 0.020 | 8 | 43 | -0.037 | -0.044 | -0.029 | no |
| 0.000 | 0.020 | 9 | 43 | -0.032 | -0.039 | -0.025 | no |
| 0.000 | 0.020 | 10 | 43 | -0.026 | -0.031 | -0.020 | no |
| 0.000 | 0.020 | 11 | 43 | -0.020 | -0.025 | -0.016 | no |
| 0.000 | 0.020 | 12 | 43 | -0.013 | -0.016 | -0.011 | yes |
| 0.000 | 0.020 | 13 | 43 | -0.011 | -0.013 | -0.008 | yes |
| 0.000 | 0.020 | 14 | 43 | -0.006 | -0.008 | -0.004 | yes |
| 0.000 | 0.020 | 15 | 43 | -0.004 | -0.006 | -0.002 | yes |
| 0.000 | 0.020 | 16 | 43 | 0.000 | 0.000 | 0.000 | yes |
| 0.250 | 0.020 | 1 | 43 | -0.357 | -0.380 | -0.334 | no |
| 0.250 | 0.020 | 2 | 43 | -0.242 | -0.260 | -0.223 | no |
| 0.250 | 0.020 | 3 | 43 | -0.202 | -0.221 | -0.182 | no |
| 0.250 | 0.020 | 4 | 43 | -0.145 | -0.159 | -0.131 | no |
| 0.250 | 0.020 | 5 | 43 | -0.115 | -0.129 | -0.101 | no |
| 0.250 | 0.020 | 6 | 43 | -0.061 | -0.071 | -0.051 | no |
| 0.250 | 0.020 | 7 | 43 | -0.041 | -0.049 | -0.033 | no |
| 0.250 | 0.020 | 8 | 43 | -0.037 | -0.044 | -0.029 | no |
| 0.250 | 0.020 | 9 | 43 | -0.033 | -0.039 | -0.026 | no |
| 0.250 | 0.020 | 10 | 43 | -0.026 | -0.031 | -0.020 | no |
| 0.250 | 0.020 | 11 | 43 | -0.021 | -0.025 | -0.016 | no |
| 0.250 | 0.020 | 12 | 43 | -0.013 | -0.016 | -0.011 | yes |
| 0.250 | 0.020 | 13 | 43 | -0.011 | -0.013 | -0.008 | yes |
| 0.250 | 0.020 | 14 | 43 | -0.006 | -0.008 | -0.004 | yes |
| 0.250 | 0.020 | 15 | 43 | -0.004 | -0.006 | -0.002 | yes |
| 0.250 | 0.020 | 16 | 43 | 0.000 | 0.000 | 0.000 | yes |
| 0.500 | 0.020 | 1 | 43 | -0.358 | -0.381 | -0.335 | no |
| 0.500 | 0.020 | 2 | 43 | -0.242 | -0.263 | -0.222 | no |
| 0.500 | 0.020 | 3 | 43 | -0.202 | -0.221 | -0.182 | no |
| 0.500 | 0.020 | 4 | 43 | -0.144 | -0.158 | -0.130 | no |
| 0.500 | 0.020 | 5 | 43 | -0.115 | -0.129 | -0.101 | no |
| 0.500 | 0.020 | 6 | 43 | -0.061 | -0.071 | -0.051 | no |
| 0.500 | 0.020 | 7 | 43 | -0.041 | -0.049 | -0.033 | no |
| 0.500 | 0.020 | 8 | 43 | -0.036 | -0.043 | -0.028 | no |
| 0.500 | 0.020 | 9 | 43 | -0.033 | -0.040 | -0.027 | no |
| 0.500 | 0.020 | 10 | 43 | -0.026 | -0.031 | -0.021 | no |
| 0.500 | 0.020 | 11 | 43 | -0.021 | -0.025 | -0.017 | no |
| 0.500 | 0.020 | 12 | 43 | -0.013 | -0.016 | -0.011 | yes |
| 0.500 | 0.020 | 13 | 43 | -0.011 | -0.013 | -0.008 | yes |
| 0.500 | 0.020 | 14 | 43 | -0.006 | -0.008 | -0.004 | yes |
| 0.500 | 0.020 | 15 | 43 | -0.004 | -0.006 | -0.002 | yes |
| 0.500 | 0.020 | 16 | 43 | 0.000 | 0.000 | 0.000 | yes |
| 1.000 | 0.020 | 1 | 43 | -0.356 | -0.379 | -0.334 | no |
| 1.000 | 0.020 | 2 | 43 | -0.243 | -0.264 | -0.222 | no |
| 1.000 | 0.020 | 3 | 43 | -0.202 | -0.221 | -0.182 | no |
| 1.000 | 0.020 | 4 | 43 | -0.143 | -0.158 | -0.130 | no |
| 1.000 | 0.020 | 5 | 43 | -0.116 | -0.130 | -0.103 | no |
| 1.000 | 0.020 | 6 | 43 | -0.061 | -0.071 | -0.051 | no |
| 1.000 | 0.020 | 7 | 43 | -0.041 | -0.049 | -0.033 | no |
| 1.000 | 0.020 | 8 | 43 | -0.035 | -0.042 | -0.028 | no |
| 1.000 | 0.020 | 9 | 43 | -0.033 | -0.040 | -0.027 | no |
| 1.000 | 0.020 | 10 | 43 | -0.026 | -0.032 | -0.021 | no |
| 1.000 | 0.020 | 11 | 43 | -0.021 | -0.025 | -0.017 | no |
| 1.000 | 0.020 | 12 | 43 | -0.014 | -0.017 | -0.011 | yes |
| 1.000 | 0.020 | 13 | 43 | -0.011 | -0.013 | -0.008 | yes |
| 1.000 | 0.020 | 14 | 43 | -0.006 | -0.008 | -0.004 | yes |
| 1.000 | 0.020 | 15 | 43 | -0.004 | -0.006 | -0.002 | yes |
| 1.000 | 0.020 | 16 | 43 | 0.000 | 0.000 | 0.000 | yes |

Prespecified k* result:

- M_XGB, λ=0, δ=0.02: smallest non-inferior k=12.
- M_XGB, λ=0.25, δ=0.02: smallest non-inferior k=12.
- M_XGB, λ=0.5, δ=0.02: smallest non-inferior k=12.
- M_XGB, λ=1, δ=0.02: smallest non-inferior k=12.

## Participant-level attribution upgrade (post hoc)

Each inner-held-out participant contributes one normalised electrode-attribution vector. The upgraded score uses the median minus lambda times MAD across these people, retaining outer-participant exclusion. This measures between-person heterogeneity more directly than pooling people into inner folds. The extension does not retrospectively replace H3.

| lambda | k* | k* Holm | participant minus fold at k=12 | LCB | UCB | Holm p |
| --- | --- | --- | --- | --- | --- | --- |
| 0.000 | 12 | 12 | 0.000 | 0.000 | 0.000 | 1.000 |
| 0.250 | 12 | 12 | 0.000 | 0.000 | 0.000 | 1.000 |
| 0.500 | 12 | 12 | 0.000 | 0.000 | 0.000 | 1.000 |
| 1.000 | 12 | 12 | 0.000 | 0.000 | 0.001 | 1.000 |

Across all 60 paired aggregation comparisons, 0 favoured the upgrade and 0 favoured the original aggregation after family-wide Holm adjustment.

The penalty gate compares every positive lambda with lambda zero within the upgraded aggregation. These are exploratory diagnostics with correction across the complete family:

| lambda | k | N | penalty minus magnitude | LCB | UCB | Holm p | benefit | harm |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.250 | 4 | 43 | 0.000 | 0.000 | 0.000 | 1.000 | no | no |
| 0.250 | 6 | 43 | 0.000 | 0.000 | 0.000 | 1.000 | no | no |
| 0.250 | 8 | 43 | 0.000 | -0.001 | 0.001 | 1.000 | no | no |
| 0.250 | 12 | 43 | 0.000 | 0.000 | 0.000 | 1.000 | no | no |
| 0.500 | 4 | 43 | 0.000 | 0.000 | 0.000 | 1.000 | no | no |
| 0.500 | 6 | 43 | 0.000 | 0.000 | 0.000 | 1.000 | no | no |
| 0.500 | 8 | 43 | 0.000 | -0.001 | 0.001 | 1.000 | no | no |
| 0.500 | 12 | 43 | 0.000 | 0.000 | 0.000 | 1.000 | no | no |
| 1.000 | 4 | 43 | 0.003 | 0.001 | 0.006 | 0.332 | no | no |
| 1.000 | 6 | 43 | 0.000 | 0.000 | 0.000 | 1.000 | no | no |
| 1.000 | 8 | 43 | 0.001 | -0.001 | 0.002 | 1.000 | no | no |
| 1.000 | 12 | 43 | 0.000 | 0.000 | 0.000 | 1.000 | no | no |

All candidates are retained. A null or harmful comparison is not converted into a positive result by changing the gate or choosing a candidate from outer-test scores.

## Selection baselines

The comparison used random-subset counts {'4': 100, '6': 100, '8': 100, '12': 500}. The frozen plan requested at least 100 per k and 500 at k*; the run was not capped and this status must remain visible in any manuscript claim.

| method | k | N | mean Macro-F1 | SD |
| --- | --- | --- | --- | --- |
| PERM | 4 | 43 | 0.385 | 0.070 |
| GEOM | 4 | 43 | 0.383 | 0.069 |
| SRCFA | 4 | 43 | 0.383 | 0.071 |
| SHAP_lam0 | 4 | 43 | 0.382 | 0.071 |
| RANDOM | 4 | 43 | 0.366 | 0.059 |
| MI | 4 | 43 | 0.280 | 0.049 |
| SHAP_lam0 | 6 | 43 | 0.453 | 0.080 |
| SRCFA | 6 | 43 | 0.453 | 0.080 |
| PERM | 6 | 43 | 0.440 | 0.080 |
| GEOM | 6 | 43 | 0.419 | 0.068 |
| RANDOM | 6 | 43 | 0.416 | 0.068 |
| MI | 6 | 43 | 0.360 | 0.066 |
| SRCFA | 8 | 43 | 0.469 | 0.081 |
| SHAP_lam0 | 8 | 43 | 0.468 | 0.081 |
| PERM | 8 | 43 | 0.466 | 0.080 |
| GEOM | 8 | 43 | 0.465 | 0.072 |
| RANDOM | 8 | 43 | 0.445 | 0.071 |
| MI | 8 | 43 | 0.396 | 0.068 |
| SHAP_lam0 | 12 | 43 | 0.485 | 0.079 |
| SRCFA | 12 | 43 | 0.485 | 0.079 |
| PERM | 12 | 43 | 0.485 | 0.079 |
| MI | 12 | 43 | 0.480 | 0.079 |
| GEOM | 12 | 43 | 0.478 | 0.076 |
| RANDOM | 12 | 43 | 0.478 | 0.077 |

## Stability, sessions, and faithfulness

Stability summary:

| group | pairs | Spearman ρ | Kendall τ | Jaccard@4 | Jaccard@6 | Jaccard@8 |
| --- | --- | --- | --- | --- | --- | --- |
| per_subject_STRONGEST | 903 | 0.927 | 0.801 | 0.752 | 0.905 | 0.803 |
| inner_folds_group_level | 430 | 0.948 | 0.840 | 0.816 | 0.992 | 0.838 |
| outer_folds_UPPER_BOUND | 903 | 0.987 | 0.943 | 0.888 | 1.000 | 0.923 |

Cross-session summary:

| design | train | test | matched | N | mean Macro-F1 | SD |
| --- | --- | --- | --- | --- | --- | --- |
| CS1 | 1 | 1 | yes | 43 | 0.492 | 0.101 |
| CS1 | 1 | 2 | no | 43 | 0.528 | 0.088 |
| CS1 | 1 | 3 | no | 43 | 0.510 | 0.090 |
| CS2 | 1+2 | 3 | no | 43 | 0.530 | 0.095 |

Faithfulness deletion summary:

| arm | kept | N | mean Macro-F1 | SD |
| --- | --- | --- | --- | --- |
| remove_top | 2 | 43 | 0.263 | 0.051 |
| remove_bottom | 2 | 43 | 0.292 | 0.060 |
| remove_top | 4 | 43 | 0.351 | 0.059 |
| remove_random | 4 | 43 | 0.366 | 0.059 |
| remove_bottom | 4 | 43 | 0.382 | 0.070 |
| remove_top | 6 | 43 | 0.376 | 0.063 |
| remove_random | 6 | 43 | 0.416 | 0.068 |
| remove_bottom | 6 | 43 | 0.454 | 0.080 |
| remove_top | 8 | 43 | 0.408 | 0.069 |
| remove_random | 8 | 43 | 0.445 | 0.071 |
| remove_bottom | 8 | 43 | 0.469 | 0.081 |
| remove_top | 10 | 43 | 0.445 | 0.077 |
| remove_bottom | 10 | 43 | 0.475 | 0.080 |
| remove_top | 12 | 43 | 0.455 | 0.076 |
| remove_random | 12 | 43 | 0.478 | 0.077 |
| remove_bottom | 12 | 43 | 0.485 | 0.079 |
| remove_top | 14 | 43 | 0.487 | 0.078 |
| remove_bottom | 14 | 43 | 0.491 | 0.080 |

## External and bipolar sensitivity analyses

NinaPro DB5 is a methodological replication only; its hardware, sampling rate, movement set, and feature units are not interchangeable with GRABMyo.

| DB5 k | N | mean Macro-F1 | SD |
| --- | --- | --- | --- |
| 1 | 10 | 0.105 | 0.021 |
| 2 | 10 | 0.138 | 0.021 |
| 3 | 10 | 0.162 | 0.029 |
| 4 | 10 | 0.180 | 0.026 |
| 5 | 10 | 0.200 | 0.042 |
| 6 | 10 | 0.231 | 0.058 |
| 7 | 10 | 0.232 | 0.070 |
| 8 | 10 | 0.252 | 0.068 |
| 9 | 10 | 0.260 | 0.076 |
| 10 | 10 | 0.265 | 0.079 |
| 11 | 10 | 0.260 | 0.084 |
| 12 | 10 | 0.268 | 0.092 |
| 13 | 10 | 0.266 | 0.088 |
| 14 | 10 | 0.269 | 0.097 |
| 15 | 10 | 0.270 | 0.096 |
| 16 | 10 | 0.281 | 0.099 |

Bipolar sensitivity (F_j − F_{j+8}):

| λ | bipolar k | N | mean Macro-F1 | SD |
| --- | --- | --- | --- | --- |
| 0.000 | 1 | 43 | 0.174 | 0.044 |
| 0.000 | 2 | 43 | 0.240 | 0.049 |
| 0.000 | 3 | 43 | 0.310 | 0.070 |
| 0.000 | 4 | 43 | 0.356 | 0.080 |
| 0.000 | 5 | 43 | 0.405 | 0.085 |
| 0.000 | 6 | 43 | 0.442 | 0.086 |
| 0.000 | 7 | 43 | 0.464 | 0.085 |
| 0.000 | 8 | 43 | 0.480 | 0.089 |
| 0.250 | 1 | 43 | 0.174 | 0.044 |
| 0.250 | 2 | 43 | 0.240 | 0.049 |
| 0.250 | 3 | 43 | 0.310 | 0.072 |
| 0.250 | 4 | 43 | 0.356 | 0.080 |
| 0.250 | 5 | 43 | 0.405 | 0.085 |
| 0.250 | 6 | 43 | 0.442 | 0.086 |
| 0.250 | 7 | 43 | 0.464 | 0.085 |
| 0.250 | 8 | 43 | 0.480 | 0.089 |
| 0.500 | 1 | 43 | 0.174 | 0.044 |
| 0.500 | 2 | 43 | 0.240 | 0.049 |
| 0.500 | 3 | 43 | 0.312 | 0.072 |
| 0.500 | 4 | 43 | 0.356 | 0.080 |
| 0.500 | 5 | 43 | 0.406 | 0.085 |
| 0.500 | 6 | 43 | 0.442 | 0.086 |
| 0.500 | 7 | 43 | 0.464 | 0.085 |
| 0.500 | 8 | 43 | 0.480 | 0.089 |
| 1.000 | 1 | 43 | 0.174 | 0.044 |
| 1.000 | 2 | 43 | 0.240 | 0.049 |
| 1.000 | 3 | 43 | 0.313 | 0.073 |
| 1.000 | 4 | 43 | 0.356 | 0.080 |
| 1.000 | 5 | 43 | 0.406 | 0.085 |
| 1.000 | 6 | 43 | 0.442 | 0.086 |
| 1.000 | 7 | 43 | 0.464 | 0.085 |
| 1.000 | 8 | 43 | 0.480 | 0.089 |

## Literature status

The current literature matrix contains 93 screened entries. This matrix is a scoping resource with flagged registry mismatches, not a systematic review.

## Reproducibility and limitations

- The strict result gate is `scripts/16_verify_results.py`; it must pass before numeric manuscript macros are generated.
- The 1D CNN/integrated-gradients phase is conditional in the frozen execution plan and is not represented as evidence unless its own artifacts exist.
- Window-length sensitivity and the rest-inclusive task were not run; neither contributes evidence to the manuscript.
- Ethics remains unresolved at the author's request. Funding, contributions, conflicts and the permanent archive identifier still require author confirmation.
- Random-baseline capping, if present above, is a declared deviation rather than silently reported as full frozen-plan coverage.
- mRMR is not included in the executed baseline set because the current pipeline does not contain a validated implementation; it is therefore reported as omitted, not as a null result.
- Source artifacts: `artifacts/statistics/`, `artifacts/metrics/`, `artifacts/rankings/`, `artifacts/selection_baselines/`, `artifacts/stability/`, `artifacts/cross_session/`, `artifacts/faithfulness/`, `artifacts/db5/`, `artifacts/bipolar/`, and `artifacts/participant_attribution/`.
