# Reproduction routes and operative script order

There are two different tasks: checking the frozen delivered record, and rerunning the entire study from downloaded signals. The revision was verified using the former and selectively rerun for the explicitly documented new experiments. It does not claim that every historical fit was freshly trained during this revision.

## Verify and rebuild delivered outputs

1. Restore the source folders from `reproducibility/code/` into a repository-shaped workspace. Keep `manuscript_revision/20261014/` in that workspace. The source uses paths relative to the repository root, not a required drive letter.
2. Restore historical quantitative inputs from `reproducibility/verified_inputs/` to the same root-relative paths. Preserve the original frozen plan and supplied result manifests. Revision experiments already reside in the dated package.
3. Obtain the real public datasets and place the GRABMyo `Session1/`, `Session2/`, `Session3/` trees and NinaPro DB5 `data/raw/ninapro_db5/` at the documented locations. Public source identifiers, license notes and original checksum lists are retained with the package.
4. Reconstruct the feature caches if absent using the raw extraction/cache scripts below. Compare the resulting byte fingerprints with `input_hashes.json`. Never edit an old expected hash to conceal a mismatch.
5. Install the executed versions in `requirements_current.txt` in Python3.10. CUDA-capable XGBoost, pdflatex, bibtex, pdftoppm, pdftotext and pdfinfo are required for the recorded analysis/build/QA path. The historical lock in `legacy_build_metadata/` describes a different environment.
6. Run `python scripts/69_build_revision.py`. It dispatches the required `scripts/16_verify_results.py --revision-dir manuscript_revision/20261014`, regenerates figures/tables/reports and compiles both PDFs. Then render and inspect every page. A new PDF is not covered by an old visual-acceptance fingerprint.

The current gate intentionally needs the original raw/cache inputs as well as the compact result package; raw signal and feature-cache data are not duplicated in the archive. A successful numerical build does not supply missing author declarations.

## Full raw-data rerun in a separate clean workspace

These commands describe the operative later pipeline, not the invalid preliminary scaffold. Each command reads real recordings or preceding real outputs. They are a reproduction route, not a claim that all were newly executed on2026-10-14. Keep the frozen delivered workspace intact. Seed20260728, budgets and fixed penalties are retained in source/configuration. A different GPU/library stack may prevent byte-identical outputs; preserve that new run separately and report differences rather than rewriting the delivered fingerprints.

```powershell
python scripts/audit_grabmyo_integrity.py
python scripts/22_acquire_db5.py
python scripts/23_audit_db5_task.py
python scripts/32_audit_db5_signal.py
python scripts/20_extract_features_full.py
python scripts/33_db5_features.py
python scripts/35_extract_bipolar_features.py
python scripts/24_full_channel_loso_parallel.py --models XGB --device cuda --workers 1 --tag _xgb
python scripts/24_full_channel_loso_parallel.py --models SVM,RF --workers 3 --rf-jobs 2 --tag _svmrf
python scripts/25_cross_fitted_ranking.py --device cuda --workers 1 --inner-folds 5 --max-attrib 20000 --max-train 200000
python scripts/26_sparse_sensor_curve.py --model XGB --device cuda --group-lambdas --lambdas 0.0,0.25,0.5,1.0 --train-subsample 200000 --k-workers 4
python scripts/27_selection_baselines.py --device cuda --k-values 4,6,8,12 --k-star 12 --n-random 100 --n-random-at-k-star 500 --srcfa-lambda 0.5 --fit-workers 4
python scripts/29_stability.py
python scripts/30_cross_session.py
python scripts/31_faithfulness.py --device cuda --srcfa-lambda 0.0 --keep-sizes 2,4,6,8,10,12,14 --fit-workers 4
python scripts/34_db5_replication.py --device cuda
python scripts/36_bipolar_sensitivity.py --device cuda --train-subsample 200000 --k-workers 4
python scripts/38_feature_redundancy.py
python scripts/39_loo_threshold_check.py
python scripts/28_statistics.py
python scripts/37_secondary_statistics.py
python scripts/61_fixed_layout_lambda.py
python scripts/20_extract_features_full.py --window-ms 150
python scripts/20_extract_features_full.py --window-ms 500
python scripts/62_completion_caches.py
```

The table of original comparison counts is intentionally reproduced; this command does not newly select12 based on a fresh experiment. Original ranking and count artifacts are required before the dated revision fits. The revision queue does not create the Rest17 curve itself; in a fully clean reconstruction run it explicitly:

```powershell
python scripts/26_sparse_sensor_curve.py --model XGB --device cuda --group-lambdas --lambdas 0.0 --train-subsample 200000 --k-workers 4 --cache-dir data/cache/rest17 --out-dir artifacts/completion_analyses/rest17
```

Then follow the dated README's scripts64,70,79,71/75 and81 and the final69 build. Script70 covers window500/window150, shared-resource selection and isolated person aggregation. Script79 supplies the additional full geometric ordering after70. Script71 starts the RF manifest and can finish the RF curve by itself;75 is the documented scheduling continuation, not a different classifier. Do not run duplicate writers against one result folder.

Historical scripts00-15 and older manuscript/build entry points are preserved as source history; they are not the revision's reproduction route. The quarantined preliminary package is excluded. Optional CNN/IG, mRMR and independent new-cohort validation were not executed and have no fabricated result.
