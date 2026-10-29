# Physiology / signal-acquisition reviewer audit (2026-09-21)

| Topic | Manuscript statement | Evidence | Status |
|---|---|---|---|
| Montage | 2 rings × 8 monopolar forearm electrodes, 2 cm apart, electrode j aligned with j+8 | `Electrodelocation.pdf` ("2 × 8 channels forearm setup", 2 cm inter-ring); `reports/grabmyo_electrode_geometry.md` | OK |
| Ring orientation | Not stated (which ring is distal is not documented) | The previous draft and figures asserted "distal F1–F8"; no source found | Removed |
| Circumference / spacing | 24.1 ± 2.3 cm; about 3.0 cm arc spacing | `subject-info.csv`, 43 participant rows (summary rows excluded) | OK (macro) |
| Sessions | "three different days" | dataset readme | OK. The previous "≥ 7 days" claim was unsupported and removed |
| Device | EMGUSB2+, OT Bioelettronica, 2048 Hz | dataset readme | OK |
| Mains | 50 Hz notch | measured band-power ratio 10.35 vs 0.62 (`reports/signal_properties_audit.md`) | OK |
| Band-pass | 20–450 Hz for 2048 Hz; 10–95 Hz for DB5 (Nyquist 100 Hz) | scripts 20 / 33 | OK |
| DB5 units | 8-bit integer codes, not mV | `reports/db5_signal_audit.md` | OK; the threshold is expressed in ADC units |
| Count thresholds | 1e-2 mV monopolar, 5e-3 mV bipolar, 7 ADC DB5, each about 1.15× the median absolute first difference | extraction reports; bipolar SSC medians 17–69 after the fix | OK; the pooled-data derivation is disclosed |
| IEMG = 512 × MAV | 250 ms × 2048 Hz = 512 samples | arithmetic | OK |
| Muscle mapping | Declined; positional statements only | Surface EMG records compound activity; circumferential index-to-muscle mapping is not documented | OK. The previous "flexor carpi radialis = Ch 1/9" claims were removed |
| Bipolar derivation | B_j = F_j − F_{j+8}, longitudinal pairs 2 cm apart | geometry report | OK; described as a derived montage, not a physical bipolar electrode |
| Population | able-bodied only | both datasets | Stated; no amputee or clinical claim ("novel amputees" in the previous draft removed) |
| Cross-session interpretation | No claim that donning/doffing is harmless | CS design is cross-subject | OK |
