# Preliminary attribution findings — PROVISIONAL, 10 of 43 outer folds

**Status: not a result.** Based on `artifacts/rankings/cross_fitted_scores.csv` while P2 is still
running (10/43 outer folds complete). Recorded now because it already bears on the study's
direction, and because writing down an expectation before the full run finishes is the only way to
tell later whether the conclusion followed the evidence or the evidence was read to fit a
conclusion.

## What the numbers say so far

Mean normalised attribution `A_c` and within-outer-fold instability `U_c`, averaged over 10 outer folds:

| channel | A_c | U_c | U/A |
|---|---|---|---|
| 4 | 0.0902 | 0.0016 | 1.8% |
| 6 | 0.0887 | 0.0010 | 1.1% |
| 14 | 0.0851 | 0.0012 | 1.4% |
| 7 | 0.0751 | 0.0014 | 1.8% |
| 8 | 0.0730 | 0.0018 | 2.5% |
| 10 | 0.0698 | 0.0018 | 2.5% |
| … | … | … | … |
| 12 | 0.0416 | 0.0007 | 1.6% |
| 9 | 0.0410 | 0.0009 | 2.2% |

Uniform attribution would be 1/16 = 0.0625 per channel.

## Three observations

### 1. Attribution is stable — my stated prediction was wrong

I predicted low cross-subject ranking agreement, citing Liu & Zhou (no consistent channel
selection across subjects) and the SHAP-fragility-under-collinearity literature. Across the first
10 outer folds the top-4 set is **{4, 6, 7, 14} without exception**, and `U_c` is only **1–3% of
`A_c`**. That prediction is not surviving contact with the data, and the write-up must say so
rather than quietly dropping it.

**Important qualification on what "stable" means here.** `U_c` is the dispersion of channel
importance across *inner folds*, and each inner fold's importance is averaged over ~20,000 windows
drawn from a group of 8–9 held-out participants. Averaging over a group smooths individual
variation. So this measures **stability of group-averaged attribution**, not agreement between
individual people. Those are different claims, and only the first is currently supported. Measuring
per-subject attribution variability requires attributing one participant at a time and is a
separate analysis that should be added before any claim about individual consistency.

### 2. Attribution is diffuse, which argues *against* strong sensor reduction

| | observed | uniform expectation |
|---|---|---|
| share of attribution held by top 4 of 16 channels | **34.0%** | 25% |
| share held by bottom 8 of 16 | **39.6%** | 50% |
| ratio of most- to least-important channel | **2.2x** | 1.0x |

Concentration is real but weak. If a handful of electrodes carried the gesture information, the top
4 would hold far more than a third of it. Instead the bottom half still carries about 40%.

This is the single most consequential preliminary observation, because the study's headline
hypothesis is that a small subset suffices. Diffuse importance predicts a **gently sloping sensor
curve with no sharp plateau**, and therefore a real possibility that no k < 16 clears the
prespecified 0.02 margin — contingency framing 4 in the execution plan. That must not be softened
by relaxing the margin afterwards.

### 3. Stability regularisation will probably do nothing

`Q_c(λ) = A_c − λ·U_c`, with λ ∈ {0, 0.25, 0.5, 1.0}. The largest possible penalty is
1.0 × 0.0018 ≈ 0.0018, while gaps between adjacent channels in `A_c` are typically 0.005–0.05.
**The penalty is an order of magnitude too small to reorder anything but near-ties.**

So gate G2 — does λ>0 beat λ=0 — looks likely to come back null, which sends the paper to
contingency framing 2: SR-CFA collapses to mean-SHAP, the acronym leaves the title, and the
contribution becomes the evaluation rather than the score.

That is not a failure of the experiment. A stability penalty is only useful when attribution is
unstable; finding that it is stable at group level is a legitimate answer, and one this design can
support precisely because the penalty was defined and frozen before the data were seen.

## What would change these readings

- The remaining 33 outer folds.
- The inner-fold agreement analysis (`scripts/29_stability.py`), which uses disjoint held-out
  subject groups rather than the ~98%-overlapping outer folds and is the honest stability estimate.
- Per-subject attribution, which is not yet computed and is required before any claim about
  agreement between individuals.
- The sensor curve itself (P3), which measures what actually matters: whether performance survives
  channel removal, not whether attribution says it should.

Attribution concentration and classification performance are related but not the same thing. A
diffuse attribution profile makes a flat sensor curve *plausible*, not certain — redundancy between
channels could still allow removal without loss. P3 decides it.
