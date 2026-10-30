# Whole-study results review and Figure 1 rebuild

Date: 2026-10-29. Project: `E:\grabmyo_data`.

The current numerical record supports a retrospective, participant-disjoint model evaluation in which twelve GRABMyo monopolar electrodes meet a specified **mean** Macro-F1 loss tolerance of 0.02. This is not a guarantee for every participant, an independently validated common physical layout, or a prospective evaluation with untouched development decisions. The supplied new Figure 1 also needs factual corrections before submission.

## Recompiled manuscript

- [Current article](../../publication/Main_article.pdf): 12 pages, including the supplied updated Figure 1.
- [Current supplement](../../publication/Supplementary_material.pdf): 13 pages.
- [Editable source](../../publication/LaTeX_source/main.tex) and [PDF figure dependencies](../../publication/figures/vector/).
- [Pre-recompile files](Before_recompile/) preserve the previous browsing copies. The dated scientific and publication releases remain unchanged.

The updated artwork was identified by its content, Canva metadata and 2026-10-29 timestamp, then copied byte-for-byte from `figures/PDF/fig1_montage.pdf` into the manuscript's expected relative figure directory. Only surrounding whitespace is cropped by LaTeX. The caption now describes panels A-C, identifies the documented montage, distinguishes schematic anatomy from muscle registration, and avoids presenting stability regularization as a demonstrated improvement. Bibliography spacing was adjusted to avoid an almost empty thirteenth article page. No manuscript metric was edited.

The local TeX Live build completed with BibTeX and repeated LaTeX passes. Final logs contain no undefined references/citations, multiply defined references, or overflowing horizontal/vertical boxes. The class emits harmless font-size substitution warnings. All final pages were inspected for layout; Figure 1 and the final bibliography page were also inspected at full-page resolution. The built-in app compiler timed out while downloading its initial TeX dependencies; the delivered PDFs were successfully built and verified using the installed TeX Live compiler.

## Verification performed

| Check | Fresh evidence |
| --- | --- |
| Required publication gate | `scripts/16_verify_results.py --revision-dir manuscript_revision/20261014`: **PASS, 4,593 checks**, executed on an isolated byte-identical copy of the analysis code and inputs |
| Independent statistical calculation | **606** count/margin rows and **42** minimum-count rows across **14** conditions reproduced, including percentile intervals, null-centred studentized bootstrap, Holm adjustments and decision flags |
| Current manuscript numbers | All **453** historical macros and **46** revision macros match fresh gate-generated values, allowing the documented Seed-to-MonteCarlo identifier changes |
| Repository tests | **53 passed** |
| Prediction and scaling checks | Gate reconstructs saved baseline and primary/RF prediction metrics, held-out row alignment, primary training/scaler fingerprints, participant exclusion ledgers, matched inner splits and selected subsets |
| Secondary statistical tables | Gate reconstructs all **15** original primary/secondary tables and compares full numeric content and decision flags |
| Raw-data integrity | **PASS**: all **30,715** published GRABMyo checksum entries, **10** official DB5 archives and **30** extracted exercise files freshly checked; zero missing files or checksum mismatches |

The gate regenerated statistics, macros and result-driven figures in `E:\Temp\codex-chatgpt\grabmyo_review_20261029`, so it did not overwrite a frozen release or replace the new author Figure 1 with the older generated montage. The isolated scientific gate validates the original result-driven figure inputs. Its PASS does **not** certify the factual labels in the new author artwork.

Reproducible independent calculations and full-precision outputs are retained in [independent_statistics_review.py](independent_statistics_review.py), [independent_statistics_verification.json](independent_statistics_verification.json), [independently_recomputed_noninferiority.csv](independently_recomputed_noninferiority.csv), and [independently_recomputed_minimum_counts.csv](independently_recomputed_minimum_counts.csv). Full gate checks are in [scientific_gate_verification.json](scientific_gate_verification.json); the execution log is [strict_revision_verification.log](strict_revision_verification.log).

## Results and their interpretation

| Analysis | Rechecked result | Interpretation |
| --- | --- | --- |
| Primary GRABMyo curve, n=43 | Full16 mean **0.541313**; SHAP12 mean **0.528009**; paired change **-0.013304**, 95% CI **[-0.016041, -0.010598]** | Meets the 0.02 mean-loss criterion; twelve is the smallest qualifying count |
| Tolerance sensitivity | Minimum counts **14**, **12**, **11** at margins **0.01**, **0.02**, **0.03**; primary null-centred Holm sensitivity agrees | The chosen engineering tolerance materially determines the count |
| Participant losses | **42/43** declined; **11/43** lost more than 0.02; worst change **-0.036071**, participant 27 | Mean non-inferiority does not establish individual preservation |
| Gesture losses | Four corrected declines: gestures **2, 9, 10, 14** | Task-specific degradation remains despite the aggregate mean decision |
| Primary geometry comparator | Geometry12 change **-0.019347**, CI **[-0.025365, -0.013199]**; SHAP12-minus-geometry12 **+0.006043**, CI **[-0.001019, +0.012737]**; complete geometric curve minimum **15** | Geometry12 fails the mean criterion, but the direct mean superiority of SHAP12 is uncertain; one method passing while another fails is not itself a method-difference test |
| Mean-random comparison | Attribution exceeds mean random subsets at all four sampled counts under the lighter classifier | Supported within that protocol; selection resources and validation designs were not shared across all legacy comparators |
| Shared-resource grouped permutation | SHAP minus permutation at six electrodes **+0.030931**, CI **[+0.021063, +0.041032]**, Holm p **0.00000608**; at twelve **+0.000240**, CI **[-0.002925, +0.003413]**, p **0.976168** | Positive six-electrode contrast; no established twelve-electrode advantage. This does not make six electrodes non-inferior to full16 |
| Stability regularization | No corrected beneficial or harmful person-level penalty contrast among twelve tests; positive person-level penalties at count twelve retain the same physical set in all outer folds | No established improvement; some zero contrasts reflect unchanged inputs |
| Two split-derived fixed layouts | Odd-development/even-test qualifies; reverse split lower bound **-0.020020** misses the boundary and qualifies in **90/200** bootstrap-seed diagnostics | Different layouts and a numerically fragile boundary; not independent prospective validation or a probability that non-inferiority is true |
| Rest, 150 ms, 500 ms, RF | Twelve-electrode changes approximately **-0.0139**, **-0.0119**, **-0.0126**, **-0.007837**; each meets 0.02 within its condition | Rankings were reused. RF evaluated only counts twelve and sixteen, so no RF minimum count is estimated |
| NinaPro DB5, n=10 | Count-twelve change **-0.012571**, percentile lower bound about **-0.019994**; no corrected reduced count at 0.02 | Very near the unadjusted boundary; does not independently confirm the GRABMyo count |
| Derived bipolar, n=43 | Seven-minus-eight change **-0.015802**, CI approximately **[-0.0203, -0.0113]** | Does not support removing one of eight derived pairs at the primary margin; not equivalent to validating fewer physical bipolar sensors |
| Deletion with retraining | Retain-six Remove-Top minus Remove-Bottom approximately **-0.0775**, CI **[-0.0921, -0.0627]**, corrected p<0.001 | Supports predictive ranking relevance, not causal muscle identification |
| Cross-session | Full-array means approximately **0.492**, **0.528**, **0.510**, **0.530** for the four retained session conditions | Does not establish reduced-layout robustness to placement displacement |

Primary sources are the current `manuscript_revision/20261014/tables/` and `experiments/statistics/` files, together with `artifacts/statistics/`, `artifacts/cross_session/`, `artifacts/bipolar/`, and `artifacts/db5/`. Full-precision source fingerprints for the independently reconstructed primary/count results are recorded in `independent_statistics_verification.json`. No result values were estimated from plots.

## Completeness and leakage review

The previously missing bipolar summary and incomplete participant extension are resolved in this checkout. Primary and fresh participant-extension curves each have 2,752 unique cells (43 participants x 4 penalties x 16 counts). Bipolar has 1,376 (43 x 4 x 8); DB5 has 160 (10 x 16). Rest-inclusive, 150 ms, 500 ms and geometric curves each have 688 (43 x 16). These grids are complete, duplicate-free and finite. The fresh revision extension has current source hashes; the old extension's historical hash mismatch remains preserved separately.

Active ranking and fitting code excludes the outer participant before inner grouped splitting, uses inner-training-only scalers, and attributes inner-held-out participants. Primary sparse evaluation excludes the test participant before sampling/scaling. The shared-resource comparator also checks participant exclusion and permutes jointly within participants. No new outer-participant inclusion was identified in these active fitting paths.

Two disclosed development exposures prevent a claim of strict untouched-test evaluation: count-feature threshold calibration pooled recordings before partitioning, and model-budget calibration used outer outcomes for participants 1 and 7. Rounded threshold invariance is useful robustness evidence but does not retroactively make calibration fold-local. These exposures conflict with the repository's absolute prohibition on using outer-test participants for development/tuning. They are not resolved by the numerical gate, and the current evidence cannot be called fully compliant with that absolute rule. A defensible retrospective interpretation preserves the disclosures; a fully untouched evaluation requires separately locked development decisions and new validation.

Participant resampling respects the correct unit, but overlapping LOSO training sets and fixed fitted models make intervals conditional. The exploratory null-centred sensitivity does not remove training-set dependence or development exposure. The analysis was not independently preregistered; secondary families, full geometric curves and selector-activity diagnostics remain post-hoc/exploratory.

For auditability, primary and RF revision predictions are saved and reconstructible. Some other new fits retain metrics without saved final predictions: **79** shared-budget fits and **602** geometric fits. Their subsets, source fingerprints, reuse rows and aggregate statistical results can be checked, but every new score cannot be independently reconstructed from a saved prediction vector. This is a reproducibility limitation, not evidence that the metrics were fabricated.

## Corrections required before submission

1. **Figure 1 topology:** the supplied artwork labels F9-F16 as proximal and F1-F8 as distal. The dataset's `Electrodelocation.pdf` and the analysis topology identify F1-F8 as proximal and F9-F16 as distal. Correct the artwork rather than relying on the caption to contradict it.
2. **Figure 1 distance:** the artwork includes a 3 cm inter-ring annotation; the documented montage and geometry use 2 cm. The nominal 24 cm circumference is a geometry assumption, not a measured circumference for every participant. Anatomical illustrations do not establish individual muscle registration.
3. **Figure 1 stability wording:** labels such as "Reliable" and "Stable Channel Ranking" must be presented as the candidate procedure, not an observed benefit. Current corrected tests do not establish improved recognition from regularization.
4. **Development independence:** retain the pooled-threshold and outer-outcome budget disclosures. Do not describe the complete study as strictly free of development exposure or as prospectively validated.
5. **Author declarations:** institutional determination, funding, conflicts, CRediT/authorship approval and a permanent public archive remain unresolved in [author materials](../Author_materials/author_declarations.md). Their omission from the clean reader PDF does not resolve them.

No independent new cohort, online control, causal preprocessing latency, hardware energy/cost reduction, or clinical benefit was measured. The present findings should remain scoped to this offline reduction procedure.

[Back to project guide](../../README.md)
