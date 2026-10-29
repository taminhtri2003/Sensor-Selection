# NinaPro DB5 — empirical signal audit

Measured on movement periods (restimulus > 0) of 10 E1 recordings, unfiltered.

## Acquisition

- Sampling rate: **200 Hz** -> Nyquist **100 Hz**
- The GRABMyo band (20-450 Hz) is **not representable** here; a DB5-specific band is required.

## Amplitude

- median |x|: 4
- 99th percentile |x|: 59.5
- median |diff(x)|: 6

## Spectrum

- Peak power at **88.7 Hz**
- 95% of power below **94.9 Hz**; 99% below **97.7 Hz**
- Fraction of total power retained by a high-pass at:
  - 5 Hz: 99.2%
  - 10 Hz: 97.5%
  - 15 Hz: 95.6%
  - 20 Hz: 93.7%

## Powerline

| candidate | band-power ratio vs 10-95 Hz median |
|---|---|
| 50 Hz | 0.26 |
| 60 Hz | 0.65 |

No powerline peak stands out (both ratios near 1). The Myo armband applies its own hardware filtering, so **no notch filter is applied to DB5**. Adding one would remove genuine EMG power in a band where little interference exists.

## Chosen DB5 preprocessing

Stated as a deliberate difference from GRABMyo, not an oversight:

- band-pass **10-95 Hz**, 4th-order Butterworth, zero-phase
- notch: see above
- window 250 ms = **50 samples** at 200 Hz, 50% overlap

The 50-sample window is short. MNF/MDF estimated from 50 samples are coarse (frequency resolution 4 Hz), which must be acknowledged when comparing feature importance between datasets.

---

## Addendum: quantisation and hardware band-limiting (manual verification)

Two properties found by inspecting the raw arrays directly. Both constrain what the DB5
replication can legitimately claim.

### DB5 EMG is 8-bit quantised, in arbitrary units

```
dtype float32, min -128.0, max 127.0
exactly 256 unique values, all integers
sensor field: "Double Myo"
```

The values are stored as float32 but are integer ADC codes from the Myo armband, **not
millivolts**. GRABMyo, by contrast, is calibrated in mV with median |x| = 2.3e-2 mV.

Consequences:

1. **Feature thresholds must be derived separately per dataset.** The ZC/SSC/WAMP threshold of
   1e-2 mV chosen for GRABMyo is meaningless against DB5's integer scale, where median |diff| = 6
   ADC units. Applying the GRABMyo threshold unchanged would put it ~6 orders of magnitude below
   the signal, recreating exactly the saturation defect found in the GRABMyo features.
   The DB5 threshold is set from its own measured amplitude distribution.
2. **Amplitude features are not numerically comparable across datasets.** MAV, RMS, VAR and IEMG
   carry different units in the two datasets. Only *relative* quantities — channel rankings,
   ranking agreement, fraction of channels retained, performance deltas — may be compared.
   Absolute feature values must never be tabulated side by side.
3. 8-bit resolution is coarse. Low-amplitude channels lose proportionally more information to
   quantisation, which may itself bias channel importance toward high-amplitude sites. This is a
   confound specific to DB5 and is a limitation, not a finding.

### Spectral power peaks just below Nyquist

Peak power sits at **88.7 Hz**, with 95% of power below 94.9 Hz and 99% below 97.7 Hz — i.e.
the spectrum is still rising as it reaches the 100 Hz Nyquist limit. Physiological sEMG carries
substantial power well above 100 Hz, so the Myo's 200 Hz sampling cannot represent the full
signal, and energy above Nyquist is folded back into the measured band.

This is a known property of the Myo armband rather than a defect in this dataset copy, but it
means DB5 and GRABMyo do not observe the same physical bandwidth. It is a further reason the
replication is **methodological only**: whether the selection procedure behaves consistently, not
whether the same frequencies or the same electrodes matter.

### Correction to the automatically generated powerline text above

The generated sentence describes both ratios as "near 1". They are 0.26 (50 Hz) and 0.65 (60 Hz),
i.e. clearly **below** the 10-95 Hz baseline — those bands carry *less* power than the median,
not merely no excess. The conclusion is unchanged and in fact strengthened: there is no powerline
peak to remove, and **no notch filter is applied to DB5**. A notch here would only delete genuine
signal.
