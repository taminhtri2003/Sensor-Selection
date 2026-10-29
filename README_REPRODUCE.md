# Reproducing the current study

Use the package versions recorded from the working scientific environment in
`reproducibility/requirements_execution_20260922.txt`. The root `requirements-lock.txt` describes
a different environment and is not evidence of the environment that produced these reruns.
GPU execution requires a CUDA-capable XGBoost build; LaTeX requires pdflatex and bibtex.

## Rebuild from completed result files

```text
python scripts/55_complete_study.py
```

This runs regression tests, reconstructs baseline metrics from saved predictions, checks
attribution and selected-subset provenance, regenerates participant-level statistics, invokes
the mandatory `16_verify_results.py` gate, and builds the IOP manuscript and supplement.
It exits on any failure. Compiled PDFs still require visual review. Unresolved author declarations
remain marked and keep the package out of submission-ready status.

## Finish interrupted experiments, then rebuild

```text
python scripts/55_complete_study.py --finish-experiments
```

Do not start this while another copy of the bipolar or participant-attribution experiment is
running. The current logs are `runs/p11_bipolar_completion_20260922.log` and
`runs/participant_attribution_20260922.log`.

The attribution extension requires complete original P2/P3 artifacts. It has its own saved
protocol, exact input SHA256 fingerprints and per-evaluation provenance. A changed input refuses
resume. Original P2 checkpoint generation now similarly fingerprints inputs and parameters;
legacy checkpoints without that metadata must be audited separately or recomputed in an isolated
`--output-dir`. Never combine outputs from different feature thresholds, training budgets or seeds.

## Data and primary experiment order

Downloaded GRABMyo raw recordings are under `Session1/`, `Session2/`, `Session3/`; DB5 is under
`data/raw/ninapro_db5/`. No synthetic samples or metrics enter the study.

1. `audit_grabmyo_integrity.py` and the DB5 manifest verify source data.
2. `20_extract_features_full.py`, `33_db5_features.py`, `35_extract_bipolar_features.py` extract features.
3. `24_full_channel_loso_parallel.py` runs full-channel baselines.
4. `25_cross_fitted_ranking.py` computes original fold-based attribution (new isolated directory for a fresh run).
5. `26_sparse_sensor_curve.py --group-lambdas --lambdas 0.0,0.25,0.5,1.0 --train-subsample 200000` runs the primary curve.
6. Scripts `27`, `29`, `30`, `31`, `34`, `36`, `38` run baselines, stability, sessions, faithfulness,
   DB5, bipolar and feature redundancy under their documented protocols.
7. `53_participant_attribution.py` runs the post-hoc person-level aggregation extension.
8. `55_complete_study.py` regenerates and verifies the complete reporting graph.

The archived putEMG analysis is outside the current two-dataset scope. The optional CNN/IG,
window-length and rest-inclusive analyses must not be described as completed without artifacts.

## Scientific limits

The study retains the frozen margins and participant-level statistical unit. Post-hoc extensions
are labelled. Earlier test-fold budget calibration and pooled threshold estimation are disclosed;
passing the present code checks does not prove a development-independent historical test cohort.
A non-significant stability benefit remains a negative result, not a failed software build.
