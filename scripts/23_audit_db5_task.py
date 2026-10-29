"""Derive the NinaPro DB5 cohort description and task definition from the data itself.

The prior manuscript stated DB5 demographics (10 subjects, 8M/2F, age 34.9 +/- 11.8) with no
derivation; those numbers do not come from any file in this repository. Every value below is
read out of the distributed .mat files.

Outputs:
  data/metadata/db5_subject_info.csv
  data/metadata/db5_class_mapping.csv
  reports/db5_task_audit.md
"""

import glob
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.io as sio

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "ninapro_db5"
META = ROOT / "data" / "metadata"
REPORTS = ROOT / "reports"

# DB5 exercise A (E1) movement names, per the NinaPro DB5 protocol description.
E1_NAMES = {
    1: "Thumb up",
    2: "Extension of index and middle, flexion of the others",
    3: "Flexion of ring and little finger, extension of the others",
    4: "Thumb opposing base of little finger",
    5: "Abduction of all fingers",
    6: "Fingers flexed together in fist",
    7: "Pointing index",
    8: "Adduction of extended fingers",
    9: "Wrist supination (axis: middle finger)",
    10: "Wrist pronation (axis: middle finger)",
    11: "Wrist supination (axis: little finger)",
    12: "Wrist pronation (axis: little finger)",
}


def scalar(d, key):
    if key not in d:
        return None
    v = np.asarray(d[key]).ravel()
    if v.size == 0:
        return None
    x = v[0]
    if isinstance(x, np.ndarray):
        x = x.ravel()[0] if x.size else None
    return x


def main():
    META.mkdir(parents=True, exist_ok=True)
    subs, class_rows = [], []

    for sdir in sorted(RAW.glob("s*"), key=lambda p: int(p.name[1:]) if p.name[1:].isdigit() else 0):
        if not sdir.is_dir():
            continue
        e1 = list(sdir.glob("*_E1_*.mat"))
        if not e1:
            continue
        d = sio.loadmat(str(e1[0]))
        emg = np.asarray(d["emg"])
        rst = np.asarray(d["restimulus"]).ravel()
        rrep = np.asarray(d.get("rerepetition", d["repetition"])).ravel()
        fs = float(np.asarray(d["frequency"]).ravel()[0])

        gender = scalar(d, "gender")
        gender = str(gender).strip() if gender is not None else "?"
        subs.append({
            "subject": sdir.name,
            "subject_id": int(scalar(d, "subject") or 0),
            "age": float(scalar(d, "age") or np.nan),
            "gender": gender,
            "height_cm": float(scalar(d, "height") or np.nan),
            "weight_kg": float(scalar(d, "weight") or np.nan),
            "forearm_circumference_cm": float(scalar(d, "circumference") or np.nan),
            "laterality": str(scalar(d, "laterality")).strip(),
            "fs_hz": fs,
            "n_emg_channels": int(emg.shape[1]),
            "e1_duration_s": round(emg.shape[0] / fs, 1),
            "e1_movements": int((np.unique(rst) > 0).sum()),
            "e1_repetitions": int((np.unique(rrep) > 0).sum()),
        })

        for m in sorted(np.unique(rst)):
            n_win = int((rst == m).sum())
            class_rows.append({
                "subject": sdir.name, "exercise": "E1", "movement_id": int(m),
                "movement_name": "Rest" if m == 0 else E1_NAMES.get(int(m), "?"),
                "n_samples": n_win, "duration_s": round(n_win / fs, 1),
            })

    df_sub = pd.DataFrame(subs)
    df_sub.to_csv(META / "db5_subject_info.csv", index=False)

    df_cls = pd.DataFrame(class_rows)
    df_cls.to_csv(META / "db5_class_mapping.csv", index=False)

    # Cohort summary derived, not asserted
    n = len(df_sub)
    g = df_sub.gender.str.upper().str[0].value_counts().to_dict()
    age_m, age_s = df_sub.age.mean(), df_sub.age.std()
    active = df_cls[df_cls.movement_id > 0]
    rest = df_cls[df_cls.movement_id == 0]
    dur_active = active.groupby("subject").duration_s.sum()
    dur_rest = rest.groupby("subject").duration_s.sum()

    with open(REPORTS / "db5_task_audit.md", "w", encoding="utf-8") as f:
        f.write("# NinaPro DB5 — cohort and task definition, derived from the data\n\n")
        f.write("Every number here is read from the distributed `.mat` files.\n\n")
        f.write("## Cohort\n\n")
        f.write(f"- Subjects: **{n}**\n")
        f.write(f"- Gender counts (from `gender` field): **{g}**\n")
        f.write(f"- Age: **{age_m:.1f} +/- {age_s:.1f}** years "
                f"(range {df_sub.age.min():.0f}-{df_sub.age.max():.0f})\n")
        f.write(f"- Height: {df_sub.height_cm.mean():.1f} +/- {df_sub.height_cm.std():.1f} cm\n")
        f.write(f"- Weight: {df_sub.weight_kg.mean():.1f} +/- {df_sub.weight_kg.std():.1f} kg\n")
        f.write(f"- Forearm circumference: {df_sub.forearm_circumference_cm.mean():.1f} +/- "
                f"{df_sub.forearm_circumference_cm.std():.1f} cm\n")
        f.write(f"- Sampling rate: **{sorted(df_sub.fs_hz.unique())} Hz**\n")
        f.write(f"- EMG channels: **{sorted(df_sub.n_emg_channels.unique())}** "
                f"(two Myo armbands, 8 electrodes each)\n\n")
        f.write("## Task (Exercise E1)\n\n")
        f.write(f"- Active movements: **{sorted(df_sub.e1_movements.unique())}**\n")
        f.write(f"- Repetitions per movement: **{sorted(df_sub.e1_repetitions.unique())}**\n")
        f.write(f"- Label source: `restimulus` / `rerepetition` (refined boundaries) rather than "
                f"`stimulus`, which carries the un-refined prompt timing\n\n")
        f.write("### Class balance (seconds per subject, E1)\n\n")
        f.write(f"- Active classes combined: {dur_active.mean():.0f} s per subject\n")
        f.write(f"- Rest class: {dur_rest.mean():.0f} s per subject "
                f"({100*dur_rest.mean()/(dur_rest.mean()+dur_active.mean()):.0f}% of the recording)\n\n")
        f.write("Rest dominates the raw recording, which is why the primary task excludes it: "
                "including a large, easy rest class inflates accuracy and hides degradation on the "
                "active movements that matter.\n\n")
        f.write("### Movement list\n\n| id | movement |\n|---|---|\n")
        for k in sorted(E1_NAMES):
            f.write(f"| {k} | {E1_NAMES[k]} |\n")
        f.write("\n## Relation to GRABMyo\n\n")
        f.write("DB5 E1 is a 12-class finger/wrist movement task; GRABMyo's primary task is 16 "
                "active hand and finger gestures. The movement sets are **not** identical and the "
                "electrode locations are **not** transferable between datasets. DB5 therefore "
                "serves as a *methodological* replication only: whether the selection procedure "
                "behaves the same way, not whether the same physical channels are chosen.\n")

    print(df_sub.to_string(index=False))
    print(f"\nsubjects={n} gender={g} age={age_m:.1f}+/-{age_s:.1f}")
    print(f"active movements={sorted(df_sub.e1_movements.unique())} "
          f"reps={sorted(df_sub.e1_repetitions.unique())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
