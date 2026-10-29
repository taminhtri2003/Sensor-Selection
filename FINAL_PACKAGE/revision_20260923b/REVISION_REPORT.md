# Editorial and statistical revision, 2026-09-23

## Parts A and B: revised manuscript and supplement

| File | Content |
|---|---|
| `main_iop_marked.pdf` | Revised main manuscript. This round's changes are in blue. |
| `main_iop_clean.pdf` | Same text with no colour marking. |
| `supplementary_iop_marked.pdf` | Revised supplement (blue = changed). |
| `supplementary_iop_clean.pdf` | Same supplement, clean. |
| `manuscript_sources.zip` | LaTeX-ready sources: sections, tables, macros and figures. |

- **Source:** `manuscript/` in the repository. The pre-revision copy is in `_archive_invalid/pre_editorial_revision_2026-09-23/`.
- **Build checks:** the main text is 16 pages and the supplement 8. Both have no undefined references and no overfull boxes. `scripts/45_check_manuscript_numbers.py` returns PASS.
- **Provenance:** every number comes from a macro or a generated table, and no value was typed by hand.

## Part C: change log (substantive changes only)

| Location | Original issue | Revision | Reason |
|---|---|---|---|
| Introduction, last paragraph | "Four prespecified questions guide the analysis" | "The analysis plan posed four study questions". H1 is identified as the primary question with its decision rule fixed in advance; H2–H4 are secondary questions whose detailed test families were specified later. | The plan (`configs/statistics/frozen_analysis_plan.yaml`) names H1–H4 as confirmatory hypotheses. The detailed H2–H4 families were fixed only after the results (decision log, Decision 13). |
| Introduction; Results 3.1; Discussion (limitations); Conclusion; Abstract | Procedure and fixed layout were not distinguished | Added throughout: the LOSO design evaluates a selection procedure and the electrode count it supports; it is not a prospective validation of a fixed sparse hardware layout. | Rankings are recomputed in each outer fold. |
| Methods 2.3 | "confirmatory H2 family"; Holm "within each confirmatory test family" | "H2 test family (8 tests)". Holm is applied within each hypothesis family, and the plan-versus-specification history is stated. The text points to where every H2–H4 effect size is reported. | Exact prespecification language. |
| Methods 2.4 | Fixed-layout check not mentioned | One sentence added: a single-split consistency check, not independent validation. | Transparency. |
| Main Table 1 (was Table 2) | Eight columns mixing the three margins with Holm | Now shows k, Macro-F1, Δk, 95% CI, non-inferior at δ = 0.02, and Holm. k* = 12 is in bold, with a rule between k = 12 and k = 11. The δ = 0.01 and 0.03 decisions moved to Table S3. | Main table focused on the primary decision. |
| Main Table 2 (was Table 3) | Only the 4 SR-CFA-vs-random contrasts shown, without CI or r_rb; mixed with exploratory contrasts and percentiles | The complete 8-test H2 family: cross-fitted SHAP and SR-CFA × k = 4, 6, 8, 12. Columns: attribution mean, random mean, difference, 95% CI, higher/lower counts, p_Holm, r_rb. | The family was incomplete in the table. All values are from `artifacts/statistics/h2_attribution_vs_random.csv`. |
| Table S4 (new) | Exploratory contrasts sat inside the H2 table | SR-CFA vs permutation importance, geometric and mutual information at every k. Columns: means, difference, 95% CI, uncorrected p, r_rb. | Separates exploratory from secondary tests; adds CI and r_rb from `baseline_pairwise_exploratory.csv`. |
| Table 4 → Table S5 | Holm p only, no CI or r_rb | All 15 H4 contrasts with difference, 95% CI, p_Holm and r_rb. Figure 6 stays in the main text. | Complete H4 reporting, from `h4_faithfulness.csv`. |
| Results 3.2 (H4) | "held at every number retained" | The ordering is stated exactly: the three-way order where all three deletion orders exist, and Top < Bottom at every n. The non-significant 14-electrode contrast is kept explicitly. | Precision; the exception is retained. |
| Table 1 → Table S1 | Table and Figure 3 duplicated each other; XGBoost training windows were given as "all" | Figure 3 kept (between-participant variability). The table moved to the supplement, with "all (550,368 per fold)". | Option A. The count is identical in every fold (`loso_full_channel_subject_metrics_xgb.csv`). |
| Main Table 3 (was Table 5) | ρ given as mean ± SD but τ and Jaccard as means only | Every metric given as mean (SD). The caption states the values are descriptive and pairs are not independent. | Consistent convention; avoids implying inferential replicates. |
| Table S6 (H3) | No effect size | Adds r_rb, computed on untied participants and shown as "--" when all are tied, with a caption caveat. | Consistent effect-size reporting. |
| Results 3.2 | Participant-level extension occupied a paragraph and a main figure (Figure 7) | Summarised in 2 sentences. The figure became Figure S1, and the generated paragraph moved to supplementary methods S6. | Post hoc and null result. |
| Figure S2 caption | "Does the upgraded stability penalty improve prediction?" | "Stability penalty versus attribution magnitude alone under participant-level aggregation (post hoc)." | Neutral wording. |
| Table S8 (DB5); Results 3.3 | Column "Bootstrap seeds" showed 96%, while the text said 95.5% | Column is now "Non-inf. in bootstrap reruns" and reads 191/200 (95.5%). Text and caption describe it as a Monte Carlo decision-stability diagnostic, not a probability. New macro `\DBFiveSeedHits`. | Removes the inconsistency and the misleading label. |
| Table S10; Results 3.3 | 0.478 in the text versus 0.480 in the table, unexplained | Explained. 0.478 is the full-array bipolar model trained on all 550,368 windows (`bipolar_full_channel_metrics.csv`). 0.480 is the k = 8 reference of the 200,000-window reduction curve (`bipolar_provenance.json`), mirroring the monopolar 0.542 vs 0.541. Now stated in both places. | Different training budgets; nothing was reconciled by hand. |
| Supplementary S4 | Fixed-layout check used λ = 0.5 with no stated reason | Now states: λ = 0.5 was used, no rationale was recorded, and the primary analysis uses λ = 0. It also notes that the frozen layout differs by one electrode (3 vs 16) from the set excluded in the primary folds. Flagged [AUTHOR CHECK REQUIRED]. | Decision log, Decision 13: "no recorded rationale". No λ = 0 result was invented. |
| Table S2 | "95% participant interval"; gesture IDs only | Column is "95% bootstrap CI" (percentile bootstrap of the participant mean). Gesture names added from the dataset's `MotionSequence.txt`. | Verified in `src/semg_sparse/statistics/non_inferiority.py` and the dataset documentation. |
| Figure 5, tables | "Channel-selection methods" | "Electrode-selection methods". | Terminology. |
| Discussion | "The principal finding is deliberately modest"; "A second important result is negative"; "which is the simpler option"; "The headline 25% reduction"; "aggressive sparsification" | "The principal finding was a moderate reduction"; "Stability regularisation provided no statistically detectable benefit"; "suggesting that the additional stability term was unnecessary under the present protocol"; "The observed 25% reduction"; "larger reductions in electrode count" / "extensive electrode reduction". | Word choice as requested. |
| Discussion, limitations | Fixed-layout limitation missing | Added the procedure-versus-layout limitation. The fixed-layout check is described as a single split whose count was chosen after the full-cohort curve, and which used λ = 0.5. | Required limitation. |
| Conclusion | "consistently outperformed average random selection" | Rewritten. States: 12 electrodes met the criterion and 11 did not; moderate reduction; "outperformed the mean random-subset baseline at each tested subset size"; advantage over spatial selection limited to one subset size; no stability benefit; offline and montage-specific; fixed-layout validation still needed. | Aligned with the data. |
| Supplementary S1 | — | Departures now include the post hoc H2–H4 family specification, the λ used in the fixed-layout check, and the post hoc participant extension. | Complete disclosure. |
| Supplement overall | Order of tables did not follow the main text | S1–S10 now follow the order of first citation in the main text, and the reading order is explained at the top of the supplement. | Traceability. |
| Pipeline | A full rebuild (`scripts/58_study_diagrams.py`) would overwrite the authors' Figure 1 | The script's output is redirected to `figures/source/fig1_schematic_alternative`. | Prevents silently replacing Figure 1. |

The reorganised tables are all generated from the artifacts: main tables 1–3 and tables S1, S3–S6 and S8–S10 by `scripts/42_generate_tables.py`, and Table S2 by `scripts/56_extension_report.py`.

## Part D: author checks and values requiring recalculation

### Values requiring recalculation

None. Every value the brief anticipated might be missing is present in the saved results and is now reported:

- H2 cross-fitted SHAP CI and r_rb
- H2 SR-CFA r_rb at every k
- H4 CI and r_rb
- H3 r_rb
- rerun counts: 191/200 for DB5 and 0/200 for bipolar

### Author checks

1. **[AUTHOR CHECK REQUIRED: λ = 0.5 in the fixed-layout check (supplementary S4)].** No rationale was recorded. The options are:
   - (a) State a reason, if one exists.
   - (b) Repeat the check with λ = 0. This is a short GPU run with the existing script `scripts/audit_fixed_population_layout.py`, changing only `res.ranking(lam=0.50)`; it can be done on request.

   The check is exploratory in either case.
2. **[AUTHOR CHECK REQUIRED: gesture-name order (Table S2)].** Names follow the dataset's `MotionSequence.txt`, which states the order 1–17. The dataset's `GestureList.JPG` lays out three pairs in the opposite order:
   - IDs 5/6 (TIFE/TLFE vs TLFE/TIFE)
   - IDs 11/12 (WE/WF vs WF/WE)
   - IDs 13/14 (FS/FP vs FP/FS)

   Confirm against the recording protocol. Removing the names is also acceptable.
3. **[AUTHOR CHECK REQUIRED: Figure 1 artwork].** Issues outstanding from earlier:
   - text at about 5 pt, below the 8 pt minimum
   - the "Flexor/Extensor Group (FCR/FDS, EDC/ECU)" labels imply muscle mapping
   - "Reliable" and "Not stability assessment" in panel C imply that SR-CFA is superior
   - Myo-style pods instead of discrete electrodes
4. **[AUTHOR CHECK REQUIRED: title wording].** "a prespecified non-inferiority study" is defensible because the primary margin, statistical unit, bootstrap and k* rule were fixed in advance. Confirm you are comfortable with it, given that the H2–H4 families were specified later (this is disclosed).

### Author input still required (placeholders kept in the text)

- [AUTHOR INPUT REQUIRED: IRB determination or exemption for the secondary analysis] (Methods, ethics statement)
- [AUTHOR INPUT REQUIRED: acknowledgements]
- [AUTHOR INPUT REQUIRED: funding source and grant number]
- [AUTHOR INPUT REQUIRED: CRediT contributions]
- [AUTHOR INPUT REQUIRED: conflict-of-interest confirmation]
- [AUTHOR INPUT REQUIRED: permanent repository DOI for code, analysis plan and result files]

## Final self-check

| # | Check | Status |
|---|---|---|
| 1 | No invented numbers | All values come from macros or generated tables; the checker passes. |
| 2 | H1–H4 labels consistent | Yes: Introduction, Methods, Results, tables and supplement. |
| 3 | "prespecified" defensible | Used only for the primary margin and decision rule, the sensitivity margins, the plan's 500 subsets at k* and the absence of sex stratification. |
| 4 | Secondary vs exploratory distinguished | Yes. |
| 5 | Non-significance ≠ equivalence | Yes. |
| 6 | Fixed layout not overstated | Yes (S4, limitations, Conclusion). |
| 7 | Table/figure duplication reduced | Table 1 moved (Figure 3 kept); H4 table moved (Figure 6 kept); participant-extension figure moved. |
| 8 | Electrode/channel terminology | "Electrode" for the GRABMyo monopolar analysis; "channel" kept for DB5 (Myo channels) and in the feature definition. |
| 9 | Participant/subject terminology | "Participant" for GRABMyo. "Subjects" is kept only where the NinaPro DB5 documentation uses it and in the standard term "leave-one-subject-out". |
| 10 | λ and δ notation | Consistent. |
| 11 | p, p_Holm, r_rb formatting | Consistent. |
| 12 | CI format | "95% CI a to b" (text) or "a–b" for absolute values, as before. |
| 13 | Text vs tables | Consistent (same artifacts). |
| 14 | 95.5% vs 96% | Reconciled: 191/200 (95.5%). |
| 15 | Bipolar 0.478 vs 0.480 | Explained by the training budgets. |
| 16 | Placeholders listed | Yes (above). |
| 17 | Conservative and evidence-driven | Yes. |
