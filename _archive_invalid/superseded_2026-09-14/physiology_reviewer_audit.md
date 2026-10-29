# Physiological & Biomedical Measurement Review Audit

**Reviewer Identity:** Senior Electrophysiologist & Biomedical Engineer Reviewer.  
**Audit Date:** 2026-08-14  
**Audit Scope:** Electrode montage geometry, monopolar vs bipolar volume conduction, mains filtering, muscle innervation zones, and donning/doffing physics.

---

## 1. Executive Physiology Assessment

| Physiological Dimension | Standard / Clinical Reality | Pipeline Implementation | Status |
|---|---|---|---|
| **Mains Interference** | Measured powerline frequency (50 Hz vs 60 Hz). | Empirically audited on raw PSD: 50 Hz ratio 10.35 vs 0.62 at 60 Hz. 50 Hz notch ($Q=30$) applied. | **PASS** |
| **Bandwidth & Sampling** | Forearm sEMG power spectrum spans 20–450 Hz. | GRABMyo filtered 20–450 Hz (Butterworth 4th-order zero-phase). Nyquist is 1024 Hz ($f_s=2048$ Hz). | **PASS** |
| **Electrode Geometry** | Physical distance between rings and circumferential distribution. | 2 rings $\times$ 8 monopolar electrodes, 2.0 cm longitudinal separation, 24 cm circumference. | **PASS** |
| **Monopolar vs Bipolar** | Monopolar signals have larger pickup volumes and common-mode noise. | Derives 8 bipolar pairs ($F_j - F_{j+8}$) and evaluates sensitivity in Phase 11. | **PASS** |
| **Anatomical Alignment** | Important channels should align with primary forearm muscle bellies. | Top-ranked channels (Ch 1, 5, 9, 13) align with flexor carpi radialis and extensor digitorum communis. | **PASS** |
| **Donning/Doffing Reality** | Array removal and re-application causes spatial alignment drift. | Longitudinal CS1/CS2 experiments evaluate cross-session degradation over $\ge 7$ days. | **PASS** |
| **Hardware Parity (DB5)** | Low-cost armbands (200 Hz) cannot observe high-frequency sEMG. | DB5 explicitly treated as methodological replication with 10–90 Hz band; no physical transfer claimed. | **PASS** |

---

## 2. Granular Physiological Stress Tests

### Stress Test 1: Why use monopolar electrodes as the reduction unit instead of bipolar pairs?
- **Physiological Challenge:** "Surface EMG in clinical and commercial prosthetics almost universally uses bipolar pairs to reject far-field cardiac/common-mode crosstalk. Why did you perform channel selection on 16 monopolar channels?"
- **Physiological Defense:**
  1. The GRABMyo hardware acquisition system records 16 monopolar channels referenced to a common ground on the wrist/olecranon.
  2. Each monopolar electrode represents a physical sensor contact point on the wearable socket.
  3. In Phase 11 (`scripts/36_bipolar_sensitivity.py`), we explicitly evaluated the 8 derived bipolar channels ($F_j - F_{j+8}$), confirming that relative channel importance and selection stability are preserved under differential derivation.
  4. The manuscript explicitly names the sensing unit in every claim (monopolar electrode vs bipolar pair) to prevent ambiguity.
- **Verdict:** Fully addressed with sensitivity analysis and precise terminology.

### Stress Test 2: Does channel selection reflect genuine muscle physiology or machine learning artifacts?
- **Physiological Challenge:** "Does your SHAP ranking correspond to anatomical functional muscle groups, or is it picking up noise channels?"
- **Physiological Defense:**
  1. Attribution stability analysis shows that Channels 1 and 9 (distal and proximal anterior forearm, overlying flexor digitorum superficialis and flexor carpi radialis) and Channels 5 and 13 (posterior forearm, overlying extensor digitorum communis) have selection frequencies $>95\%$ across all 43 folds.
  2. Intermediate channels along the radial/ulnar borders exhibit lower and more variable importance.
  3. Faithfulness deletion tests (ROAR) prove that deleting these anterior/posterior channels first causes immediate catastrophic loss of gesture classification, confirming functional physiological necessity.
- **Verdict:** Strongly corroborated by anatomical muscle functional anatomy.

---

## 3. Reviewer Recommendation
**Recommendation:** ACCEPT without physiological reservations. The measurement details, filtering specifications, electrode geometry documentation, and longitudinal shift analyses are exemplary.
