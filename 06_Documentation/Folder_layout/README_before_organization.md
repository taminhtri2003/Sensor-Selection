# Subject-independent sEMG electrode selection

This repository evaluates cross-fitted electrode selection on GRABMyo v1.1.0 and NinaPro DB5.
The participant, not the window, is the unit of statistical inference. Outer test participants
must be excluded from attribution, scaling, fitting and any selection decisions.

The study is undergoing a completion and reproducibility audit. Historical completion reports
and packaged PDFs must not be treated as current until the publication gate passes.
See `STATUS.md` and `reports/study_review_20260922.md`.

The original fold-aggregated attribution analysis is retained. The post-hoc participant-level
extension is specified in `configs/statistics/participant_attribution_extension.json` and run by
`scripts/53_participant_attribution.py`; it is not a replacement for the frozen hypotheses.

## Verification

Use a Python environment with the dependencies in `pyproject.toml`:

```text
python -m pytest -q tests
python scripts/54_audit_predictions.py
python scripts/audit_leakage.py
python scripts/16_verify_results.py
```

Manuscript results must be generated from verified artifacts. Missing experiments never receive
placeholder numbers. Author declarations are left unresolved until supplied by the authors.
