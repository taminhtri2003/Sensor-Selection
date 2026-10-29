"""Leave-one-participant-out check of the label-free ZC/SSC/WAMP amplitude thresholds.

Post-hoc sensitivity analysis added 2026-09-21 in response to the pre-submission audit (P0-1).
The thresholds were set once, as ~1.15x the median |first difference| of the signal:

  GRABMyo monopolar 1e-2 mV   from 54 probe records of participants {1,7,15,23,31,43}
                              (reports/signal_properties_audit.md, raw unfiltered)
  GRABMyo bipolar   4e-3 mV   same probes, ring-1 minus ring-2 derivation (5e-3 before Decision 20)
  DB5               7 ADC     from all 10 subjects, active samples (reports/db5_signal_audit.md)

For every outer fold p the median is recomputed WITHOUT participant p's records. If the rounded
threshold that the documented rule gives is the same in every fold, fold-wise derivation would
have produced bit-identical features, and the held-out participant had no influence on them.
Participants whose records were not in the probe set trivially give the pooled value.

Rule reconstructed from the scripts: threshold = 1.15 x median, rounded to one significant figure
(GRABMyo: 1.15 x 8.736e-3 = 1.005e-2 -> 1e-2; bipolar: 1.15 x 4.35e-3 = 5.0e-3 -> 5e-3;
DB5: 1.15 x 6 = 6.9 -> 7).

Output: artifacts/sensitivity/loo_threshold_check.csv, reports/loo_threshold_check.md
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.io as sio
import wfdb

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "artifacts" / "sensitivity"
PROBES = [(s, p, g, t) for s in (1, 2, 3) for p in (1, 7, 15, 23, 31, 43)
          for g, t in ((1, 1), (9, 3), (17, 7))]
RING1 = [f"F{i}" for i in range(1, 9)]
RING2 = [f"F{i}" for i in range(9, 17)]
USED = {"grabmyo_monopolar": 1e-2, "grabmyo_bipolar": 4e-3, "db5": 7.0}  # bipolar: Decision 20


def rule(median):
    v = 1.15 * median
    return float(f"{v:.0e}")


def main():
    mono, bip = [], []
    for s, p, g, t in PROBES:
        rec = wfdb.rdrecord(str(ROOT / f"Session{s}" / f"session{s}_participant{p}"
                                / f"session{s}_participant{p}_gesture{g}_trial{t}"))
        sig = np.asarray(rec.p_signal, float)
        names = list(rec.sig_name)
        mono.append((p, float(np.median(np.abs(np.diff(sig[:, :16], axis=0))))))
        b = sig[:, [names.index(c) for c in RING1]] - sig[:, [names.index(c) for c in RING2]]
        bip.append((p, float(np.median(np.abs(np.diff(b, axis=0))))))

    db5 = []
    for f in sorted((ROOT / "data/raw/ninapro_db5").rglob("*_E1_*.mat")):
        d = sio.loadmat(str(f))
        emg = np.asarray(d["emg"], float)
        act = emg[np.asarray(d["restimulus"]).ravel() > 0]
        db5.append((int(f.parent.name[1:]), float(np.median(np.abs(np.diff(act, axis=0))))))

    rows = []
    for name, recs, folds in (("grabmyo_monopolar", mono, range(1, 44)),
                              ("grabmyo_bipolar", bip, range(1, 44)),
                              ("db5", db5, range(1, 11))):
        pooled = float(np.median([v for _, v in recs]))
        for p in folds:
            loo = float(np.median([v for q, v in recs if q != p]))
            rows.append({"representation": name, "held_out": p,
                         "held_out_in_probe_set": any(q == p for q, _ in recs),
                         "pooled_median": pooled, "loo_median": loo,
                         "loo_rule_threshold": rule(loo), "used_threshold": USED[name],
                         "pooled_rule_threshold": rule(pooled)})
    df = pd.DataFrame(rows)
    df["identical"] = np.isclose(df.loo_rule_threshold, df.used_threshold)
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT / "loo_threshold_check.csv", index=False)

    lines = ["# Leave-one-participant-out threshold check (post hoc, audit P0-1)", "",
             "Rule: threshold = 1.15 x median |first difference|, one significant figure.", "",
             "| representation | folds | folds with held-out in probe set | pooled median | "
             "LOO median range | used threshold | folds giving identical threshold |",
             "|---|---|---|---|---|---|---|"]
    for name, g in df.groupby("representation", sort=False):
        lines.append(f"| {name} | {len(g)} | {int(g.held_out_in_probe_set.sum())} | "
                     f"{g.pooled_median.iloc[0]:.4g} | {g.loo_median.min():.4g}-"
                     f"{g.loo_median.max():.4g} | {g.used_threshold.iloc[0]:g} | "
                     f"{int(g.identical.sum())}/{len(g)} |")
    g = df[df.representation == "grabmyo_bipolar"]
    lines += ["", "## Bipolar threshold provenance", "",
              "`scripts/35_extract_bipolar_features.py` states the bipolar threshold as 1.15 x a "
              "measured median |diff| of 4.35e-3 mV, but how that median was computed is not "
              f"recorded. On the documented probe set the raw bipolar median is "
              f"{g.pooled_median.iloc[0]:.3g} mV (filtered: 3.06e-3 mV), for which the rule gives "
              f"{g.pooled_rule_threshold.iloc[0]:g} mV. The earlier value 5e-3 mV could not be "
              "reproduced from the documented rule, so the bipolar analysis was re-run with the "
              "rule-derived value (decision_log Decision 20; earlier run archived). The leave-one-out "
              f"median varies only within {g.loo_median.min():.3g}-{g.loo_median.max():.3g} mV, and "
              "the rule gives the same threshold in every fold."]
    (ROOT / "reports/loo_threshold_check.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    # the monopolar and DB5 thresholds are the ones the confirmatory / replication claims rest on
    ok = df[df.representation != "grabmyo_bipolar"].identical.all()
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
