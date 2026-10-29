# Pre-submission audit — "How far can a subject-independent sEMG array be reduced?"

Auditor role: senior reviewer and scientific editor (Physiological Measurement). Date: 2026-09-21.

**Inputs.**
- Manuscript: `manuscript/main_elsevier.pdf` (built 2026-09-21 17:19, 11 pp.), the current source of wording and numbering. The PDFs in `Downloads/manuscript*.pdf` are a different study (post-stroke HD-EMG) and were not used.
- Comment audit: `Downloads/Manuscript_Update_Guide_Comments_Audit_Highlighted.docx`. Its comments refer to the **2026-09-14 version** (Table 4/5, Figure 5 caption with Ch 1/9, LCB −0.0152) and are treated as historical guidance.
- Evidence: `artifacts/**`, `configs/statistics/frozen_analysis_plan.yaml`, `reports/decision_log.md`, and an independent recomputation written for this audit (`scripts/audit_presubmission_numbers.py` → `reports/presubmission_numeric_audit.csv`).

Every item below is tagged **MUST FIX / SHOULD FIX / OPTIONAL**. Per instruction, the manuscript has not been rewritten.

---

## A. Executive assessment

The numbers are sound. An independent recomputation from per-participant outputs reproduced every decision-relevant value in the text, including k*, the unrounded LCBs, the Δ signs, the n values and the deletion ordering. Tables, figures and text draw on one source of truth through generated macros.

The manuscript is **not yet submittable**, for five reasons. First, it claims the held-out participant had no influence, which the pooled count-feature threshold and the fold-1/fold-7 budget calibration contradict. Second, the H1 multiplicity handling departs from the frozen plan: Holm within H1 was required but not applied. The departure is harmless numerically (k* unchanged) but undisclosed, and the text's replacement argument (contiguity / fixed-sequence) is stated as if prespecified. Third, several sentences turn non-significance into equivalence ("matched", "did not differ", "about as well"). Fourth, two statements are false: the DB5 curve is not monotone, and the unit tests do not do what Methods says. Fifth, Figure 1 is unreadable at print size and uses prohibited wording.

None of these requires new experiments except the optional fold-wise threshold recomputation. The scientific conclusions do not change. What changes is how precisely they are stated.

---

## B. P0 — submission-blocking (all MUST FIX)

**P0-1. The "no influence of the held-out participant" claim is contradicted in two places.**
- *Evidence.* The ZC/SSC/WAMP threshold (10⁻² mV) was set from the pooled median |first difference| of all 43 participants (Methods §3.2; `reports/signal_properties_audit.md`). The GRABMyo training budgets (Decision 6: RF 200k, SVM 40k; Decision 8: 200k for the curve phases) were chosen from held-out Macro-F1 of participants 1 and 7 (`artifacts/metrics/budget_calibration.csv`).
- *Affected text.*
  - Abstract: "the held-out participant never influenced scaling, training or ranking".
  - Fig 1 caption: "all preprocessing statistics, model fitting and channel ranking use only the other participants R−p".
  - Fig 1 boxes: "Zero-Leakage LOSO Outer Split", "No feature scaling, ranking, or tuning!".
  - Methods §3.3: "No hyperparameter was tuned on any outer test participant".
- *Resolution, preferred.* Recompute the threshold leave-one-participant-out. This is cheap: accumulate per-participant histograms of |diff| (about 1 h CPU), then take the exact pooled-minus-one median for each fold. If 1.15 × every leave-one-out median gives the same threshold (10⁻² mV at the precision used), the fold-wise procedure produces identical features and the claim can be stated truthfully with that evidence. If any fold differs, re-extract features for those folds only and rerun the affected analyses. Do the same for DB5 (7 ADC) and the bipolar threshold (5 × 10⁻³ mV).
- *Resolution, minimum if no rerun.* Replace the absolute claims with: "z-scoring, model fitting, attribution and ranking used outer-training participants only; one label-free amplitude threshold for the count features was set from pooled recordings, and training-set sizes were calibrated on two folds (Section X)". Apply this to the Abstract, the Fig 1 caption, Fig 1 itself and §3.3.

**P0-2. H1 multiplicity: the plan was not followed, and a post-hoc argument is presented as control.**
- *Evidence.* The frozen plan (`hypothesis_tests.multiplicity`: Holm, applied to "each confirmatory family separately (H1–H4)") requires Holm within H1. `scripts/28_statistics.py` applies unadjusted per-k 95% two-sided intervals.
- *Recomputation* (`reports/presubmission_numeric_audit.csv`). With one-sided bootstrap p-values and Holm over the 15 tested k at α = 0.025, k* = **14 / 12 / 11** at δ = 0.01 / 0.02 / 0.03, identical to the reported values. A fixed-sequence procedure from k = 15 downward also gives 14 / 12 / 11.
- *Problematic text* (Results H1): "For the same reason, the result survives the multiplicity of testing 15 values of k. A fixed-sequence procedure … controls the familywise error rate without adjustment and yields the same k*." The contiguity of passing k values does not itself control FWER, and fixed-sequence testing was **not prespecified**.
- *Fix.*
  - Add the Holm-adjusted H1 analysis as the plan-conformant result, implemented after the fact. List it under Deviations.
  - Report fixed-sequence only as a post-hoc sensitivity analysis.
  - Delete "survives the multiplicity".
  - Remove the DB5 fixed-sequence sentence, or label it the same way.

**P0-3. Non-significance written as equivalence.**
- Abstract: "a data-free evenly spread layout matched the attribution ranking at most sizes".
- Results: "XGBoost and the SVM did not differ"; "attribution was not better than simpler alternatives"; "It did not differ from permutation importance…"; "The geometric baseline … matched SR-CFA at k = 4 … 8 … 12"; "session 3 did not differ"; "Performance on later sessions was not lower than on the training session".
- Discussion: the heading "Attribution is not better than simple alternatives"; "matched the attribution ranking at 4, 8 and 12 electrodes, and permutation importance matched it at three of four sizes".
- Conclusion: "performed about as well as the attribution ranking at most sizes".
- No equivalence test was run, so each must become "no statistically detectable difference (exploratory, uncorrected)" (see table I). The Discussion design recommendation "the evidence favours a well-spread layout of about 12 electrodes over trusting any particular ranking" is **unsupported**: GEOM at k = 12 was never tested for non-inferiority against 16 electrodes. Delete it or reframe it as a hypothesis.

**P0-4. False or overstated statements.**
1. Results DB5: "the ranked curve had the same monotone shape". The mean DB5 curve is **not monotone** (k = 11 < k = 10; k = 13 < k = 12; audit CSV). → "a broadly increasing curve".
2. Methods §3.4: "Unit tests verified that a participant-specific signal planted in the data could not raise that participant's score." The tests (`tests/test_leakage.py`, `tests/test_cross_fitted_attribution.py`) verify three things: the outer participant is never attributed, inner folds are subject-disjoint, and a subject-confounded canary detects scaler leakage. → State exactly that.
3. Results H4: "with many left, the array is redundant enough that any two electrodes can be spared". No experiment removed arbitrary pairs; the k = 14 contrast is non-significant, which is not evidence of equivalence. → Delete.
4. Results bipolar: "In deployable sensor units, then, the array showed no redundancy within the prespecified tolerance." The pairs are derived, not physical, and "no redundancy" goes beyond one NI failure. → See I-21.

**P0-5. Figure 1 is not fit for print** (see G).

---

## C. P1 — major revision

| # | Issue | Evidence | Action | Tag |
|---|---|---|---|---|
| C1 | **Margin rationale missing** (Phase 6). The paper says only "engineering tolerance, not clinical". | Plan's justification: "pragmatic engineering tolerance … chosen before the sensor curve" | Explain in §3.5: (i) 0.02 is an absolute difference in class-averaged F1, i.e. 2 points on a 0–1 scale; relative to the full-array curve reference (0.541) it is about 3.7% of performance and about 4% of the distance above chance (0.063); (ii) it was chosen as a tolerance for hardware simplification before the curve existed; (iii) it has no clinical or user-performance validation; (iv) 0.01 and 0.03 are reported because k* depends strongly on δ (14 / 12 / 11), so readers can apply their own tolerance. No clinical justification to be invented. | MUST |
| C2 | **Prespecification language is too broad.** | Intro: "Every decision rule was fixed in a statistical analysis plan written before any sparse-channel result existed." Fig 1 caption: "Decision rules (margin, statistical unit, bootstrap, multiplicity, k*) were frozen…". Conclusion: "decision rules fixed in advance". | Use three categories consistently (Phase 2 table below) and "prespecified" throughout (the word "pre-registered" is correctly absent from the text but present in Fig 1). | MUST |
| C3 | **Methods reproducibility gaps** (Phase 4). | Code inspection | Add: (a) attribution is **window-weighted**: up to 20,000 inner-held-out windows sampled uniformly without replacement, pooled across participants (near-balanced here because windows per participant are nearly equal; state the per-participant count); (b) PERM permutes **individual features** (sklearn `permutation_importance`, 3 repeats, 8,000 held-out windows from outer-training data, `f1_macro`), channel score = mean over its 10 features; (c) MI = `mutual_info_classif` per feature on 20,000 windows, channel score = mean over 10 features; (d) GEOM = farthest-point sampling on a 2 × 8 grid with circular arc distance (circumference 24 cm, ring spacing 2 cm), deterministic start at F1, ties → lowest index; (e) random subsets: k channels without replacement within a draw, draws independent (duplicate subsets possible; there are only 1,820 distinct subsets at k = 12), RNG seed 20260728 + participant id; (f) ranking tie-break = lower channel index; (g) per-subject profile = mean normalised attribution of that participant over the outer folds in which it was inner-held-out, and pairwise Spearman / Kendall / Jaccard@k over the 903 pairs; (h) XGBoost `multi:softprob`, all other defaults; (i) the comparison model's subsample uses the same seed as P4. | MUST |
| C4 | **Budget-calibration disclosure.** | Decisions 6 and 8 | State in §3.3 that the training sizes were set on held-out folds 1 and 7 before the confirmatory runs, and list this in Deviations/Limitations (part of P0-1). | MUST |
| C5 | **Limitations are incomplete** (Phase 10). | Discussion | Add: zero-phase (non-causal) filtering and 250 ms windows, making this an offline benchmark only; no imaging-based sensor-to-muscle registration; fatigue and posture not isolated; rankings come from full-array models and may shift after reduction; lighter H2/H4 model; H2–H4 inferential details specified post hoc; the fixed layout is post hoc; DB5 n = 10; the pooled threshold (if not rerun); derived rather than physical bipolar pairs. | MUST |
| C6 | **Conclusion lacks SUPPORTED / NOT ESTABLISHED structure** (Phase 11). | §6 | Rewrite (template in I-30). End with: "Validation in target clinical populations (e.g. people with upper-limb loss) and in online, causal control settings is required." | MUST |
| C7 | **"underpowered"** is used without a power analysis. | Discussion: "the replication was underpowered" | → "small (n = 10) and imprecise; the decision at k = 12 is sensitive to the bootstrap seed". | MUST |
| C8 | **SVM saturation inferred from one fold.** | "The SVM had therefore not saturated" | → "On one calibration fold … suggesting that the SVM had not saturated; its result is therefore likely a lower bound." | SHOULD |
| C9 | **Citation–claim alignment** is not yet verified at full-text level. Bibliographic identity is verified for all 35 entries; the *content* of several claims was checked only against titles/abstracts. | Intro: "subject-independent performance is systematically lower than user-dependent performance [phinyomark2018emg, cote2019deep]"; "every electrode adds cost … [vujaklija2016new]"; Related Work characterisations | An author must confirm each supporting passage in the full text, or soften the claim. | MUST |
| C10 | **Target journal / template mismatch.** | `\journal{Physiological Measurement}` with Elsevier `elsarticle` | Physiological Measurement is published by IOP; use the IOP template, or change the target journal. | MUST |
| C11 | **Figure 3 (curve)**: the primary δ is not visually dominant. | fig4_sparse_curve panel b | Make the primary δ = 0.02 thick and dark; draw 0.01 and 0.03 thin and grey with different dash patterns. Optionally annotate k* descriptively. | SHOULD |
| C12 | **Figure 7** shows mean curves for DB5 and bipolar, although their conclusions are NI decisions; the session panel is unpaired. | fig8 | Add Δ_k ± CI vs −δ panels for DB5 and bipolar; draw paired lines per participant for sessions (S1 → S2 → S3 under CS1; CS1-S3 vs CS2-S3). | SHOULD |
| C13 | **Methods ↔ Results order** (old comment #88): §3.8 "Exploratory analyses" bundles stability, cross-session, bipolar, DB5, fixed layout and redundancy, while Results mirrors them only loosely. | Structure | Give each exploratory analysis its own numbered Methods subsection, in the same order as Results. | SHOULD |
| C14 | **Bipolar reference**: the k = 8 curve reference (200k windows) differs from the full bipolar baseline (all windows). | Results bipolar | State the reference explicitly, as done for the monopolar curve. | SHOULD |

**Phase 2 classification (for C2 and P0-2).**

| A. Fixed before any sparse-channel result | B. Question fixed; inferential details specified later | C. Fully post hoc |
|---|---|---|
| Participant as unit; 10,000-resample cluster bootstrap, percentile 95% CI; primary margin 0.02 and sensitivity 0.01 / 0.03; k* = min{k : LCB > −δ}; Wilcoxon + r_rb; Holm within each confirmatory family (specified, **not implemented for H1**); H1–H4 statements; random-subset counts (100 / 500); λ candidates {0, 0.25, 0.5, 1}; DB5 / bipolar / cross-session as exploratory | H2 test family (8 tests, both rankings); H3 family (12 tests); H4 family (15 tests); λ handling (no λ* selected; the plan required selection but gave no criterion); H2/H4 comparison model (50 trees); λ = 0.5 for P4 (no recorded rationale); faithfulness protocol-check tolerance | Fixed-layout experiment; fixed-sequence H1 argument; DB5 and bipolar seed-robustness analyses; feature-redundancy analysis; LOO threshold check (if run) |

---

## D. P2 — polish

- SHOULD: Terminology. "participant" is used for GRABMyo and "subject" for DB5; keep that, and say so once. "SR-CFA" should mean λ > 0 only, with "cross-fitted SHAP (λ = 0)" for λ = 0; Fig 5's legend is correct, but Results H2 says "SR-CFA subsets" while referring to λ = 0.5.
- SHOULD: Deletion terminology. Use **Remove-Top / Remove-Random / Remove-Bottom** in Methods, Results, Table 5 ("Top removed"), Fig 5's legend ("most important removed first") and the text ("top-removed").
- SHOULD: "Kept" / "retained" / "n retained" → one term ("channels retained").
- OPTIONAL: The title is a question; the journal may prefer a declarative title.
- OPTIONAL: bibtex warns of empty pages for three entries (NeurIPS 2017 / 2019, EMBC 2006). Add page numbers from the proceedings, if verified.
- OPTIONAL: Define "chance Macro-F1 ≈ 0.063" as 1/16 under uniform guessing.

---

## E. Comment-audit matrix (historical comments vs current manuscript)

| OLD COMMENT | CURRENT STATUS | EVIDENCE | REQUIRED ACTION |
|---|---|---|---|
| #175 (P0) Table 4 vs Table 5 SR-CFA values disagree | **Resolved** | The two tables are different protocols: the headline curve (300 trees, 200k windows; now Table 2) and the comparison model (50 trees, 150k; now Table 3). Captions name each protocol; both generated from artifacts; the old hand-typed values are gone | None; keep the protocol names in captions |
| #199 (P0) ROAR remove/retain terminology inverted; k = 12 ordering | **Partly resolved** | The ordering was recomputed under one protocol and holds at every k, including 12 (Remove-Top 0.455 < Random 0.478 < Remove-Bottom 0.485). Terminology still mixes "top-removed", "Top removed", "most important removed first" | Adopt Remove-Top / Remove-Random / Remove-Bottom everywhere (D) |
| #88 (P1) Methods ↔ Results 1-to-1; baseline protocol before Results 4.1; consistent names | **Partly resolved** | §3.3 now contains the classifier protocol; exploratory methods are bundled | C13 |
| #89 (P1) Flowchart | **Open** | Fig 1 exists but fails at print size and uses prohibited wording | G-Fig 1 |
| #192 (P1) No blanket "SR-CFA outperforms" | **Mostly resolved** | Results report H2 per k with Holm; the exploratory contrasts are stated per k. New problem: the non-significant contrasts are now called "matched" | P0-3 |
| #196 (P2) No interpretation in captions | **Mostly resolved** | Fig 3 caption "(curves overlap)" and Fig 2 caption are descriptive; Fig 1 caption makes a claim (leakage) | Fix the Fig 1 caption (P0-1) |
| Old Fig 5 caption, flexor/extensor channels | **Resolved** | The anatomical wording was removed; Discussion declines muscle mapping | Add the limitation "no imaging-based registration" (C5) |
| Physiology as plausibility (REUSE) | **Resolved in spirit** | Discussion: "We deliberately do not map them to named muscles" | Optionally add one sentence in the plausibility framing without naming muscles for channels |
| Limitation: mapping without imaging (REUSE) | **Open** | Not stated | C5 |
| Limitation: ranking from the full model may shift after reduction (REUSE) | **Open** | Not stated | C5 |
| Fatigue / posture untested (ADAPT) | **Open** | Not stated | C5 |
| Real-time / clinical claims (REWRITE) | **Resolved** | No latency or clinical claims; "offline" stated | Add zero-phase / causal wording (C5) |
| Conclusion "validation in human subjects" | **Resolved / superseded** | The current conclusion has no such phrase; the required replacement sentence is missing | C6 |
| Abstract "pre-registered" | **Resolved in text; open in Fig 1** | Fig 1: "Pre-Registered Non-Inferiority" | G-Fig 1 |
| Abstract LCB −0.0152 vs −0.0160 | **Resolved** | −0.015973 recomputed; the macro prints −0.0160; the −0.0152 figures were archived | None |
| Bipolar k* from Δ / LCB | **Resolved** | k = 7: Δ = −0.015452, LCB = −0.020322 → not NI; k* = none at 0.02 | None |
| NinaPro unrounded LCB | **Resolved** | LCB = −0.019994 > −0.02 (margin 6 × 10⁻⁶); fragility reported | Print −0.019994 (6 dp) wherever the decision is discussed |
| "Hardware generalization" → methodological replication | **Resolved** | Text uses "methodological replication"; no transfer claim | None |
| Bibliography DOI / claim audit | **DOIs resolved; claim alignment open** | 35 entries from Crossref / arXiv | C9 |
| Adaptive recalibration "required" | **Resolved** | No such claim | None |

---

## F. Section-by-section review

**Title.** Accurate and appropriately cautious. OPTIONAL: declarative form ("Cross-fitted attribution supports a 25% reduction of a monopolar forearm sEMG array under a prespecified non-inferiority margin"). Avoid "subject-independent array" (it is recognition that is subject-independent).

**Abstract.**
- MUST: the "never influenced scaling, training or ranking" (P0-1) and "matched" (P0-3) sentences.
- MUST: "Deletion with retraining confirmed that the ranking was faithful" → "supported deletion-based faithfulness".
- MUST: "A population-level array of this design…" → "For subject-independent recognition with this two-ring monopolar montage…".
- SHOULD: say the H2–H4 test details were specified after results; keep n and the gesture count (they are present).

**Introduction.**
- MUST: "Every decision rule was fixed…" (C2).
- MUST: verify the cited support for the user-dependent vs subject-independent gap (C9).
- SHOULD: separate "user-dependent evaluation is valid for personalised systems" from "leakage" (old guide). The current text blends them in the first problem statement.

**Related Work.** Acceptable. SHOULD: confirm that the RoSHAP characterisation matches the preprint's method section.

**Methods.** MUST: P0-1, P0-4(2), C1, C3, C4, and the H1 Holm deviation added to §3.10. SHOULD: C13, C14.

**Results.** MUST: P0-2, P0-3, P0-4(1, 3, 4), and the "best subset available" sentence (I-10). SHOULD: report Holm-adjusted H1 alongside; state for H2 that "SR-CFA" = λ = 0.5.

**Discussion.** MUST: P0-3 (heading and "matched"), the unsupported design recommendation, "underpowered", "not decorative", "could not reorder channels in a way that mattered", and "The supported method is plain cross-fitted TreeSHAP magnitude" (ambiguous "supported"). Add C5.

**Conclusion.** MUST: C6; remove "about as well" and "population-level devices".

---

## G. Figure-by-figure review (at print size)

| Figure (PDF no.) | Findings | Action | Tag |
|---|---|---|---|
| **Fig 1 workflow** | Text about 4–5 pt at print width; text overflows boxes ("Margin:" clipped); arrows cross text; contains equations and a legend-like banner. Labels "HD-sEMG Signal Pipeline" (the montage is not high-density), "Concentric 16-Ch Montage", "Zero-Leakage LOSO Outer Split", "Strict Test Quarantine … No feature scaling, ranking, or tuning!", "Pre-Registered Non-Inferiority", "Non-Inferiority & Deployment". Caption makes the leakage claim. | Redesign as a left-to-right flowchart mirroring Methods: Data (GRABMyo, DB5) → Preprocessing & features → Outer LOSO split → Inner cross-fitted attribution → Ranking Q_c(λ) → Sparse retraining → Non-inferiority (H1) → H2 / H3 / H4 → Exploratory analyses. At most about 8 words per box, ≥ 7 pt at print size, no equations except Q_c(λ), no results. Wording: "Two-ring 16-electrode monopolar montage", "Outer leave-one-subject-out split", "Prespecified non-inferiority test", "Evaluation". Caption describes the boxes only. | MUST |
| **Fig 2 full channel** | Readable. Participant-paired lines present (a). Colours distinguishable in greyscale by x-position only; fine. | OPTIONAL: label model names directly under the strips (already done). | — |
| **Fig 3 sparse curve** | The four λ curves overlap (correctly shown). Panel b: δ lines use one colour; the primary is not dominant. | C11; y-label "Δk = F1k − F116" fine. | SHOULD |
| **Fig 4 baselines** | The legend (6 entries) sits above panel a; the order puts SR-CFA first, implying a winner; the random mean is a single point per k. | Order the legend alphabetically or by type (attribution / model-based / data-free / random); consider showing the random-subset distribution as a violin. Keep panel b. | SHOULD |
| **Fig 5 deletion** | Legend wording differs from Methods / Table. | "Remove-Top", "Remove-Random", "Remove-Bottom". | SHOULD |
| **Fig 6 attribution** | Positional only (good); no muscle names. At print size the in-cell labels are about 5.5 pt and borderline. | Increase to ≥ 6.5 pt. | SHOULD |
| **Fig 7 exploratory** | Session panel unpaired; DB5 and bipolar show curves, not the NI quantity. | C12. | SHOULD |
| Captions | Fig 3 "(curves overlap)" acceptable as description. No other interpretive captions. | — | — |

## H. Table-by-table review

| Table | Findings | Action | Tag |
|---|---|---|---|
| 1 Full channel | Correct values; the note gives Holm p. Training-window column OK. | — | — |
| 2 Sparse NI | Values verified (k = 12 LCB −0.015973). Primary δ column not visually identified. | Bold the δ = 0.02 header or mark it "(primary)". Add a Holm-adjusted H1 column or footnote (P0-2). | SHOULD / MUST (Holm) |
| 3 Baselines | "p=<0.001" typography (the `tab_baselines` rows use "$p$=$<$0.001"); corrected vs uncorrected rows labelled with a dagger (good); no bolding (good). | Fix to "p < 0.001". | MUST |
| 4 Stability | The outer-fold caveat is present. | Define Jaccard@k and the per-subject profile in Methods (C3g). | SHOULD |
| 5 Faithfulness | Headers "Top removed" etc.; values verified; ordering correct. | Rename to Remove-Top / Remove-Random / Remove-Bottom. | SHOULD |
| A.1 λ (H3) | Fine. | — | — |
| A.2 Cross-session | The note uses p with relation (fixed). | — | — |
| A.3 Replication | DB5 and bipolar combined in one table with different references (k = 16 vs k = 8). | Split into two tables, or add a clear column group header. Print DB5 k = 12 LCB to 6 dp (−0.019994). | SHOULD |

---

## I. Sentence-level rewrite table

| # | LOCATION | CURRENT TEXT | PROBLEM | PROPOSED REWRITE | REASON |
|---|---|---|---|---|---|
| 1 | Abstract, Approach | "…in which the held-out participant never influenced scaling, training or ranking." | Contradicted by the pooled threshold and the budget calibration | "…in which scaling, model fitting and channel ranking used only the other participants (one label-free feature threshold was set from pooled data)." | P0-1 |
| 2 | Abstract, Main results | "Deletion with retraining confirmed that the ranking was faithful." | "confirmed" overstates | "Deletion with retraining supported the faithfulness of the ranking." | Phase 5 |
| 3 | Abstract, Main results | "In exploratory comparisons, a data-free evenly spread layout matched the attribution ranking at most sizes." | Equivalence from non-significance | "In exploratory comparisons, no statistically detectable difference was observed between the attribution ranking and a data-free, evenly spread layout at 4, 8 and 12 electrodes." | P0-3 |
| 4 | Abstract, Significance | "A population-level array of this design tolerates removal of about a quarter of its monopolar electrodes within a stated engineering tolerance, not more." | "population-level array" overgeneralises | "For subject-independent, offline recognition with this two-ring monopolar montage, about a quarter of the electrodes could be removed within a prespecified engineering tolerance, but not more." | Phase 10 |
| 5 | Abstract, Significance | "…but it offers little beyond even spatial coverage for choosing sparse layouts." | Implies an equivalence that was not tested | "…but in exploratory comparisons its advantage over an evenly spread layout was detectable only at six electrodes." | P0-3 |
| 6 | Intro ¶3 | "Every decision rule was fixed in a statistical analysis plan written before any sparse-channel result existed." | Too broad (C2) | "The primary decision rules (statistical unit, bootstrap, non-inferiority margin, definition of k*) were fixed in a statistical analysis plan before any sparse-channel result existed; the test families for H2–H4 were specified in detail afterwards (Section 3.10)." | Phase 2 |
| 7 | Fig 1 caption | "…all preprocessing statistics, model fitting and channel ranking use only the other participants R−p. … Decision rules (margin, statistical unit, bootstrap, multiplicity, k*) were frozen before any sparse-channel result existed." | Leakage claim; interpretation in caption; over-broad | "Study workflow. For each held-out participant p, z-scoring, model fitting and channel ranking use the other participants R−p; attributions are computed on participant-disjoint inner folds of R−p; k-channel subsets are retrained and tested on p." | P0-1, Phase 8 |
| 8 | Methods §3.3 | "No hyperparameter was tuned on any outer test participant." | Budgets calibrated on held-out folds 1 and 7 | "Model hyperparameters were fixed in advance and not tuned; training-set sizes were chosen on two calibration folds (participants 1 and 7) before the confirmatory runs (Section 3.10)." | P0-1 / C4 |
| 9 | Methods §3.4 | "Unit tests verified that a participant-specific signal planted in the data could not raise that participant's score." | Not what the tests do | "Unit tests verified that the outer test participant is never attributed, that inner folds are participant-disjoint, and that a subject-confounded synthetic dataset detects scaler leakage." | P0-4 |
| 10 | Results H2 | "Attribution therefore reliably beats the average random subset, but it rarely finds the best subset available for a given person." | "best subset" judged from sampled subsets; "reliably" | "Attribution-ranked subsets exceeded the mean of the sampled random subsets at every k, but rarely fell in the upper tail (≥ 95th percentile) of each participant's sampled random-subset distribution." | Phase 5 |
| 11 | Results H2 ¶2 | "In exploratory contrasts, attribution was not better than simpler alternatives." | Equivalence / negation from non-significance | "In exploratory, uncorrected contrasts, attribution showed limited additional benefit over simpler alternatives." | P0-3 |
| 12 | Results H2 ¶2 | "It did not differ from permutation importance at k = 4, 8 or 12 … and it exceeded it only at k = 6 …" | Same | "No statistically detectable difference from permutation importance was observed at k = 4, 8 or 12 (…); SR-CFA was higher at k = 6 (…)." | P0-3 |
| 13 | Results H2 ¶2 | "The geometric baseline … matched SR-CFA at k = 4 (…), k = 8 (…) and k = 12 (…)." | "matched" | "…showed no statistically detectable difference from SR-CFA at k = 4, 8 and 12 (…); SR-CFA was higher at k = 6 (…)." | P0-3 |
| 14 | Results H1 | "For the same reason, the result survives the multiplicity of testing 15 values of k. A fixed-sequence procedure … controls the familywise error rate without adjustment and yields the same k*." | Contiguity ≠ FWER control; fixed-sequence not prespecified; the plan's Holm not applied | "The plan specified Holm correction within H1, which the primary analysis did not apply; applying it post hoc (one-sided bootstrap p, 15 values of k) gave the same k* at all three margins (Supplementary Table X). A post-hoc fixed-sequence analysis from k = 15 downward also gave the same k*." | P0-2 |
| 15 | Results H3 | "In these data, the cross-fitted magnitude ranking is already stable enough that a stability penalty has nothing to correct." | Causal / overstated | "Under this protocol the stability penalty produced no measurable improvement, consistent with the small instability term (median U_c/A_c = 2.4%)." | Phase 5 |
| 16 | Results H4 | "The only non-significant contrast was … where only two electrodes are removed." | Fine | Keep | — |
| 17 | Results H4 | "With few electrodes left all arms perform poorly; with many left, the array is redundant enough that any two electrodes can be spared." | Unsupported | Delete, or: "The separation between deletion orders was largest at intermediate sizes." | P0-4 |
| 18 | Results cross-session | "Performance on later sessions was not lower than on the training session." | Equivalence from non-significance (S3) | "Mean Macro-F1 on sessions 2 and 3 was numerically higher than on session 1; the session-2 difference was nominally significant (uncorrected) and the session-3 difference was not statistically detectable." | P0-3 |
| 19 | Results cross-session | "…and session 3 did not differ (…)." | Same | "…and no statistically detectable difference was observed for session 3 (…)." | P0-3 |
| 20 | Results DB5 | "The procedure itself transferred without modification, and the ranked curve had the same monotone shape." | Factually false (not monotone) | "The procedure ran on DB5 without modification; the mean curve increased broadly with k but was not monotone." | P0-4 |
| 21 | Results bipolar | "In deployable sensor units, then, the array showed no redundancy within the prespecified tolerance." | Derived pairs ≠ deployable; "no redundancy" overstated | "With derived bipolar pairs as the unit, no reduction met the primary margin." | Phase 10 |
| 22 | Results redundancy | "The duplicated feature therefore did not distort the channel ranking." | Absence claim | "Removing the duplicated feature had little measurable effect on the channel ranking." | Phase 5 |
| 23 | Results P1 | "XGBoost and the SVM did not differ: …" | Equivalence wording | "No statistically detectable difference was observed between XGBoost and the SVM: …" | P0-3 |
| 24 | Discussion ¶2 | "The ranking is therefore not decorative: it reflects what the retrained models depend on." | Informal, overstated | "Deletion with retraining therefore supports that the ranking reflects channels on which the retrained models depend." | Phase 7 |
| 25 | Discussion ¶2 | "It could not reorder channels in a way that mattered." / "The supported method is plain cross-fitted TreeSHAP magnitude…" | Informal; ambiguous "supported" | "It changed the top-12 set in at most one fold. The evidence therefore favours plain cross-fitted TreeSHAP magnitude over the regularised variant; a related robustness-weighted score has been proposed independently." | Phase 7 |
| 26 | Discussion heading | "Attribution is not better than simple alternatives" | Equivalence from non-significance | "Limited additional benefit over simple alternatives" | P0-3 |
| 27 | Discussion ¶3 | "A data-free geometric rule … matched the attribution ranking at 4, 8 and 12 electrodes, and permutation importance matched it at three of four sizes." | "matched" | "In exploratory comparisons, neither a data-free geometric rule (k = 4, 8, 12) nor permutation importance (k = 4, 8, 12) differed detectably from the attribution ranking." | P0-3 |
| 28 | Discussion ¶3 | "For a device designer, the evidence favours a well-spread layout of about 12 electrodes over trusting any particular ranking to identify an unusually good sparse subset." | Not tested (GEOM vs full not NI-tested) | "Whether a data-free, evenly spread layout is itself non-inferior to the full array was not tested and is a question for future work." | P0-3 |
| 29 | Discussion, cross-session | "Held-out participants were not recognised worse on later days than on the training day." | Equivalence phrasing | "No additional loss on later days was detected on top of the cross-user gap." | P0-3 |
| 30 | Discussion DB5 | "…but the replication was underpowered." / "It is best read as a non-contradiction rather than a replication of the reduction." | "underpowered" without a power analysis | "…but with 10 subjects the estimates were imprecise, and the k = 12 decision depended on the bootstrap seed; the result neither replicates nor contradicts the GRABMyo reduction." | C7 |
| 31 | Conclusion | whole paragraph ("decision rules fixed in advance", "about as well", "population-level devices") | C2, P0-3, Phase 10–11 | "Supported, for subject-independent offline recognition with a two-ring monopolar montage in able-bodied participants: removal of four of 16 electrodes within a prespecified 0.02 Macro-F1 tolerance; attribution-ranked subsets above the average random subset; deletion-based support for faithfulness; no measurable benefit from the stability penalty. Not established: clinical performance, reduction of physical bipolar hardware, equivalence to geometric selection, real-time use, muscle-level localisation, and generalisation beyond this cohort. Validation in target clinical populations (e.g. people with upper-limb loss) and in online, causal control settings is required." | Phase 11 |
| 32 | Methods §3.3 | "The SVM had therefore not saturated, and its result is a lower bound." | Single fold | "…suggesting that the SVM had not saturated; its reported result is therefore likely a lower bound." | C8 |

---

## J. Final pre-submission checklist

- [x] Every number in text / tables / figures generated from artifacts (`45_check_manuscript_numbers.py` PASS; independent recomputation consistent).
- [x] Participant counts 43 / 43 (10 / 10 DB5) in every analysis.
- [x] k* = 12 / 14 / 11; unrounded LCBs (k = 12: −0.015973; k = 11: −0.024479).
- [x] Bipolar decision from Δ / LCB (k = 7 LCB −0.020322 → fail); DB5 LCB −0.019994 (fragile, stated).
- [x] Deletion ordering holds at all 7 sizes (verified per participant file).
- [ ] P0-1 leakage claim fixed (preferred: LOO threshold recomputation).
- [ ] P0-2 Holm-within-H1 added and disclosed; fixed-sequence labelled post hoc.
- [ ] P0-3 all equivalence wording removed (items I-3, 5, 11–13, 18–19, 23, 26–29, 31).
- [ ] P0-4 false statements corrected (monotone, unit tests, "any two electrodes", "deployable").
- [ ] P0-5 / G Figure 1 redesigned; no "HD-sEMG / Concentric / Zero-Leakage / Pre-Registered / Deployment".
- [ ] C1 margin rationale paragraph.
- [ ] C3 Methods details (PERM, MI, GEOM, random draws, weighting, per-subject profiles).
- [ ] C5 limitations; C6 conclusion structure.
- [ ] C9 full-text claim–citation verification by an author.
- [ ] C10 journal / template decision.
- [ ] Tables: "p < 0.001"; Remove-Top / Random / Bottom; primary δ marked.
- [ ] Rebuild with `bash scripts/build_manuscript.sh` and re-run this audit's numeric script.
