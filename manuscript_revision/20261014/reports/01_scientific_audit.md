# Scientific audit - before new revision experiments

Date: 2026-10-14. Locations refer to the preserved current LaTeX sources. Evidence status: source/artifact inspection; new numerical validation is pending.

| Severity | Exact location and current decision | Problem and validity consequence | Correction and required work |
|---|---|---|---|
| Critical | Discussion, paragraph beginning “This pattern suggests”; geometric layout was not tested for non-inferiority | The paper cannot assess the incremental selection value at the supported count from a lighter-model superiority comparison. | Fit deterministic geometric12 under primary training and reference budgets; new computation A. |
| Major | Results, first subsection; supplementary per-gesture table gives full-data baseline only | A global mean loss can hide gesture-specific loss; full-data baseline predictions cannot be paired with a 200k reduced model. | Save matched 200k full16 and SHAP12 predictions; participant-paired gesture effects and confusion changes; computation B. |
| Major | H1 result and conclusion; only mean paired loss is discussed | Population-average non-inferiority gives no individual guarantee. | Report all participant differences, quantiles, losses over margin and worst observed loss; computation C. |
| Major | Methods, secondary method comparison: SHAP inner models 300 trees/200k versus permutation model 20k and 50-tree final comparator | Ranking quality and resource allocation are confounded; final evaluation budgets alone do not equalise selection cost. | Shared inner-model and held-out-observation comparison, recorded compute cost, common final model; exploratory computation D. |
| Major | Methods NI paragraph: fraction of uncentred bootstrap means below the margin called a null-hypothesis p-value | Percentile-tail inversion is not an explicitly sampled null distribution. Holm inference needs its approximation explained and independently checked. | Preserve original decision; audit a null-centred studentised paired bootstrap sensitivity, and label the original tail calculation precisely; computation. |
| Major | SAP header says “committed 2026-08-12”; Git has no commits | A dated file and narrative are not independently authenticated preregistration. | Document provenance and dated logs; qualify chronology and use a title without a claim of prospective registration; rewriting and record audit. |
| Major | Methods, “all preprocessing statistics” derive exclusively from remaining participants | Count-feature thresholds were pooled historically, then verified post hoc. The unrestricted exclusion claim contradicts the threshold subsection. | Restrict the claim to fold-specific standardisation, fitting and ranking; retain pooled-threshold history and reproduce its invariance checks. |
| Major | Supplement S1 item 12 and Discussion: window and Rest analyses “not run” | Rest17 is complete; w500 has 42 participants; current reporting is stale. | Verify completed data, finish missing fold, perform bounded w150 check, update evidence classification and counts. |
| Major | Figure 1 caption: proximal F1-F8 and distal F9-F16 | The available source documentation must support ring orientation; otherwise the illustration overstates anatomy. | Inspect original montage diagrams; label ring1/ring2 and aligned indices if orientation is unverified; figure rebuild. |
| Major | Supplement S4 and Discussion fixed-layout wording | Two split directions yield distinct dropped sets and distinct NI decisions; neither is independent count validation after cohort-wide selection. | Preserve both layouts, split sizes and opposite decisions, explicitly disclose count-selection exposure. No prospective claim. |
| Moderate | Discussion, “probably a lower bound” for SVM | Increased training on one calibration fold does not establish a general lower bound. | Call it a budget-limited baseline; distinguish observed single-fold calibration from unproved optimum; rewriting. |
| Moderate | Attribution variability and stability statements | Inner-fold pooling suppresses person heterogeneity; shared fitted models and overlapping outer cohorts preclude independent-replicate interpretations. | Retain verified person aggregation as post hoc, report negative penalty findings and overlap limitation; artifact validation and rewriting. |
| Moderate | Current eight main figures and supplementary placement | Classifier context occupies main space while participant and gesture loss have no principal visual. | Six evidence-focused figures, move classifier, extended stability and session diagnostics to Supplementary; code and visual QA. |
| Major | Funding, contributions, conflict, permanent archive and secondary ethics placeholders | Author-only facts remain unavailable. | Keep visible, list explicitly; ethics remains unresolved per existing authorization. |

Supported contributions to validate: a participant-disjoint reduction procedure evaluated at a predefined engineering tolerance; attribution utility relative to random and spatial coverage; boundaries revealed by stability, session, task, window, split and sensor representation. No novel stability algorithm or universal fixed physical layout is established.

## Montage issue resolved by source inspection

The original `Electrodelocation.pdf`, page1, explicitly places ring1 (electrodes1-8) proximal to ring2 (9-16), with2cm longitudinal separation. The caption orientation is supported by this document. The revision will retain documented numbering and orientation, use a clearly schematic forearm without muscle-registration claims, and include an unwrapped topology. The initial concern above is resolved rather than treated as an established error.

## Dataset identity and current integrity resolved

The source PLOS data-availability paragraph transposes the DB4/DB5 archive identifiers. The official Zenodo records identify1000116 as DB5 (double Myo) and1000138 as DB4 (Cometa). The actual downloaded study archives use the correct1000116 record. Current full checksum verification passed for allGRABMyo files, allten DB5 archives and allthirty extracted exercise files. The reproduction link is corrected, and live official JSON records and per-file digests are preserved. No dataset was substituted and no experimental metric changed.


## Earlier invalid package and source separation

The repository preserves a2026-08-12 integrity finding concerning a preliminary delivery with hardcoded fallback metrics and missing experiments. That package remains quarantined under `_archive_invalid/`. It is distinct from the later September sources used here. The revision does not reuse its invented headline values; current inputs are fingerprinted real-data result files, with canonical saved predictions and hard failures for missing evidence. The historical finding is preserved in `original/reports/INTEGRITY_FINDING_fabricated_results.md` rather than erased. Final computational acceptance still requires the current revision verification gate and visual inspection.


## DB5 implemented cutoff correction

A further source audit found that scripts/33_db5_features.py requests10-95Hz, but the shared band-pass function caps the upper limit at0.45*fs-1=89Hz. Script84 reconstructed every saved DB5 feature row from allten raw E1 files and matched all21089 rows exactly, including labels and direct10-89Hz filtering. The old report printed the requested setting rather than the implemented setting. Methods and Supplementary now state the effective10-89Hz band and preserve the requested95Hz history. No filter, feature file or experimental metric was changed. scripts/16_verify_results.py's revision route repeats this full reconstruction and verifies its source fingerprints. Filter order is clarified as SciPy design argument4/eight poles per pass; exact feature definitions, Welch settings and representation-specific thresholds are added to Supplementary.

The misleading script33 header and report-output string are now corrected for future reruns, while its requested filter argument and all feature computations remain unchanged. Original source/report and the pre-correction audit fingerprint are retained under original/.


## Historical permutation validation clarified

Source27 derives permutation importance using a window split within outer-training participants:20k fitted windows,8k other validation windows, and scaling from the40k ranking pool before that split. It is not participant-disjoint inner validation, and its scaler includes the internal validation windows. The outer test participant remains excluded, so this is a difference in selection-stage validation design rather than outer-test contamination. The completed shared-model comparison instead uses common participant-disjoint inner models, training-only scalers and exact shared validation observations. The manuscript now discloses all of these changes and does not attribute historical differences solely to resource budget. The historical results and fingerprinted source27 are preserved. Every deletion subset also matches the unpenalized ordering; its random references match the P4 mean-random baseline and its model parameters/budget match that protocol.

## Resolution after complete experimental verification

The dated revision gate passed4593 checks after every queued participant experiment completed. Primary full16/SHAP12 predictions reproduced original metrics, complete task/window/RF and geometric results were verified, all15 historical statistical tables were reconstructed, and the current-provenance participant extension passed without rewriting the old failed source hash. The original audit table remains as the contemporaneous issue record.

- Geometry: the full fixed ordering qualifies first at15 at0.02 under both percentile and null-centred Holm rules. This is one ordering; the direct SHAP12-minus-geometry12 mean interval still crosses zero.
- Fairer attribution comparison: shared-resource SHAP has a positive mean advantage over grouped permutation at6; the12-site advantage is uncertain. Changes in grouping, validation, scaling and resources remain confounded.
- Penalty extension: no corrected beneficial penalty contrast. All participant-level penalties at12 select identical physical sets in all43 folds; this explains input identity, not equivalence of different layouts.
- Generalization: individual and gesture losses, both split layouts, DB5 test-construction sensitivity, derived bipolar limitations and lack of a new same-montage cohort are retained.
- Communication: six main and seven supplementary vector figures, native sources, full-precision tables and provenance are generated from checked files. Final page inspection and author-input qualifications are documented in report08; a compiled file alone is not visual acceptance.
