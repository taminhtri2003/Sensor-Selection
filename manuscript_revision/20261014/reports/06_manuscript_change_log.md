# Manuscript change log

The original September manuscript tree and reports are preserved under original/. This native revision is a separate dated package; original primary result files and the frozen analysis plan are unchanged.

| Location | Before | Revision and scientific reason |
|---|---|---|
| Title | Whole study described as prespecified | Emphasizes participant-independent attribution and NI; internally dated plan and development exposures are disclosed rather than claimed as externally registered |
| Introduction | Broad channel reduction, no closest EMG SHAP comparator | Six paragraphs distinguish established selection/XAI work, leakage-controlled evaluation and mean tolerance; Rani, Wang and Gehlot added with verified metadata |
| Methods | Broad preprocessing exclusion and softmax description | Seven subsections; specifies soft-probability/argmax, fold scaling, historical pooled threshold, budget exposures and protocol-specific references |
| Statistics | Unshifted percentile tail described as a null test | Original calculation retained and labeled; exploratory null-centred studentized bootstrap, exact families, rank/mean estimand distinction and overlapping-model uncertainty added |
| Results1 | Aggregate minimum count without individual losses | Mean NI and full participant distribution reported together; tighter/looser margins retained |
| Results2 | Geometry comparison only with lighter model | Primary-protocol geometry12 added; uncertain direct mean contrast distinguished from differing NI decisions; shared-resource SHAP/group permutation and measured costs added |
| Results3 | Attribution maps and deletion without matched gesture predictions | Participant-level per-gesture degradation and confusion change added using primary saved predictions and numeric MotionSequence labels; no muscle explanation inferred |
| Results4 | Stale sensitivity completion and a common-layout implication | Complete rest/window and fixed-count classifier sensitivity; two distinct split-derived layouts and opposite decisions retained; no independent count validation claimed |
| Stability extension | Historical source-hash mismatch | Preserved old failure; isolated current refit and complete input checks; all fixed penalties disclosed, none selected from test outcomes |
| Figures | Eight main plots and broad illustrative anatomy | Six main figures with distinct evidence purposes, documented montage without muscles, separate model budgets and individual/gesture loss; classifier context moved to supplement |
| Supplementary | Older departures, limited sensitivity coverage | Updated methods, completed sensitivity curves, new prediction/resource/NI/person-extension tables and full-precision source files |
| Administrative text | Unresolved placeholders | Ethics remains explicitly unresolved as requested; funding, roles, conflict and archive DOI require author input and are not invented |

The abstract is structured and limited to the journal's250-word requirement. The compiled PDF and visual checks are documented in final QC, rather than inferred from the presence of editable text. Numerical facts are regenerated from result files through the revision route of scripts/16_verify_results.py.


## DB5 implemented cutoff correction

A further source audit found that scripts/33_db5_features.py requests10-95Hz, but the shared band-pass function caps the upper limit at0.45*fs-1=89Hz. Script84 reconstructed every saved DB5 feature row from allten raw E1 files and matched all21089 rows exactly, including labels and direct10-89Hz filtering. The old report printed the requested setting rather than the implemented setting. Methods and Supplementary now state the effective10-89Hz band and preserve the requested95Hz history. No filter, feature file or experimental metric was changed. scripts/16_verify_results.py's revision route repeats this full reconstruction and verifies its source fingerprints. Filter order is clarified as SciPy design argument4/eight poles per pass; exact feature definitions, Welch settings and representation-specific thresholds are added to Supplementary.

The misleading script33 header and report-output string are now corrected for future reruns, while its requested filter argument and all feature computations remain unchanged. Original source/report and the pre-correction audit fingerprint are retained under original/.

The post-hoc amendment08 selector-activity audit found that allthree participant-level penalties leave count12 physical site sets unchanged in all43 outer folds, yielding identical fixed-protocol scores there. This explains the degenerate operating-point comparison; it is not evidence that different layouts are equivalent. Allcounts and both aggregation rules are retained in selection_change_audit.csv.

The completed-analysis layout proof caught and corrected two unescaped filename underscores. Float placement and widow control reduce unnecessary main-text float pages. A final literature check added Simon et al. (2024) to delimit offline reduction from online prosthesis control; complete publisher methods and Crossref metadata were verified, without importing its outcomes as this study data.

After all43 geometric folds and the4593-check revision gate passed, the full primary-protocol geometric count curve was integrated into Methods, Results, Discussion, Supplementary figureS7 and its generated decision table. Its primary-margin minimum15 is reported alongside SHAP12 without converting differing NI decisions into a direct superiority test. The original fixed ordering, seed and margin were retained.

The final documented test command, python -m pytest tests -q, passed all53 tests. An earlier unscoped invocation after code archiving recursively collected both repository and archived test modules and stopped with duplicate-module collection errors; that diagnostic is preserved in reports/unscoped_pytest_duplicate_collection.log. No test was removed or weakened.

Supplementary pagination audit identified legacy double-column table environments and top-only placement carried into a one-column document. The result-driven generator now emits ordinary tables with flexible placement for those legacy inputs. This changes layout only; full numerical verification and compilation are repeated before renewed PDF acceptance. Unsuccessful layout probes and preceding PDFs are preserved under original/layout_proofs/.

Final acceptance inspected the13-page main PDF and14-page Supplementary. Every final main rendering exactly matches its previously inspected full-resolution page; all revised supplementary pages were inspected, including cropped checks of the dense table page. Format-only validation confirms that legacy table scientific content and all other generated numeric inputs are unchanged. The final manifest and archive are written only after this acceptance.
