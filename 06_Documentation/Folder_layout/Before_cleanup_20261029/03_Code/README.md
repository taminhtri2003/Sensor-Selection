# Code guide

Run commands from `F:\grabmyo_data`. Folder shortcuts preserve the code's original project-root discovery; the canonical executable code stays in `scripts/` and `src/`.

| Task | Scripts |
| --- | --- |
| Feature extraction and dataset checks | `20_extract_features_full.py`, `22_acquire_db5.py`, `33_db5_features.py`, `35_extract_bipolar_features.py` |
| Participant-disjoint ranking | `25_cross_fitted_ranking.py` |
| Primary electrode-count curve | `26_sparse_sensor_curve.py` |
| Selection baselines and statistics | `27_selection_baselines.py`, `28_statistics.py`, `37_secondary_statistics.py` |
| Stability, deletion and transfer | `29_stability.py`, `30_cross_session.py`, `31_faithfulness.py`, `34_db5_replication.py`, `36_bipolar_sensitivity.py` |
| Participant attribution | `53_participant_attribution.py` and the configuration in `configs/statistics/` |
| Matched predictions and selection resources | `64_revision_predictions.py`, `65_revision_matched_budget.py` |
| Sensitivity experiments | `62_completion_caches.py`, `71_revision_random_forest.py`, `79_primary_geometric_curve.py` |
| Final statistical outputs | `63_completion_statistics.py`, `66_revision_statistics.py`, `72_revision_outputs.py` |
| Figures 1-6 and S1-S7 | `67_revision_figures.py` |
| Result verification | `16_verify_results.py --revision-dir manuscript_revision/20261014` |
| Clean manuscript preparation, build and package | `87_prepare_final_manuscript.py`, `88_build_final_manuscript.py`, `89_release_final_manuscript.py` |

[Scripts](../scripts), [Python package](../src), [configurations](../configs), [tests](../tests), [environment files](Environment/), [dataset utilities](Dataset_utilities/) and [the frozen source snapshot](../manuscript_revision/20261014/reproducibility/code) are separated for browsing. Numbered scripts include earlier and exploratory analyses; the table identifies the main entry points.

The executed analysis environment was `D:\miniconda3\envs\graph_gpu\python.exe`. The exact executed dependency record is [requirements_current.txt](../manuscript_revision/20261014/reproducibility/requirements_current.txt); the original project lockfiles in Environment are retained for provenance and can differ.

Rebuilding statistics, figures or verification reports writes into dated output folders. Preserve an existing release before running those commands. Folder organization itself does not rerun experiments. Full reproduction instructions are in [Documentation](../manuscript_revision/20261014/reproducibility/README.md).
