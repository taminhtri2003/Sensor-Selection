# NinaPro DB5 — cohort and task definition, derived from the data

Every number here is read from the distributed `.mat` files.

## Cohort

- Subjects: **10**
- Gender counts (from `gender` field): **{'M': 8, 'F': 2}**
- Age: **28.0 +/- 4.0** years (range 22-34)
- Height: 172.1 +/- 9.9 cm
- Weight: 68.6 +/- 9.1 kg
- Forearm circumference: 25.5 +/- 2.0 cm
- Sampling rate: **[np.float64(200.0)] Hz**
- EMG channels: **[np.int64(16)]** (two Myo armbands, 8 electrodes each)

## Task (Exercise E1)

- Active movements: **[np.int64(12)]**
- Repetitions per movement: **[np.int64(6)]**
- Label source: `restimulus` / `rerepetition` (refined boundaries) rather than `stimulus`, which carries the un-refined prompt timing

### Class balance (seconds per subject, E1)

- Active classes combined: 277 s per subject
- Rest class: 453 s per subject (62% of the recording)

Rest dominates the raw recording, which is why the primary task excludes it: including a large, easy rest class inflates accuracy and hides degradation on the active movements that matter.

### Movement list

| id | movement |
|---|---|
| 1 | Thumb up |
| 2 | Extension of index and middle, flexion of the others |
| 3 | Flexion of ring and little finger, extension of the others |
| 4 | Thumb opposing base of little finger |
| 5 | Abduction of all fingers |
| 6 | Fingers flexed together in fist |
| 7 | Pointing index |
| 8 | Adduction of extended fingers |
| 9 | Wrist supination (axis: middle finger) |
| 10 | Wrist pronation (axis: middle finger) |
| 11 | Wrist supination (axis: little finger) |
| 12 | Wrist pronation (axis: little finger) |

## Relation to GRABMyo

DB5 E1 is a 12-class finger/wrist movement task; GRABMyo's primary task is 16 active hand and finger gestures. The movement sets are **not** identical and the electrode locations are **not** transferable between datasets. DB5 therefore serves as a *methodological* replication only: whether the selection procedure behaves the same way, not whether the same physical channels are chosen.
