# Reviewer #2 audit — current study review (2026-09-22)

Adversarial review of `manuscript/main_iop.tex` and the current result graph. Final PDF clearance is recorded separately in `reports/completion_gate.json`. Each point states
the objection, whether it holds, and what was done. "Open" items are disclosed in the paper and
not fixable without new data or compute.

## A. Validity of the headline claim (k* = 12)

| # | Objection | Verdict | Action |
|---|---|---|---|
| A1 | k* is the minimum over 15 tested k; multiplicity inflates false non-inferiority. | Holds in general, not here. All k from 15 down to 12 pass, so a fixed-sequence procedure (FWER-controlling without adjustment) gives the same k*. | Stated in Results. The same argument shows DB5 has no k* under fixed-sequence testing, which is also stated. |
| A2 | The k = 16 reference of the curve (200k windows) is not the P1 full-data model; mixing them would bias Δ. | Valid concern, avoided. | All Δ_k use the k = 16 model of the same curve (identical budget); stated in Methods, Results and the Table 2 caption. |
| A3 | Margin 0.02 is arbitrary. | Holds; it is an engineering tolerance. | Frozen before results (plan sha256 734f889a…); labelled as not clinical; sensitivity margins reported (k* = 14 / 11). |
| A4 | Non-inferiority does not mean no loss. | Holds. | Results say every Δ_k < 0 and that the claim is non-inferiority, not equivalence. |
| A5 | Ranking and training use the same outer-training participants: is the ranking overfitted? | Partly. The ranking never sees the test participant, which is what the LOSO estimate needs. | Cross-fitting confines attribution to inner-held-out participants; leakage assertions each fold; 47 unit tests pass, including a planted-signal canary. |
| A6 | Count-feature threshold computed from pooled data (including test participants). | Holds, minor: one label-free scalar. | Disclosed in Methods and Limitations. |

## B. Attribution claims

| # | Objection | Verdict | Action |
|---|---|---|---|
| B1 | "SR-CFA" is presented as the method, but λ was never selected. | Held against the previous draft. | No λ selected; all four reported; H3 null reported; the paper says the supported method is plain cross-fitted SHAP magnitude (Decision 13). |
| B2 | The stability penalty resembles published robust-SHAP scores. | Holds. | RoSHAP preprint cited as closely related; the penalty is not claimed as novel. |
| B3 | Beating random subsets is a weak baseline. | Holds. | Geometric and permutation baselines reported: attribution matches them at most k. Stated in the abstract and Discussion. |
| B4 | The faithfulness test compared arms trained differently. | Held against the 2026-08-15 run. | Recomputed under one protocol (Decision 11); the protocol check is reported with its residual numerical difference (mean 0.0014). |
| B5 | Channel-to-muscle labels are unsupported. | Held against the previous draft (it named muscles with fabricated frequencies). | Removed. The Discussion explicitly declines anatomical mapping. |
| B6 | H2–H4 test families were specified after results. | Holds. | Listed as a deviation; the families are the natural ones (all k where the data exist). |

## C. Baselines and compute

| # | Objection | Verdict | Action |
|---|---|---|---|
| C1 | The SVM was trained on 40k windows; it may be the best model. | Possible. | Calibration (0.555 → 0.591 from 20k to 40k on one fold) reported; SVM stated as a lower bound; the SVM–XGB difference is not significant. |
| C2 | H2/H4 use a 50-tree comparison model. | Holds. | Stated in Methods, table captions and Limitations; the absolute values are never compared with the headline curve. |
| C3 | No deep-learning model. | Holds. | The plan listed cross-model attribution as exploratory; not run; disclosed. |

## D. Exploratory analyses

| # | Objection | Verdict | Action |
|---|---|---|---|
| D1 | Cross-session "gain" confounds session diversity with twice the data. | Holds. | Stated in Methods, Results and Discussion. |
| D2 | Later sessions scored higher than the training session; this contradicts electrode-shift literature. | Not a contradiction: all conditions are cross-subject, so session effects sit on top of the cross-user gap. | Stated. No claim that electrode shift is harmless. |
| D3 | DB5 "replication" is underpowered and borderline. | Holds. | Reported as fragile: LCB on the margin, 95.5% of bootstrap seeds, neighbouring k fail, no k* under fixed-sequence testing. |
| D4 | The fixed layout is a single post-hoc split. | Holds. | Labelled post hoc; reported only as a consistency check; kept out of the abstract. |
| D5 | Exploratory results promoted into the abstract. | Held against the previous draft. | The abstract separates the original analyses from the post-hoc participant-level upgrade and exploratory geometric comparison. |

## E. Reporting integrity

| # | Check | Result |
|---|---|---|
| E1 | Every number in the text comes from a macro generated from an artifact | `scripts/45_check_manuscript_numbers.py`; allowed literals are design constants only |
| E2 | Tables generated from artifacts | `scripts/42_generate_tables.py` |
| E3 | Figures drawn from artifacts with the statistics' bootstrap | `scripts/44_figures.py` |
| E4 | Every reference resolves to the cited work | 38 entries freshly checked against Crossref/arXiv/DataCite records (`scripts/build_verified_bib.py`); 14 of 30 previous citations had non-existent or wrong DOIs and were fixed or removed |
| E5 | Cohort completeness | Current strict gate checks exact participant-by-condition grids; corrected bipolar completion is required before the final build. |

## Open (disclosed, not fixable here)
- Single primary dataset of able-bodied participants; offline evaluation only.
- Monopolar selection unit; the bipolar analysis is partial evidence about deployable sensors.
- Window-length sensitivity, the 17-class task and cross-model attribution were not run.

## Upgrade audit

The participant-level aggregation extension is complete and passes `verify_extension()` in `scripts/16_verify_results.py`. It reconstructs the scores and ranks, checks all outer exclusions, verifies all reused fits against their source, and checks the input fingerprints. No corrected penalty benefit was established. The original negative H3 result remains intact. Detailed results are in `artifacts/participant_attribution/`; this extension is post hoc and does not create a fresh validation cohort.

Historical training-budget calibration used held-out outcomes. The current fitting pipeline excludes each outer participant, but that does not erase development contamination. The fixed-layout count was also chosen from a full-cohort curve, so its test split is not an independent validation of that count.
