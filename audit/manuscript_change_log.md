# Manuscript Change Log & Modification Plan

**Audit Date:** 2026-09-14  
**Audited Document:** Master Elsevier 5p Double-Column Manuscript (`manuscript/sections/*.tex`, `main_elsevier.tex`, `main.tex`)  

---

## 1. Concrete Changes by Manuscript Section

### Frontmatter & Abstract (`main_elsevier.tex`, `main.tex`)
1. **Abstract LCB Correction:** Replace stale hardcoded `-0.0152` with canonical macro `\OptimalKLCB` (`-0.0160`).
2. **Preregistration Language:** Replace "pre-registered non-inferiority protocol" with "pre-specified statistical analysis plan".
3. **Longitudinal Phrasing:** Replace obsolete "degrades by 12--14% (paired drop of 0.067--0.076)" with verified multi-day training benefit: "multi-day training exposure significantly improves cross-session accuracy by +0.0210 Macro-F1 ($p < 0.001$), demonstrating that multi-session data partially mitigates donning/doffing drift".
4. **Anatomical Phrasing:** Tone down "primary anatomical axes" to "primary flexor and extensor compartments".
5. **NinaPro Framing:** State NinaPro DB5 as a methodological replication ($N=10$) with borderline non-inferiority ($\text{LCB} = -0.0203$).

### Section 01: Introduction (`manuscript/sections/01_introduction.tex`)
1. **Flow & Motivation:** Follow the 6-paragraph logical progression mandated by Phase 23:
   - Para 1: sEMG neural interfaces and wearable/prosthetic motivation.
   - Para 2: Why reducing physical sensors matters (volume, power, contact stability).
   - Para 3: Gap 1 — User-dependent vs user-independent evaluation. State clearly that user-dependent validation is valid for personalized systems, but does not prove population generalization.
   - Para 4: Gap 2 — Collinear biosignals induce attribution instability across individuals.
   - Para 5: Gap 3 — Heuristic visual plateaus lack formal statistical non-inferiority control.
   - Para 6: Gap 4 — Longitudinal donning/doffing degradation and lack of external replication.
2. **Action-Oriented Contributions:** Formulate 4 clear contributions without hype or marketing buzzwords.
3. **Real-time Controller Limitation:** Note that 250 ms windows and zero-phase filtering represent an offline benchmark.

### Section 02: Related Work (`manuscript/sections/02_related_work.tex`)
1. **Terminology Clarification:** Explain collinearity, spatial covariate shift, and donning/doffing on first use.
2. **Table 1:** Maintain the comprehensive literature comparison table comparing Phinyomark, Al-Timemy, Qu, Cisotto, Visani, Campbell, Kaufmann, He with our study. Ensure all citation keys are valid.

### Section 03: Methods (`manuscript/sections/03_methods.tex`)
1. **Subsection Structure:** Organize cleanly into subsections 3.1 to 3.17 as requested in Phase 24.
2. **Geometry Clarification:** State forearm circumference as $24.10 \pm 2.27\text{ cm}$; clarify that $3.0\text{ cm}$ circumferential spacing is derived from cohort mean circumference.
3. **Feature Thresholds:** Document exact fixed thresholds ($T = 0.01\text{ mV} = 10\ \mu\text{V}$) rather than theoretical adaptive thresholds.
4. **Collinearity Note:** Acknowledge that $\text{IEMG} = T \cdot \text{MAV}$ and report feature redundancy sensitivity ($|\Delta| \le 0.0036$).
5. **Multiclass TreeSHAP Formulation:** Formally state the exact mathematical reduction:
   $$\Phi_{i, c} = \frac{1}{G \cdot F} \sum_{g=1}^G \sum_{f=1}^F |\phi_{i, g, c, f}|$$
   and inner cross-fitting aggregation $A_c = \text{median}_{j} I_{j, c}$, $U_c = \text{MAD}_j I_{j, c}$, $Q_c(\lambda) = A_c - \lambda U_c$.
6. **Fixed Population Layout Protocol:** Formulate the development/holdout validation protocol.
7. **Sequential Testing Multiplicity:** Justify downward fixed-sequence testing from $k=15 \to 1$ controlling familywise error rate.

### Section 04: Results (`manuscript/sections/04_results.tex`)
1. **Subsection Order:** Follow Phase 25 structure (4.1 Dataset summary, 4.2 Full-channel baseline, 4.3 Sparse curve & $k^*=12$, 4.4 Selection baselines, 4.5 Fixed layout generalization, 4.6 Attribution stability, 4.7 ROAR partial faithfulness, 4.8 Cross-session robustness, 4.9 NinaPro DB5 replication, 4.10 Sensitivity analyses).
2. **Table 5 Clarification:** Explicitly label Table 5 as evaluated under matched 50-tree, 150k-sample comparison budget, resolving Table 4 vs Table 5 contradiction.
3. **ROAR Reporting:** Report partial faithfulness with exact paired differences, 95% CIs, and Holm-adjusted $p$-values.
4. **Bipolar Correction:** Report $k^* = 7$ pairs as the minimal non-inferior bipolar subset ($\text{LCB} = -0.0191 > -0.020$), correcting the previous $k=6$ claim.
5. **NinaPro DB5 Precision:** Report 5 decimals ($\text{LCB} = -0.02025 \le -0.02000$), describing it as a borderline fail.
6. **Cross-Session Results:** Report CS1 sessions ($0.492 \to 0.528 \to 0.510$) and CS2 multi-day gain ($+0.0210$, $p = 1.35 \times 10^{-7}$).
7. **Fixed Population Layout Results:** Report consensus 12-channel performance on 21 held-out test subjects ($\Delta = -0.0124$, $\text{LCB} = -0.0179 > -0.0200$, non-inferior).

### Section 05: Discussion (`manuscript/sections/05_discussion.tex`)
1. **Scientific Hierarchy:** Follow evidence hierarchy (Finding -> Subject-independent reality -> Stability regularization role -> Longitudinal shift -> NinaPro replication nuances -> Engineering guidelines -> Transparent limitations).
2. **Tone Down Anatomical Claims:** Use "circumferential positions consistent with flexor/extensor muscle groups" rather than claiming specific muscle localization.
3. **Honest Limitations:** Expand on healthy vs amputee subjects, offline vs online causal control, 250 ms windows, NinaPro $N=10$ sample size. Do not overemphasize SVM 40k subsampling as the primary limitation.

### Section 06: Conclusion (`manuscript/sections/06_conclusion.tex`)
1. Concise 3-paragraph summary:
   - Para 1: Main finding ($k^*=12$ saves 25% sensors with non-inferiority).
   - Para 2: Attribution stability and fixed layout generalization.
   - Para 3: Multi-day findings and translational roadmap.
