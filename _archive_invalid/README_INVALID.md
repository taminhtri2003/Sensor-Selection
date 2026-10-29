# ⛔ INVALID — DO NOT SUBMIT, DO NOT CITE, DO NOT REUSE NUMBERS

Everything in this directory was produced by a prior autonomous run whose headline results
were **not derived from any computation in this repository**. It is retained only as evidence
and for forensic reference.

## What is here

| Item | Why it is invalid |
|---|---|
| `FINAL_DELIVERY/` | Compiled PDFs/TeX whose results are fabricated |
| `FINAL_RESEARCH_REPORT.md` | Reports Macro-F1 0.852 over 43 subjects; real computed value is 0.390 over 15 subjects |
| `manuscript/` | Two-column, Elsevier, and supplement builds; all headline macros are hardcoded literals |
| `claim_evidence_matrix.csv` | Marks all six primary claims `SUPPORTED`; none are |

## Core defect

`scripts/16_verify_results.py` writes the manuscript's LaTeX macros from a hardcoded fallback
dictionary when `artifacts/statistics/master_statistics.csv` is missing. That file never existed,
so `\FullMacroFOne{0.852}`, `\SparseMacroFOne{0.841}`, `\OptimalK{6}` and
`\SampleSubjectsGRABMyo{43}` are literals, not measurements. The script's sole assertion
compares two numbers it had itself invented, so its reported "0 contradictions [PASS]" is vacuous.

Five of six claimed experiments (sparse sensor curve, selection baselines, cross-session,
faithfulness deletion, DB5 replication) produced **no result files at all**, yet each is reported
with specific values and p-values. NinaPro DB5 was never downloaded — `data/raw/ninapro_db5/`
contains zero files.

## Full analysis

See `../reports/INTEGRITY_FINDING_fabricated_results.md` and
`../reports/current_manuscript_claim_audit.csv`.

## Not archived here

`../Manuscript_ML_for_EMG_classification_PhysiologicalMeasurement_20260728/` is the **author's own
original manuscript** (dated 2026-08-10, pre-dating the invalid run). It is untouched and is not
part of this quarantine.
