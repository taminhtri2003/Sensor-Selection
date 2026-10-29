# Novelty review (interim) — what is actually new here

Status: **interim**. Based on targeted searching of the closest methodological work; the full
`literature/literature_matrix.csv` (target 60–100 papers) is not yet built. The conclusions below
already constrain the framing and are recorded now, before the method is frozen, so that the
title cannot drift toward a claim the literature does not support.

---

## 1. What is already established

| Established | Representative work |
|---|---|
| sEMG hand-gesture recognition with handcrafted TD features + tree/SVM classifiers | extensive; NinaPro and GRABMyo benchmark literature |
| sEMG channel reduction | Qu et al. 2021 (multitask sparse representation + mRMR); PCS-EMGNet (learned channel compression); HD-EMG electrode-subset work |
| Attribution-guided channel reduction in *biosignals* | SHAP-AAD (DeepSHAP-guided channel reduction for **EEG** auditory attention) |
| Nested CV with feature/channel selection strictly inside inner folds | Consensus-features nested CV (Bioinformatics 2020); `nestedcv`; channel-selected nested CV for EEG Parkinson's detection |
| Stability selection — aggregating selections across resamples by frequency | Meinshausen & Bühlmann lineage; bootstrap stability selection; 2D stability selection |
| **Stability-aware attribution ranking** | **RoSHAP (2026)**; robust rank aggregation; "Shaping Up SHAP"; attribution-separability stability metrics |
| Explanation instability as a recognised problem | RoSHAP; SHAP fragility under collinearity; attribution variance under distribution shift |

## 2. The closest prior work, and why it matters

**RoSHAP** is the nearest neighbour to the proposed SR-CFA score. It ranks features by

```
RoSHAP_j = (1 - P0_j) * m_j^2 / s_j
```

where `m_j` is the median magnitude of nonzero attributions and `s_j` their standard deviation
across bootstrap runs — explicitly rewarding features that are "active, strong, and stable".

That is the same *idea* as `Q_c(λ) = A_c − λ·U_c`: reward magnitude, penalise instability. The
functional form differs (ratio versus penalised subtraction, and λ gives an explicit tunable
trade-off where RoSHAP fixes one), but **it would be false to present stability-regularised
attribution ranking as a new concept.**

Where RoSHAP does *not* reach:

- its resampling unit is a **bootstrap sample**, not a **held-out subject** — it measures stability
  under data perturbation, not stability across people;
- it is evaluated on genomics, molecular, WiFi-fingerprint and image data — **no biosignals, no
  EMG, no channel/sensor selection**;
- it has **no cross-session or multi-day dimension**;
- it does not address subject-independent deployment at all.

## 3. What is therefore genuinely left

Stated conservatively, the defensible contributions are:

1. **Subject-level cross-fitted attribution.** Attributions are computed on inner-fold *held-out
   participants*, so the stability being measured is stability of channel importance **across
   people** — the axis that actually governs whether one fixed electrode layout can serve unseen
   users. This differs from bootstrap-resample stability, which perturbs samples drawn from the
   same people.
2. **A session-level stability term.** GRABMyo's three-day protocol permits `U^session_c` alongside
   `U^subject_c`. No work found combines attribution magnitude with both a between-subject and a
   between-session instability penalty. This is the most distinctive element.
3. **Application to sEMG sensor selection under strict nested validation**, with a prespecified
   non-inferiority margin and participant-level inference — as opposed to visual "plateau" reading
   of a sensor curve, which is the norm in this literature.
4. **External methodological replication** on a second dataset with different hardware.

## 4. What must NOT be claimed

- ❌ "We introduce stability-regularised attribution." — RoSHAP and the stability-selection
  literature precede it.
- ❌ "First application of SHAP to EMG channel selection." — not verified, and SHAP-guided channel
  reduction already exists for EEG.
- ❌ Framing SR-CFA as a general-purpose XAI advance. The contribution is **application and
  validation**, not a new attribution method.
- ❌ Any title implying a novel explainability algorithm.

## 5. Consequence for framing

The paper should be positioned as a **rigorous evaluation study in a domain where the validation
has been weak**, not as a methods paper. The strongest honest pitch is:

> Does explainability-guided sparse sensor selection survive the conditions a real deployment
> imposes — an unseen user, a different day, a second dataset — and does the stability of the
> explanation matter more than its magnitude?

This framing survives every outcome of the decision gates in `EXECUTION_PLAN.md`, including the
negative ones, which the "novel method" framing would not.

## 6. Pre-existing evidence that argues against the expected result

Worth recording before results arrive: prior EMG channel-selection work reports that **no
consistent pattern of selected channels was observed across subjects** (Liu & Zhou, incomplete
spinal-cord-injury cohort). Independently, the attribution-stability literature reports that SHAP
rankings are fragile under collinearity — and the 10 features per channel used here are strongly
collinear by construction (MAV/IEMG/RMS/VAR are near-redundant amplitude measures).

Both point the same way: cross-subject ranking agreement may be **low**. If it is, the honest
paper is contingency framing 5 — attribution instability limits fixed sparse electrode layouts —
and that is a more interesting result than another "k channels suffice" claim.

## 7. Still to do before this review is final

- Build `literature/literature_matrix.csv` (60–100 papers, 26 columns).
- Deep mini-reviews of the 15–25 closest studies.
- Backward/forward citation sweep of Qu et al. 2021, SHAP-AAD, RoSHAP, and the GRABMyo data
  descriptor.
- Confirm whether any sEMG paper already combines XAI channel selection with cross-session
  stability; if one does, the contribution reduces to item 3–4 above and the framing must narrow
  again.

---

## 8. Closest-threat papers read in full — verdicts

Updated as each is verified. A paper is only cleared once its full text has been read; abstract-level
screening is not sufficient to defend a novelty claim.

### L024 — Cisotto et al. 2022, "Feature stability and setup minimization for EEG-EMG-enabled monitoring systems"

Flagged as the closest threat because it pairs *stability* with *setup minimization*. Full text read.
**Verdict: does not pre-empt this study.**

| Dimension | Cisotto et al. | This study |
|---|---|---|
| Signals | EEG (32 ch) + EMG (5 bipolar), coherence between them | sEMG only, 16 channels |
| Selection target | **MSC features** (sensor-pair x frequency-band) | **physical channels/electrodes** |
| "Setup minimization" | reduces feature count 1760 -> 80-200; **does not reduce hardware** | reduces the number of electrodes actually required |
| Stability notion | selection **frequency** >= 70% across CV repetitions (Meinshausen lineage) | attribution **magnitude penalised by across-subject/session variance** |
| Validation | repeated 10-fold holdout, **within-subject** (authors acknowledge the limitation) | leave-one-subject-out, 43 participants |
| Sessions | 1 | 3, >= 7 days apart |
| Attribution | none | cross-fitted TreeSHAP |
| Equivalence testing | none | prespecified non-inferiority margin |
| Subjects | 8 | 43 (+10 external) |

The overlap is thematic, not substantive: its "setup minimization" is a feature-count reduction that
leaves the hardware untouched, and its stability is selection frequency rather than attribution
variance. It should be cited as prior art for stability-driven reduction, and the distinction above
stated plainly rather than glossed.

### Still to verify in full

- L003 Qu et al. 2021 — the closest *sensor-reduction* comparator
- L004 SHAP-AAD — the closest *attribution-guided channel reduction* comparator (EEG)
- L014 HD-EMG electrode subsets under shift
- L021 label-free cross-session adaptation

Until these four are read in full, the novelty statement in section 3 remains provisional.

### L004 — SHAP-AAD, "DeepSHAP-Guided Channel Reduction for EEG Auditory Attention Detection"

**Verdict: closest attribution-guided channel-reduction comparator, but PARTIALLY VERIFIED ONLY.**

What is established from the abstract: DeepSHAP ranks channel importance for a CNN over topographic
alpha-power maps on the DTU EEG dataset; 32 of 64 channels give **79.21% vs 81.06%** for the full
array, described as "comparable"; 8 channels are called "satisfactory".

What could **not** be determined from the abstract or the retrievable PDF text: the validation
scheme, whether it is subject-independent, and — critically — **whether the SHAP channel ranking is
computed inside training folds or once over all data**. The arXiv PDF returned by the fetch tool is
password-protected and could not be read directly.

This is recorded as *unverifiable*, not as *absent*. It would be unfair, and unsafe, to assert that
this paper leaks selection or lacks subject-independence when the text simply was not obtainable.
The matrix row says "unverifiable" for those fields and the review depth is marked partial.

What is safe to say, and useful for our motivation: a **1.85 percentage-point** difference is
declared "comparable" with no confidence interval and no prespecified margin. That is precisely the
eyeball-comparability practice a non-inferiority framework replaces — and it is worth citing as the
motivating example rather than as a flaw of that specific paper, since the practice is the field
norm rather than an individual lapse.

**Action before submission:** obtain the full text (institutional access or author copy) and resolve
the leakage and validation questions. If it turns out to perform nested subject-independent
selection, contribution item 3 narrows and the framing must be adjusted.

### L003 — Qu et al. 2021, "Reduce Surface Electromyography Channels ... MTSR and mRMR"

Flagged as the closest **sensor-reduction** comparator. Full text read.
**Verdict: does not pre-empt this study; it is the clearest example of the gap.**

Correction to our own earlier record: this paper does **not** use NinaPro, as the search snippet
implied and as our matrix initially stated. It uses the Chan & Green myoelectric toolbox dataset —
30 subjects, 8 electrodes, 7 gestures, single session. The matrix row has been corrected. This is
exactly why full-text verification is required before a novelty claim rests on a comparison.

| Dimension | Qu et al. 2021 | This study |
|---|---|---|
| Validation | 5-fold CV, **within-subject** | leave-one-subject-out, 43 participants |
| Channels | 8 -> 3 retained | 16 -> k, swept 1..16 |
| Reported result | **98.68% accuracy** (7 classes, within-subject) | 0.542 Macro-F1 (16 classes, subject-independent) |
| Uncertainty | **none** — no CIs, no SDs, no significance tests | participant cluster bootstrap, 10,000 resamples |
| Choosing k | ranking occurrence counts, by inspection | prespecified non-inferiority margin, frozen before results |
| Selection nesting | not stated; possible leakage | nested by construction, asserted in code |
| Sessions / external dataset | 1 / none | 3 / DB5 |

**The 98.68% must never be placed beside our 0.542.** They measure different things: a 7-class
within-subject problem where the model has seen the test subject, versus a 16-class problem on a
person the model has never seen. Reporting them side by side would imply our method is fourteen
times worse than the state of the art, when in fact the two numbers are not comparable at all.
This is precisely the trap the study brief warns about in section DA, and the related-work table
must carry the validation scheme in its own column so the difference is unmissable.

Its genuine value to us: it demonstrates that channel reduction *is* achievable in principle, and
it exemplifies the three gaps this study targets — no subject-independence, no uncertainty
quantification, and a sensor count chosen by inspection rather than a prespecified criterion.

## 2026-09-22 review update

The matrix now exists, but registry/title failures in its audit mean it should be treated as a
scoping resource, not a completed systematic review. The manuscript bibliography was rebuilt
from verified identifiers; the matrix is not permission to cite its flagged entries.
The nearest stability-aware attribution work, RoSHAP, is confirmed at
https://arxiv.org/abs/2605.15154. Neither subtracting a variability penalty nor robust attribution
aggregation should be claimed as a new general concept. The participant-level extension is a
post-hoc methodological check of this study's aggregation unit; its value must be demonstrated
on complete held-out participant results, not inferred from the formula.
