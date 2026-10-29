# Final quality control

This is a completed computational and editorial peer-review draft. It is not an author-approved submission or independent prospective device validation. Ethics, funding, contributions, conflicts and public archive information remain explicitly unresolved or deferred.

| Criterion | Requirement | Decision | Evidence |
|---|---|---|---|
| 1 | Novelty bounded by verified primary literature | Qualified pass | 02_novelty_and_literature.md; comparative_matrix.csv; unknown full-method fields explicit |
| 2 | Primary NI independently audited | Pass | verification.json; primary_matched_noninferiority.csv; noninferiority_audit.csv |
| 3 | Outer and inner participant exclusion | Qualified pass | Fold fitting/scaling/ranking exclusion verified; historical pooled threshold and test-fold budget development remain disclosed |
| 4 | Original versus added analyses distinguished | Pass | Methods; Supplementary chronology; exploratory protocol and eight amendments |
| 5 | Incremental attribution value critically tested | Pass | Primary geometry contrast; shared-model comparison; random and deletion results |
| 6 | Negative findings retained | Pass | Penalty gate, participant/gesture losses, geometry mean uncertainty and split-layout boundary |
| 7 | Twelve-electrode statement has mean/protocol scope | Pass | Main Results and Conclusion; no individual preservation claim |
| 8 | Fixed-layout claim bounded by available evidence | Qualified pass | Two distinct layouts; count-development exposure; no fresh independent same-montage cohort |
| 9 | Figures generated from experimental files | Pass | figure_provenance.csv; source_data; six main and seven supplementary vector figures |
| 10 | Numerical consistency verified | Pass | scripts/16_verify_results.py --revision-dir manuscript_revision/20261014; macro provenance |
| 11 | Coherent manuscript argument and legible layout | Pass after recorded inspection | visual_acceptance.json; all PDF pages inspected; abstract word-count audit |
| 12 | Unresolved declarations and missing evidence explicit | Qualified pass | unresolved_author_inputs.md; author deferred declarations; ethics remains unresolved |
| 13 | Reproduction materials and source traceability | Pass | source_manifest.csv; requirements_current.txt; verified_inputs; package_manifest.csv |
| 14 | Substantive external peer-review draft | Qualified pass | Computational/editorial review complete; submission still requires author declarations and decisions |

## Executed acceptance

The current revision gate passed 4593 recorded checks. The abstract contains 216 words (limit250).

.....................................................                    [100%]
53 passed in 2.81s

## Rendered-page acceptance

- main.pdf: 13 of 13 pages inspected; SHA256 `8288e78691402f88493b377cf44eefa40094430be5e94018cea606d55b9c6306`; 6 explicit author-input markers.
- supplementary.pdf: 14 of 14 pages inspected; SHA256 `4c3d78a6543ea025685001da0392726abe967d7cf4f846143ca07bd4593a601a`; 0 explicit author-input markers.

Inspection covers figures, axis/legend text, table scaling, captions, page breaks, references and visible placeholders. The per-page record identifies the inspected PDF fingerprint. The original source-hash failure remains preserved; it is not relabeled a successful historical verification. The current revision route checks the fresh isolated extension. A negative scientific penalty result is distinct from a failed computational provenance gate.

## Final files

Native sources are manuscript/main.tex, manuscript/supplementary.tex and their local sections/generated/tables/bibliography/class files. Reports01-08, full-precision outputs, vector figures, prediction files, protocols and executable source snapshots accompany them. Raw data are not redistributed in this package.
