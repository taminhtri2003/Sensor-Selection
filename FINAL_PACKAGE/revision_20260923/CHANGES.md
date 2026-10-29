# Rewrite from `main_iop_revised_writing.md`, 2026-09-23

**Source:** the manuscript in `FINAL_PACKAGE/review_20260922/`, identical to `manuscript/` before this edit. The previous sources are archived in `_archive_invalid/pre_markdown_rewrite_2026-09-23/`.

## Files

| File | Content |
|---|---|
| `main_iop_marked.pdf` | Rewritten manuscript. Text taken from the markdown draft is **blue**; black is text kept from the previous version. |
| `main_iop_clean.pdf` | The same text with no colour marking. Built with `\def\cleanbuild{1}`. |
| `supplementary_iop.pdf` | Supplementary material. Content unchanged; text now justified. |
| `manuscript_sources.zip` | LaTeX sources, tables, figures and macros. |

## Layout

- Body text, abstract and captions are justified on both sides. The IOP class sets `\raggedright` globally, so `ragged2e` + `\justifying` override it, and `\@makecaption` is redefined.
- Blue marking uses the macro `\chg{}`. Turn it off with `\showchangesfalse` or the clean build.
- A `\needspace` stops the Discussion heading from being stranded at the bottom of a page.

## Structure (follows the markdown's suggested structure)

The sections are now: 1 Introduction; 2 Methods (2.1–2.4); 3 Results (3.1–3.3); 4 Discussion, as continuous prose; 5 Conclusion.

The separate Related-work section was removed. Its key citations were moved into the Introduction (attribution stability and the novelty caveat for the penalty) and the Discussion (electrode shift).

## Kept from the previous version (black text)

The markdown is a writing draft that leaves these out. They are required by the journal or for reproducibility, so they were kept and merged into the new subsections:

- ethics statement
- sex reporting
- terminology definitions
- DB5 description
- mains-frequency identification
- count-feature threshold rule and its leave-one-out check
- XGBoost chronology and hyperparameters
- SVM and random-forest training budgets
- TreeSHAP sampling details and the Φ equation
- list of the H2 selection methods, the comparison model and the Holm family sizes
- deletion design
- caveat about overlapping LOSO folds
- designs of all exploratory analyses
- statistics (p, CI, r_rb) behind every claim in the Results
- participant-extension paragraph (generated)
- limitation items not listed in the markdown: SVM lower bound, lighter H2/H4 model, budget calibration on held-out folds, λ not selected, fixed-layout single-split check, window-length and 17-class analyses not run

## Numbers

Every number in the markdown was checked against `generated/results_macros.tex` and all of them match. Examples:

- full array: 0.542 (0.517–0.567)
- smallest non-inferior subset: k* = 12, Δ = −0.0133 (−0.0160 to −0.0106)
- lower bound at 11 electrodes: −0.0246
- k* is 14 at δ = 0.01 and 11 at δ = 0.03
- mean difference at 8 electrodes: −0.0366

All numbers in the text are still result macros. `scripts/45_check_manuscript_numbers.py` returns PASS.

## Places where the markdown was changed to match the evidence

| Location | Markdown | Revised | Reason |
|---|---|---|---|
| Abstract, Approach | test participant excluded from "… electrode ranking, and parameter estimation" | "… model fitting and electrode ranking" | The count threshold was computed once from 6 pooled participants, and training budgets were calibrated on held-out folds. Claiming exclusion from all parameter estimation would overstate. |
| Abstract | 320 words | 298 words | The journal limit is 300. Wording was trimmed; no content was removed. |
| Abstract, Main results | "an advantage was observed at six electrodes" | "attribution scored higher at six electrodes" | That contrast is exploratory and uncorrected. |
| 2.3 | "Holm correction … within prespecified confirmatory test families" | "within each confirmatory test family" | The detailed H2–H4 families were specified after results were available (supplementary methods S1). |
| 2.4 | departures list | adds "application of the plan's Holm correction for H1 after the primary analysis" | Keeps the full departures disclosure. |
| 3.3, DB5 | "one reduced configuration approached the non-inferiority boundary" | "met the non-inferiority margin by a negligible amount" | The lower bound was −0.019994, above −0.02, so it met the margin at the primary seed (95.5% of seeds). |
| 3.2, deletion | "generally produced the largest loss" | the ordering held at every retained count | The macros show the ordering held at all counts; 14 of 15 contrasts were significant. |
| Discussion ¶3 | "spatial coverage alone was no longer sufficient to match…" | "scored higher than both … in uncorrected exploratory contrasts" | Avoids a causal claim from an uncorrected exploratory test. |
| Discussion ¶4 | "Attribution becomes more informative when the selection problem becomes sufficiently constrained" | "At six electrodes … appeared to matter more. No advantage over the geometric layout was detected at four electrodes, however, so the benefit … did not simply increase as the array was reduced." | At k = 4, no difference was detected between SR-CFA and geometric selection (−0.0005, p = 0.986). A monotone "more constrained → more useful" claim contradicts the data. |
| Discussion ¶5 | "plain TreeSHAP magnitude captures essentially all of the useful ranking information" | "the tested stability formulation added no detectable ranking information beyond plain … magnitude" | p > 0.05 is not evidence of equivalence. |
| Results 3.1 | "reduced Macro-F1 by 0.0366" | "gave a mean difference of −0.0366" | The value comes from a signed macro. |
| Introduction | H1–H4 posed as questions without labels | labels (H1)–(H4) added | Methods, Results and the supplementary material refer to the labels. |

## Still requiring author input (unchanged)

The following are still marked [AUTHOR INPUT REQUIRED]:

- IRB determination for the secondary analysis
- acknowledgements
- funding
- CRediT roles
- conflict-of-interest confirmation
- permanent repository DOI

## Figure 1 (2026-09-23, second request)

- Figure 1 is now the authors' figure `FINAL_PACKAGE/figures/Figure 1 - Explainability-Guided Sensor Selection in Subject-Independent sEMG Gesture Recognition .pdf`. It is byte-identical to `manuscript/figures/source/fig1_overview_original_canva.pdf`.
- The figure is built by `manuscript/figures/source/make_fig1_overview.py`, which makes three label-level corrections to match the GRABMyo electrode documentation and crops the blank margins:
  - ring spacing changed from 3 cm to 2 cm
  - proximal ring relabelled F1–F8
  - distal ring relabelled F9–F16
- The previous schematic Figure 1 is archived in `_archive_invalid/fig1_schematic_replaced_2026-09-23/`.
- The caption was rewritten (in blue) to describe panels A–C, and it adds the caveats that:
  - the muscle drawings are general anatomy only
  - the electrodes are drawn schematically
  - panel C does not show which ranking performed better
- Open issues in the artwork itself, which need editing in Canva:
  - text prints at about 5 pt, below the journal's 8 pt minimum
  - the labels "Flexor Group (FCR/FDS)" and "Extensor Group (EDC/ECU)" suggest muscle mapping
  - the word "Reliable" and the phrase "Not stability assessment" in panel C imply that SR-CFA is better, which contradicts the negative H3 result
  - the Myo-style pods do not look like discrete electrodes
