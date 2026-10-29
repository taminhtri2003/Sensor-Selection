# Numerical Consistency Audit & Cross-Checking Report

**Audit Date:** 2026-09-14  
**Audited Items:** Table 4 vs Table 5, Abstract LCB, ROAR monotonicity, Bipolar non-inferiority, NinaPro DB5 non-inferiority boundary.

---

## 1. Summary of Investigated Discrepancies & Verdicts

| Item | Problem / Discrepancy Audited | Finding / Root Cause | Resolution & Canonical Value |
| :--- | :--- | :--- | :--- |
| **1A: Table 4 vs Table 5** | Same algorithm ($\text{SR-CFA}_{\lambda=0.50}$) has different numbers ($0.528$ vs $0.481$ at $k=12$). | Two different training budgets: Table 4 is 300 trees, full $\sim 550\text{k}$ training data; Table 5 is 50 trees, $150\text{k}$ subsample (designed for tractable 500-draw random comparisons). | **Keep both, but clarify protocol explicitly.** Table 4 is primary headline curve; Table 5 is matched-budget relative selector benchmark. |
| **1B: Abstract LCB** | Abstract stated $\text{LCB} = -0.0152$, while Table 4 and `\OptimalKLCB` stated $\text{LCB} = -0.0160$. | Stale hardcoded text from an earlier partial bootstrap draft. Canonical $B=10{,}000$ cluster bootstrap gives exactly $-0.0160$. | **Correct Abstract to $-0.0160$** via `\OptimalKLCB`. |
| **1C: ROAR Ordering** | Manuscript claimed $\text{F1}_{\text{top}} < \text{F1}_{\text{random}} < \text{F1}_{\text{bottom}}$, but $k=12$ data shows $\text{F1}_{\text{top}} (0.488) > \text{F1}_{\text{random}} (0.478)$. | Partial faithfulness: Top vs Bottom is strictly satisfied across all $k$ ($p < 0.007$). Strict 3-way ordering holds at $k=6$ ($p < 0.012$), but at $k=12$ (only 4 sensors removed), remaining 12 channels retain high redundancy. | **Revise text to "partial attribution faithfulness"**; report exact paired differences, 95% CIs, and Holm-adjusted $p$-values. |
| **1D: Bipolar Non-Inferiority** | Previous discussion claimed $k^* = 6$ pairs are non-inferior. | Audited bootstrap: At $k=6$, mean drop is $\Delta = -0.0373$ ($\text{LCB} = -0.0453 \le -0.020$, FAILS). At $k=7$, mean drop is $\Delta = -0.0146$ ($\text{LCB} = -0.0191 > -0.020$, PASSES). | **Correct minimal non-inferior bipolar subset to $k^* = 7$ pairs** (not 6). |
| **1E: NinaPro DB5 Boundary** | Reported $\text{LCB} \approx -0.0200$ with decision threshold $-0.020$. Insufficient precision to verify pass/fail. | 6-decimal cluster bootstrap computation yields: $\text{Mean } \Delta = -0.013029$, $\text{LCB}_{95\%} = -0.020254$, $\text{UCB}_{95\%} = -0.006212$. Since $-0.020254 \le -0.020000$, it strictly fails non-inferiority. | **Report as a borderline replication result** ($\text{LCB} = -0.0203 \le -0.020$). Do not claim full non-inferiority on NinaPro DB5. |

---

## 2. Canonical Participant-Level Recomputed Tables

### 2A. Primary Sparse Sensor Curve on GRABMyo ($N=43$, Full Budget: 300 trees, $\sim 550\text{k}$ windows)
- $k=16$ (Reference): Macro-F1 = $0.541 \pm 0.084$
- $k=15$: Macro-F1 = $0.538 \pm 0.083$, $\Delta = -0.0037$, 95% CI $[-0.0057, -0.0019]$ -> Non-Inferior
- $k=14$: Macro-F1 = $0.535 \pm 0.083$, $\Delta = -0.0060$, 95% CI $[-0.0081, -0.0039]$ -> Non-Inferior
- $k=13$: Macro-F1 = $0.530 \pm 0.083$, $\Delta = -0.0109$, 95% CI $[-0.0133, -0.0085]$ -> Non-Inferior
- **$k=12$ ($k^*$): Macro-F1 = $0.528 \pm 0.084$, $\Delta = -0.0133$, 95% CI $[-0.0160, -0.0106]$ -> Non-Inferior (Minimal $k^*$)**
- $k=11$: Macro-F1 = $0.520 \pm 0.084$, $\Delta = -0.0212$, 95% CI $[-0.0253, -0.0170]$ -> FAILS ($\text{LCB} \le -0.020$)
- $k=8$: Macro-F1 = $0.505 \pm 0.085$, $\Delta = -0.0359$, 95% CI $[-0.0430, -0.0283]$ -> FAILS
- $k=6$: Macro-F1 = $0.480 \pm 0.084$, $\Delta = -0.0610$, 95% CI $[-0.0713, -0.0507]$ -> FAILS
- $k=4$: Macro-F1 = $0.397 \pm 0.071$, $\Delta = -0.1440$, 95% CI $[-0.1583, -0.1305]$ -> FAILS

### 2B. ROAR Faithfulness Verification ($N=43$)
| Retained $k$ | Arm Top | Arm Random | Arm Bottom | Top vs Bottom Diff [95% CI] | $p_{\text{Holm}}$ | Top vs Random Diff [95% CI] | $p_{\text{Holm}}$ |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| $k=4$ | $0.372 \pm 0.062$ | $0.366 \pm 0.059$ | $0.397 \pm 0.071$ | $-0.0245$ $[-0.0396, -0.0091]$ | $0.0066$ | $+0.0068$ $[-0.0034, +0.0168]$ | $0.2322$ |
| $k=6$ | $0.399 \pm 0.066$ | $0.416 \pm 0.068$ | $0.480 \pm 0.083$ | $-0.0810$ $[-0.0970, -0.0643]$ | $<0.0001$ | $-0.0166$ $[-0.0267, -0.0063]$ | $0.0116$ |
| $k=8$ | $0.435 \pm 0.071$ | $0.445 \pm 0.071$ | $0.505 \pm 0.085$ | $-0.0700$ $[-0.0869, -0.0529]$ | $<0.0001$ | $-0.0106$ $[-0.0216, +0.0007]$ | $0.1707$ |
| $k=12$ | $0.488 \pm 0.079$ | $0.478 \pm 0.077$ | $0.528 \pm 0.084$ | $-0.0404$ $[-0.0488, -0.0320]$ | $<0.0001$ | $+0.0097$ $[+0.0025, +0.0172]$ | $0.0933$ |

### 2C. Bipolar Sensitivity Analysis ($N=43$)
- Full 8 pairs baseline: Macro-F1 = $0.4708 \pm 0.0902$
- $k=8$ pairs: Macro-F1 = $0.4716 \pm 0.0902$, $\Delta = +0.0008$ $[-0.0008, +0.0024]$ -> Non-Inferior
- **$k=7$ pairs ($k^*$): Macro-F1 = $0.4563 \pm 0.0852$, $\Delta = -0.0146$ $[-0.0191, -0.0099]$ -> Non-Inferior ($\text{LCB} > -0.020$)**
- $k=6$ pairs: Macro-F1 = $0.4336 \pm 0.0828$, $\Delta = -0.0373$ $[-0.0453, -0.0294]$ -> FAILS Non-Inferiority ($\text{LCB} \le -0.020$)

### 2D. NinaPro DB5 External Methodological Replication ($N=10$)
- Full 16 channels: Macro-F1 = $0.2806 \pm 0.0988$
- $k=12$ channels: Macro-F1 = $0.2681 \pm 0.0923$, $\Delta = -0.013029$, 95% CI $[-0.020254, -0.006212]$ -> Borderline, technically FAILS non-inferiority ($\text{LCB} \le -0.020000$).
