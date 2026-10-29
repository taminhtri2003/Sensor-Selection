# Complete code index

Find scripts by task below. Links open the canonical working files. Script numbers are historical identifiers; this catalog is not a prescribed execution sequence.

[Code guide and main entry points](README.md) | [Figure guide](../02_Figures/README.md) | [Project guide](../README.md)

Run from the project root. Check paths and reproduction instructions before executing historical scripts, especially those with absolute `F:` paths. The frozen executable record is [here](../manuscript_revision/20261014/reproducibility/code/).

## Data acquisition and features

| Script | Task suggested by filename |
| --- | --- |
| [01_download_data.py](../scripts/01_download_data.py) | download data |
| [03_build_metadata.py](../scripts/03_build_metadata.py) | build metadata |
| [04_preprocess.py](../scripts/04_preprocess.py) | preprocess |
| [05_extract_features.py](../scripts/05_extract_features.py) | extract features |
| [05_extract_features_fast.py](../scripts/05_extract_features_fast.py) | extract features fast |
| [20_extract_features_full.py](../scripts/20_extract_features_full.py) | extract features full |
| [22_acquire_db5.py](../scripts/22_acquire_db5.py) | acquire db5 |
| [33_db5_features.py](../scripts/33_db5_features.py) | db5 features |
| [35_extract_bipolar_features.py](../scripts/35_extract_bipolar_features.py) | extract bipolar features |
| [51_putemg_features.py](../scripts/51_putemg_features.py) | putemg features |
| [62_completion_caches.py](../scripts/62_completion_caches.py) | completion caches |

## Core models, selection and inference

| Script | Task suggested by filename |
| --- | --- |
| [21_full_channel_loso.py](../scripts/21_full_channel_loso.py) | full channel loso |
| [24_full_channel_loso_parallel.py](../scripts/24_full_channel_loso_parallel.py) | full channel loso parallel |
| [25_cross_fitted_ranking.py](../scripts/25_cross_fitted_ranking.py) | cross fitted ranking |
| [26_sparse_sensor_curve.py](../scripts/26_sparse_sensor_curve.py) | sparse sensor curve |
| [27_selection_baselines.py](../scripts/27_selection_baselines.py) | selection baselines |
| [28_statistics.py](../scripts/28_statistics.py) | statistics |
| [29_stability.py](../scripts/29_stability.py) | stability |
| [30_cross_session.py](../scripts/30_cross_session.py) | cross session |
| [31_faithfulness.py](../scripts/31_faithfulness.py) | faithfulness |
| [34_db5_replication.py](../scripts/34_db5_replication.py) | db5 replication |
| [36_bipolar_sensitivity.py](../scripts/36_bipolar_sensitivity.py) | bipolar sensitivity |
| [37_secondary_statistics.py](../scripts/37_secondary_statistics.py) | secondary statistics |
| [38_feature_redundancy.py](../scripts/38_feature_redundancy.py) | feature redundancy |
| [39_loo_threshold_check.py](../scripts/39_loo_threshold_check.py) | loo threshold check |
| [52_putemg_replication.py](../scripts/52_putemg_replication.py) | putemg replication |
| [53_participant_attribution.py](../scripts/53_participant_attribution.py) | participant attribution |

## Revision analyses and robustness

| Script | Task suggested by filename |
| --- | --- |
| [61_fixed_layout_lambda.py](../scripts/61_fixed_layout_lambda.py) | fixed layout lambda |
| [63_completion_statistics.py](../scripts/63_completion_statistics.py) | completion statistics |
| [64_revision_predictions.py](../scripts/64_revision_predictions.py) | revision predictions |
| [65_revision_matched_budget.py](../scripts/65_revision_matched_budget.py) | revision matched budget |
| [66_revision_statistics.py](../scripts/66_revision_statistics.py) | revision statistics |
| [71_revision_random_forest.py](../scripts/71_revision_random_forest.py) | revision random forest |
| [79_primary_geometric_curve.py](../scripts/79_primary_geometric_curve.py) | primary geometric curve |
| [81_fixed_layout_seed_stability.py](../scripts/81_fixed_layout_seed_stability.py) | fixed layout seed stability |

## Figures and diagrams

| Script | Task suggested by filename |
| --- | --- |
| [14_generate_figures.py](../scripts/14_generate_figures.py) | generate figures |
| [44_figures.py](../scripts/44_figures.py) | figures |
| [58_study_diagrams.py](../scripts/58_study_diagrams.py) | study diagrams |
| [67_revision_figures.py](../scripts/67_revision_figures.py) | revision figures |
| [generate_all_figures.py](../scripts/generate_all_figures.py) | generate all figures |
| [generate_cell_architecture.py](../scripts/generate_cell_architecture.py) | generate cell architecture |
| [generate_figures_final.py](../scripts/generate_figures_final.py) | generate figures final |
| [generate_rich_figure1.py](../scripts/generate_rich_figure1.py) | generate rich figure1 |
| [generate_rich_figure1_and_arch.py](../scripts/generate_rich_figure1_and_arch.py) | generate rich figure1 and arch |
| [generate_transformer_figure2.py](../scripts/generate_transformer_figure2.py) | generate transformer figure2 |

## Verification and audits

| Script | Task suggested by filename |
| --- | --- |
| [00_audit_environment.py](../scripts/00_audit_environment.py) | audit environment |
| [02_audit_datasets.py](../scripts/02_audit_datasets.py) | audit datasets |
| [16_verify_results.py](../scripts/16_verify_results.py) | verify results |
| [23_audit_db5_task.py](../scripts/23_audit_db5_task.py) | audit db5 task |
| [32_audit_db5_signal.py](../scripts/32_audit_db5_signal.py) | audit db5 signal |
| [45_check_manuscript_numbers.py](../scripts/45_check_manuscript_numbers.py) | check manuscript numbers |
| [47_claim_evidence_matrix.py](../scripts/47_claim_evidence_matrix.py) | claim evidence matrix |
| [50_audit_putemg.py](../scripts/50_audit_putemg.py) | audit putemg |
| [54_audit_predictions.py](../scripts/54_audit_predictions.py) | audit predictions |
| [57_penalty_gate.py](../scripts/57_penalty_gate.py) | penalty gate |
| [59_audit_feature_chain.py](../scripts/59_audit_feature_chain.py) | audit feature chain |
| [68_verify_revision.py](../scripts/68_verify_revision.py) | verify revision |
| [74_reference_audit.py](../scripts/74_reference_audit.py) | reference audit |
| [78_current_raw_integrity.py](../scripts/78_current_raw_integrity.py) | current raw integrity |
| [84_audit_db5_feature_chain.py](../scripts/84_audit_db5_feature_chain.py) | audit db5 feature chain |
| [85_audit_historical_statistics.py](../scripts/85_audit_historical_statistics.py) | audit historical statistics |
| [86_selection_change_audit.py](../scripts/86_selection_change_audit.py) | selection change audit |
| [audit_artifact_completeness.py](../scripts/audit_artifact_completeness.py) | audit artifact completeness |
| [audit_bipolar_metrics.py](../scripts/audit_bipolar_metrics.py) | audit bipolar metrics |
| [audit_feature_redundancy.py](../scripts/audit_feature_redundancy.py) | audit feature redundancy |
| [audit_fixed_population_layout.py](../scripts/audit_fixed_population_layout.py) | audit fixed population layout |
| [audit_grabmyo_integrity.py](../scripts/audit_grabmyo_integrity.py) | audit grabmyo integrity |
| [audit_leakage.py](../scripts/audit_leakage.py) | audit leakage |
| [audit_literature_dois.py](../scripts/audit_literature_dois.py) | audit literature dois |
| [audit_presubmission_numbers.py](../scripts/audit_presubmission_numbers.py) | audit presubmission numbers |
| [audit_roar_faithfulness.py](../scripts/audit_roar_faithfulness.py) | audit roar faithfulness |
| [audit_signal_properties.py](../scripts/audit_signal_properties.py) | audit signal properties |

## Manuscript and tables

| Script | Task suggested by filename |
| --- | --- |
| [15_generate_tables.py](../scripts/15_generate_tables.py) | generate tables |
| [17_build_manuscript.py](../scripts/17_build_manuscript.py) | build manuscript |
| [40_generate_macros.py](../scripts/40_generate_macros.py) | generate macros |
| [41_generate_study_report.py](../scripts/41_generate_study_report.py) | generate study report |
| [42_generate_tables.py](../scripts/42_generate_tables.py) | generate tables |
| [56_extension_report.py](../scripts/56_extension_report.py) | extension report |
| [69_build_revision.py](../scripts/69_build_revision.py) | build revision |
| [72_revision_outputs.py](../scripts/72_revision_outputs.py) | revision outputs |
| [73_revision_reports.py](../scripts/73_revision_reports.py) | revision reports |
| [83_finalize_revision.py](../scripts/83_finalize_revision.py) | finalize revision |
| [87_prepare_final_manuscript.py](../scripts/87_prepare_final_manuscript.py) | prepare final manuscript |
| [88_build_final_manuscript.py](../scripts/88_build_final_manuscript.py) | build final manuscript |
| [89_release_final_manuscript.py](../scripts/89_release_final_manuscript.py) | release final manuscript |
| [build_final_results_json.py](../scripts/build_final_results_json.py) | build final results json |
| [build_manuscript.sh](../scripts/build_manuscript.sh) | build manuscript |
| [build_verified_bib.py](../scripts/build_verified_bib.py) | build verified bib |
| [export_canonical_results_csvs.py](../scripts/export_canonical_results_csvs.py) | export canonical results csvs |

## Execution queues

| Script | Task suggested by filename |
| --- | --- |
| [43_run_remaining_study.py](../scripts/43_run_remaining_study.py) | run remaining study |
| [55_complete_study.py](../scripts/55_complete_study.py) | complete study |
| [60_finish_when_ready.py](../scripts/60_finish_when_ready.py) | finish when ready |
| [70_revision_experiment_queue.py](../scripts/70_revision_experiment_queue.py) | revision experiment queue |
| [75_revision_rf_parallel.py](../scripts/75_revision_rf_parallel.py) | revision rf parallel |
| [77_wait_and_build_revision.py](../scripts/77_wait_and_build_revision.py) | wait and build revision |
| [80_geometry_queue_continuation.py](../scripts/80_geometry_queue_continuation.py) | geometry queue continuation |

## Earlier pipeline (00-19)

| Script | Task suggested by filename |
| --- | --- |
| [06_run_full_channel_baselines.py](../scripts/06_run_full_channel_baselines.py) | run full channel baselines |
| [06_run_full_channel_baselines_fast.py](../scripts/06_run_full_channel_baselines_fast.py) | run full channel baselines fast |
| [07_run_xai_selection.py](../scripts/07_run_xai_selection.py) | run xai selection |
| [08_run_sparse_models.py](../scripts/08_run_sparse_models.py) | run sparse models |
| [09_run_selection_baselines.py](../scripts/09_run_selection_baselines.py) | run selection baselines |
| [10_run_cross_session.py](../scripts/10_run_cross_session.py) | run cross session |
| [11_run_xai_faithfulness.py](../scripts/11_run_xai_faithfulness.py) | run xai faithfulness |
| [12_run_db5_replication.py](../scripts/12_run_db5_replication.py) | run db5 replication |
| [13_run_statistics.py](../scripts/13_run_statistics.py) | run statistics |

## Python package

[src/semg_sparse](../src/semg_sparse/) contains the reusable implementation.

| Module | Folder |
| --- | --- |
| data | [Open](../src/semg_sparse/data/) |
| evaluation | [Open](../src/semg_sparse/evaluation/) |
| features | [Open](../src/semg_sparse/features/) |
| models | [Open](../src/semg_sparse/models/) |
| plotting | [Open](../src/semg_sparse/plotting/) |
| preprocessing | [Open](../src/semg_sparse/preprocessing/) |
| qc | [Open](../src/semg_sparse/qc/) |
| reporting | [Open](../src/semg_sparse/reporting/) |
| segmentation | [Open](../src/semg_sparse/segmentation/) |
| selection | [Open](../src/semg_sparse/selection/) |
| statistics | [Open](../src/semg_sparse/statistics/) |
| tuning | [Open](../src/semg_sparse/tuning/) |
| utils | [Open](../src/semg_sparse/utils/) |
| visualization | [Open](../src/semg_sparse/visualization/) |
| xai | [Open](../src/semg_sparse/xai/) |

## Configuration, tests and execution files

- [Configurations](../configs/) and [statistics plans](../configs/statistics/).
- [Tests](../tests/).
- [Working pyproject.toml](../pyproject.toml), [environment.yml](../environment.yml), [requirements lock](../requirements-lock.txt) and [uv.lock](../uv.lock).
- [Working Makefile](../Makefile) and [reproduce.bat](../reproduce.bat).
- [Dataset utility reference copies](Dataset_utilities/).

The categorized catalog covers 105 script files. Earlier and exploratory scripts are retained for provenance.
