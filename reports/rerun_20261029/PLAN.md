# Full raw-data study rerun, 2026-10-29

Requested scope: download missing datasets, restore the recorded environment, enforce two GPUs, and rerun the complete two-dataset study. Execution follows `manuscript_revision/20261014/reproducibility/RUN_ORDER.md` in a clean workspace at `outputs/rerun_20261029/workspace`. Existing artifacts remain historical evidence.

1. Verify recorded Python 3.10 dependencies, package consistency, regression tests, CUDA XGBoost, and both hosts' user GPU accounting.
2. Link the existing GRABMyo sessions, check all published SHA256 entries, download NinaPro DB5 from official Zenodo record 1000116, verify archive checksums and extracted structures.
3. Rebuild 250 ms, bipolar, 150 ms and 500 ms features and caches from raw recordings.
4. Refit full-channel XGB/SVM/RF, cross-fitted rankings, all primary sparse curves, selection comparisons, stability, cross-session, faithfulness, DB5, bipolar and fixed-layout analyses, retaining the original seeds, budgets, penalties and participant exclusions.
5. Generate new-run input fingerprints after primary results exist; retain the published fingerprint file separately. Refit revision predictions, matched-budget comparisons, participant attribution, geometry, RF and completion curves.
6. Regenerate participant-level statistics, execute `16_verify_results.py --revision-dir ...`, build reports/figures/manuscripts, and compare the new results with the delivered record. Failed gates stop execution; no fabricated or partial metrics substitute for missing results. Compiled PDFs require fresh visual review before acceptance.

Resources: server 2; two explicit GPU UUIDs selected from live availability; at most two GPU execution processes at once. CPUs 2-7 and at most six analysis threads share a total eight-core compute allocation with the existing download on CPUs 0-1. Every stage runs inside detached tmux `sensor-study-20261029` with persistent logs and status JSON. The queue may take days; a running queue is not a completed reproduction.

Storage: the user specified this Linux checkout; no E: mount exists. Temporary files, caches and operational helpers are in `.tmp/`; deliverables and the isolated workspace are in `outputs/rerun_20261029/`.

Source datasets: [GRABMyo v1.1.0](https://physionet.org/content/grabmyo/1.1.0/) and [NinaPro DB5](https://zenodo.org/records/1000116). putEMG and unsupported optional neural analyses are outside the current documented study scope.
