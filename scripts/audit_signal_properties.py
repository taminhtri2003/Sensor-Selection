"""Empirical signal audit of raw GRABMyo before any preprocessing is frozen.

Determines, from the data rather than by assumption:
  - signal units and amplitude scale (needed to set ZC/SSC/WAMP thresholds)
  - powerline interference frequency (50 vs 60 Hz)
  - channel count, sampling rate, record duration
Writes reports/signal_properties_audit.md
"""

import sys
from collections import Counter
from pathlib import Path

import numpy as np
import wfdb
from scipy.signal import welch

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "reports" / "signal_properties_audit.md"

# Spread the probe across sessions and participants rather than sampling one corner.
PROBES = []
for sess in (1, 2, 3):
    for pid in (1, 7, 15, 23, 31, 43):
        for gesture, trial in ((1, 1), (9, 3), (17, 7)):
            PROBES.append((sess, pid, gesture, trial))


def record_path(sess, pid, gesture, trial):
    d = ROOT / f"Session{sess}" / f"session{sess}_participant{pid}"
    return d / f"session{sess}_participant{pid}_gesture{gesture}_trial{trial}"


def band_power(psd, freqs, centre, half_width=1.5):
    m = (freqs >= centre - half_width) & (freqs <= centre + half_width)
    return float(np.mean(psd[m])) if m.any() else float("nan")


def main():
    units = Counter()
    fs_vals = Counter()
    nchan = Counter()
    durations = []
    amp_abs_med = []
    amp_p99 = []
    diff_abs_med = []
    r50, r60 = [], []
    loaded = 0
    failures = []

    for sess, pid, gesture, trial in PROBES:
        base = record_path(sess, pid, gesture, trial)
        if not base.with_suffix(".dat").exists():
            failures.append(f"missing: {base.name}")
            continue
        try:
            rec = wfdb.rdrecord(str(base))
        except Exception as exc:
            failures.append(f"load error {base.name}: {exc}")
            continue

        sig = np.asarray(rec.p_signal, dtype=float)
        fs = float(rec.fs)
        loaded += 1
        fs_vals[fs] += 1
        nchan[sig.shape[1]] += 1
        durations.append(sig.shape[0] / fs)
        for u in (rec.units or []):
            units[u] += 1

        emg = sig[:, :16]
        finite = emg[np.isfinite(emg)]
        amp_abs_med.append(float(np.median(np.abs(finite))))
        amp_p99.append(float(np.percentile(np.abs(finite), 99)))
        diff_abs_med.append(float(np.median(np.abs(np.diff(emg, axis=0)))))

        # PSD on unfiltered signal: powerline peak must be measured before notching
        freqs, psd = welch(emg, fs=fs, nperseg=min(emg.shape[0], 4096), axis=0)
        psd_m = np.mean(psd, axis=1)
        base_band = (freqs >= 20) & (freqs <= 450)
        baseline = float(np.median(psd_m[base_band])) + 1e-30
        r50.append(band_power(psd_m, freqs, 50.0) / baseline)
        r60.append(band_power(psd_m, freqs, 60.0) / baseline)

    if loaded == 0:
        print("FATAL: no records loaded")
        print("\n".join(failures[:10]))
        return 2

    med50, med60 = float(np.median(r50)), float(np.median(r60))
    verdict = "60 Hz" if med60 > med50 else "50 Hz"

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("# Empirical signal-property audit — raw GRABMyo\n\n")
        f.write(f"Probed {loaded} records spanning 3 sessions x 6 participants x 3 gesture/trial pairs.\n")
        f.write("All measurements are on **unfiltered** signals.\n\n")
        f.write("## Acquisition properties\n\n")
        f.write(f"- Sampling rate: {dict(fs_vals)}\n")
        f.write(f"- Channel count: {dict(nchan)}\n")
        f.write(f"- Units reported in header: {dict(units)}\n")
        f.write(f"- Record duration (s): median {np.median(durations):.2f}, "
                f"min {np.min(durations):.2f}, max {np.max(durations):.2f}\n\n")
        f.write("## Amplitude scale (drives feature thresholds)\n\n")
        f.write(f"- median |x| across records: **{np.median(amp_abs_med):.3e}**\n")
        f.write(f"- 99th percentile |x|: **{np.median(amp_p99):.3e}**\n")
        f.write(f"- median |diff(x)|: **{np.median(diff_abs_med):.3e}**\n\n")
        f.write("## Powerline interference\n\n")
        f.write("Ratio of band power at the candidate mains frequency to the median 20-450 Hz power.\n")
        f.write("A ratio near 1 means no peak; a large ratio means strong interference.\n\n")
        f.write("| Candidate | median ratio | mean ratio | max ratio |\n|---|---|---|---|\n")
        f.write(f"| 50 Hz | {med50:.2f} | {np.mean(r50):.2f} | {np.max(r50):.2f} |\n")
        f.write(f"| 60 Hz | {med60:.2f} | {np.mean(r60):.2f} | {np.max(r60):.2f} |\n\n")
        f.write(f"**Dominant mains frequency: {verdict}**\n\n")
        if failures:
            f.write(f"## Probe failures ({len(failures)})\n\n")
            for x in failures[:20]:
                f.write(f"- {x}\n")

    print(f"loaded={loaded} fs={dict(fs_vals)} chan={dict(nchan)} units={dict(units)}")
    print(f"median|x|={np.median(amp_abs_med):.3e} p99|x|={np.median(amp_p99):.3e} "
          f"median|diff|={np.median(diff_abs_med):.3e}")
    print(f"50Hz ratio={med50:.2f}  60Hz ratio={med60:.2f}  -> {verdict}")
    if failures:
        print(f"failures={len(failures)}: {failures[:3]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
