"""Empirical signal audit of NinaPro DB5 before its preprocessing is chosen.

DB5 must NOT inherit GRABMyo's filter settings. At 200 Hz the Nyquist limit is 100 Hz, so the
20-450 Hz band used for GRABMyo is impossible here; copying it across datasets is the mistake the
prior manuscript made by asserting a "10-90 Hz" band without ever measuring the signal.

Measures, from the data: amplitude scale, usable bandwidth, and whether powerline interference is
even present (the Myo armband applies its own hardware filtering, so a notch may be unnecessary).

Writes reports/db5_signal_audit.md
"""

import sys
from pathlib import Path

import numpy as np
import scipy.io as sio
from scipy.signal import welch

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "ninapro_db5"
OUT = ROOT / "reports" / "db5_signal_audit.md"
FS = 200.0


def band_ratio(psd, freqs, centre, half=2.0):
    m = (freqs >= centre - half) & (freqs <= centre + half)
    base = (freqs >= 10) & (freqs <= 95)
    if not m.any() or not base.any():
        return float("nan")
    return float(np.mean(psd[m]) / (np.median(psd[base]) + 1e-30))


def main():
    files = sorted(RAW.rglob("*_E1_*.mat"))
    if not files:
        print("FATAL: no DB5 E1 files found")
        return 2

    amp_med, amp_p99, diff_med = [], [], []
    r50, r60 = [], []
    psd_acc, freqs_ref = None, None
    frac_above = {}
    n = 0

    for f in files:
        d = sio.loadmat(str(f))
        emg = np.asarray(d["emg"], dtype=float)
        rst = np.asarray(d["restimulus"]).ravel()
        active = emg[rst > 0]                      # measure on movement, not rest
        if active.size == 0:
            continue
        n += 1
        amp_med.append(float(np.median(np.abs(active))))
        amp_p99.append(float(np.percentile(np.abs(active), 99)))
        diff_med.append(float(np.median(np.abs(np.diff(active, axis=0)))))

        freqs, psd = welch(active, fs=FS, nperseg=min(active.shape[0], 512), axis=0)
        psd_m = np.mean(psd, axis=1)
        r50.append(band_ratio(psd_m, freqs, 50.0))
        r60.append(band_ratio(psd_m, freqs, 60.0))
        psd_acc = psd_m if psd_acc is None else psd_acc + psd_m
        freqs_ref = freqs

    psd_mean = psd_acc / n
    total = np.trapezoid(psd_mean, freqs_ref) if hasattr(np, "trapezoid") else np.trapz(psd_mean, freqs_ref)
    for lo in (5, 10, 15, 20):
        m = freqs_ref >= lo
        part = np.trapezoid(psd_mean[m], freqs_ref[m]) if hasattr(np, "trapezoid") else np.trapz(psd_mean[m], freqs_ref[m])
        frac_above[lo] = float(part / total)

    # cumulative power to find the effective upper edge
    cum = np.cumsum(psd_mean) / np.sum(psd_mean)
    f95 = float(freqs_ref[np.searchsorted(cum, 0.95)])
    f99 = float(freqs_ref[np.searchsorted(cum, 0.99)])
    peak = float(freqs_ref[int(np.argmax(psd_mean))])

    med50, med60 = float(np.nanmedian(r50)), float(np.nanmedian(r60))

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("# NinaPro DB5 — empirical signal audit\n\n")
        fh.write(f"Measured on movement periods (restimulus > 0) of {n} E1 recordings, unfiltered.\n\n")
        fh.write("## Acquisition\n\n")
        fh.write(f"- Sampling rate: **{FS:.0f} Hz** -> Nyquist **{FS/2:.0f} Hz**\n")
        fh.write("- The GRABMyo band (20-450 Hz) is **not representable** here; a DB5-specific "
                 "band is required.\n\n")
        fh.write("## Amplitude\n\n")
        fh.write(f"- median |x|: {np.median(amp_med):.4g}\n")
        fh.write(f"- 99th percentile |x|: {np.median(amp_p99):.4g}\n")
        fh.write(f"- median |diff(x)|: {np.median(diff_med):.4g}\n\n")
        fh.write("## Spectrum\n\n")
        fh.write(f"- Peak power at **{peak:.1f} Hz**\n")
        fh.write(f"- 95% of power below **{f95:.1f} Hz**; 99% below **{f99:.1f} Hz**\n")
        fh.write("- Fraction of total power retained by a high-pass at:\n")
        for lo, fr in frac_above.items():
            fh.write(f"  - {lo} Hz: {fr*100:.1f}%\n")
        fh.write("\n## Powerline\n\n")
        fh.write("| candidate | band-power ratio vs 10-95 Hz median |\n|---|---|\n")
        fh.write(f"| 50 Hz | {med50:.2f} |\n| 60 Hz | {med60:.2f} |\n\n")
        if max(med50, med60) < 2.0:
            fh.write("No powerline peak stands out (both ratios near 1). The Myo armband applies "
                     "its own hardware filtering, so **no notch filter is applied to DB5**. "
                     "Adding one would remove genuine EMG power in a band where little "
                     "interference exists.\n\n")
        else:
            worst = 50 if med50 >= med60 else 60
            fh.write(f"A peak is present at **{worst} Hz**; a notch at that frequency is applied "
                     f"to DB5.\n\n")
        fh.write("## Chosen DB5 preprocessing\n\n")
        fh.write("Stated as a deliberate difference from GRABMyo, not an oversight:\n\n")
        fh.write("- band-pass **10-95 Hz**, 4th-order Butterworth, zero-phase\n")
        fh.write("- notch: see above\n")
        fh.write("- window 250 ms = **50 samples** at 200 Hz, 50% overlap\n\n")
        fh.write("The 50-sample window is short. MNF/MDF estimated from 50 samples are coarse "
                 "(frequency resolution 4 Hz), which must be acknowledged when comparing feature "
                 "importance between datasets.\n")

    print(f"n={n} peak={peak:.1f}Hz f95={f95:.1f}Hz f99={f99:.1f}Hz")
    print(f"median|x|={np.median(amp_med):.4g} median|diff|={np.median(diff_med):.4g}")
    print(f"50Hz ratio={med50:.2f} 60Hz ratio={med60:.2f}")
    print(f"power retained above 10 Hz: {frac_above[10]*100:.1f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
