# Reproduce the 2026-10-14 revision

Run from `F:/grabmyo_data`, using `D:/miniconda3/envs/graph_gpu/python.exe`. Paths in the source assume the repository root; a portable reconstruction must place downloaded raw data, the documented feature caches and immutable original result files in that layout. The source snapshot in `reproducibility/code/` is taken after the final fits and is covered by `source_manifest.csv`.

The public datasets are GRABMyo v1.1.0 (https://doi.org/10.13026/89dm-f662) and NinaPro DB5 (https://ninapro.hevs.ch; dataset archive https://doi.org/10.5281/zenodo.1000116). Respect the source datasets' terms and attribution. No synthetic data contribute study metrics. Local raw data are not included as purportedly newly acquired data.

## Immutable original inputs

`input_hashes.json` fingerprints the primary X/y/participant caches, original rankings, sparse curve and the two primary fit/geometry scripts. Original result trees remain in `artifacts/`; September manuscript and relevant reports are preserved under `original/`. The old attribution-extension source-hash failure remains preserved and documented. Do not overwrite its manifest to make it pass.

## New fits, in order

```powershell
D:/miniconda3/envs/graph_gpu/python.exe scripts/64_revision_predictions.py --resume
D:/miniconda3/envs/graph_gpu/python.exe scripts/70_revision_experiment_queue.py
```

The GPU queue completes the500ms cohort, the full150ms curve, shared-resource SHAP/group permutation, and an isolated current-provenance attribution extension. It can resume participant checkpoints. Execute the initial RF script only on a fresh RF output tree; for the recorded scheduling continuation, first preserve the script71 input manifest/checkpoints, then run:

```powershell
D:/miniconda3/envs/graph_gpu/python.exe scripts/71_revision_random_forest.py
# The recorded continuation uses unchanged parameters with concurrent participant scheduling:
D:/miniconda3/envs/graph_gpu/python.exe scripts/75_revision_rf_parallel.py
```

Do not run71 and75 concurrently against the same output. The parallel runner requires the original71 manifest and preserves complete participant checkpoints; missing participants are fit with the same sampling, scaling, parameters and seed. Amendment05 documents this resource-only scheduling change. To reproduce the recorded path on an empty output,71 can run to completion;75 then validates and preserves the complete grid without adding models.

Original pipeline scripts and configurations reconstruct feature extraction, original cross-fitting, random comparisons, deletion, DB5, derived bipolar and cross-session analyses. Dataset and cache checks appear in the original run records and the current feature-chain validation log. Re-running an entire raw-data pipeline is distinct from verifying already downloaded inputs and saved outputs.

## Complete statistics and release build

Only after every required participant grid is complete:

```powershell
D:/miniconda3/envs/graph_gpu/python.exe scripts/69_build_revision.py
```

This runs completion statistics, new participant-level statistics, the required `scripts/16_verify_results.py --revision-dir manuscript_revision/20261014` route, result-driven tables/macros/figures, evidence reports and three LaTeX passes. Missing files, incomplete grids, changed input hashes or unresolved TeX references are hard failures. The default historical16 route still checks the historical extension and may report its preserved source-hash mismatch; the revision route explicitly verifies the fresh isolated extension.

For tests:

```powershell
$env:PYTHONPATH='F:/grabmyo_data/.test_dependencies'
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
D:/miniconda3/envs/graph_gpu/python.exe -m pytest tests -q
```

The recorded environment, installed package versions, GPU/CPU details and source checksums are saved with the final build. Runtime measurements are observational on this workstation and are not portable latency guarantees.

## Quantitative traceability

- `experiments/primary_predictions/`: exact paired canonical row indices, true labels and predictions for full16/SHAP12/geometric12; metrics and input manifests.
- `experiments/matched_budget/`: all five inner-fold score vectors, participant partitions, shared validation indices, rankings, costs and paired final results.
- `experiments/attribution_extension/`: current source fingerprints and exact-source reuse rows; every penalty and count.
- `experiments/alternative_classifier/`: fixed-count RF predictions, result grid, source/scheduling manifests.
- `experiments/statistics/` and `tables/`: all full-precision participant, gesture, method and NI outputs.
- `manuscript/generated/`: numeric macro provenance, regenerated primary and supplementary tables.
- `figures/source_data/` and `figure_provenance.csv`: exact plotting inputs and hashes; vector PDFs/SVGs and300dpi previews are retained.
- `reports/verification.json`: numerical/exclusion/provenance checks; `08_final_quality_control.md` includes compilation and visual acceptance.

LaTeX sources are editable in `manuscript/main.tex` and `supplementary.tex`. Rendering and inspection of every PDF page are required after compilation. The final package manifest is written after that inspection. Author-only declarations and unavailable independent cohort evidence remain in `reports/unresolved_author_inputs.md`.

Official Zenodo record1000116 is DB5 (double Myo), and1000138 is DB4 (Cometa). The PLOS source article's data-availability paragraph reverses these two links. Dataset identity follows official repository titles, sensor structure and matching archive checksums, not the transposed links. The actual study downloads use the correct DB5 record1000116.


## Geometric continuation and boundary diagnostic

Amendment06 adds the complete fixed geometric ordering at all sixteen counts after geometry12 had already been examined. It is exploratory, not prospectively chosen before all geometry results. After script70 finishes, run script79; script80 is the one-time continuation that waits for script70 before doing so:

```powershell
D:/miniconda3/envs/graph_gpu/python.exe scripts/80_geometry_queue_continuation.py
```

Amendment07 records the fixed-layout Monte Carlo diagnostic. Script81 reruns both existing split summaries for all200 recorded seeds; it fits no models, selects no seed and retains the original boundary decision:

```powershell
D:/miniconda3/envs/graph_gpu/python.exe scripts/81_fixed_layout_seed_stability.py
```

The one-time script77 release coordinator waits for full participant coverage and explicit completion messages from the original GPU queue, geometric continuation and RF track, then invokes69. It is not a recurring automation. Script69 cannot declare visual acceptance; inspect the rendered pages before writing the final QC report.

The historical invalid preliminary delivery remains quarantined in `_archive_invalid/`. Its fabricated headline values are not revision inputs. The current revision uses the later real-data result trees, canonical prediction files and strict missing-input failures. See the preserved `original/reports/INTEGRITY_FINDING_fabricated_results.md` for the earlier finding; do not confuse that dated audit with the current quantitative record.


The executable source snapshot includes `tests/`. `requirements_current.txt` records the actual analysis, raw-audit and test versions; `local_dependency_versions.json` records the local fallback packages used via PYTHONPATH (including wfdb). The old repository lock is preserved under `code/legacy_build_metadata/` for provenance and must not be mistaken for the executed environment. Package metadata there contains historical placeholder authorship and supplies no manuscript declaration. On a clean machine, install the current requirements rather than relying on the workstation's fallback folder.

See `RUN_ORDER.md` for restoration of frozen inputs versus a full raw-data rerun, with operative script flags and the separate Rest17 step.

The revision gate also runs84_audit_db5_feature_chain.py: every saved DB5 E1 feature row is reconstructed from raw data, verifying the effective10-89Hz band rather than the originally printed requested10-95Hz. The correction preserves actual features and metrics.

The recorded verification route is Windows/PowerShell. Some preserved historical manifests use Windows path separators; a Linux/macOS port has not been verified. A cross-platform replication must handle those paths explicitly and preserve the historical records, rather than claiming the untouched Windows verification path was executed there.

The current gate also runs85_audit_historical_statistics.py. It regenerates all15 original primary/secondary statistical tables into an isolated revision folder and compares complete contents with the originals, while retaining the frozen rule and original seeds. Fixed-layout means, original-seed confidence bounds and decisions are recomputed for every split/penalty as well. Failed/new verification attempts invalidate stale PASS status; repeated build logs are archived under reports/build_history/.

Amendment08 documents the post-hoc selector-activity diagnostic after negative penalty results. Script86 quantifies physical site-set changes for every fixed penalty/count and both aggregation rules, checks identical-set metric consistency, and adds no models or significance tests. Its full96-cell and4128-participant-record outputs are retained; the current16 gate regenerates them.

## Current inference versus layout checkpoints

The complete current count-inference record is experiments/statistics/noninferiority_audit.csv with kstar_audit.csv (all fourteen conditions). Files prefixed initial_primary and completed_ni, and completed_preview_provenance.csv, are earlier completed-analysis layout checkpoints; they omit the then-unfinished geometric curve and are not the complete release inference. The final manuscript uses the full record, generated macro provenance and figure_provenance.csv.
