# NinaPro DB5 feature extraction (exercise E1)

- Subjects: **10**
- Movements: **12** (rest excluded)
- Repetitions: **6**
- Windows: **21089**
- Blocks too short to window: **0**

## Preprocessing (DB5-specific, see reports/db5_signal_audit.md)

- Band-pass 10.0-95.0 Hz, order 4, zero-phase
- **No notch** — no powerline peak present
- Window 250 ms = 50 samples, 50% overlap, never crossing movement or repetition boundaries
- Count-feature threshold 7.0 ADC units (DB5 is 8-bit integer data)
- Labels from `restimulus`/`rerepetition`

## Windows per movement

| movement | windows |
|---|---|
| 1 | 2226 |
| 2 | 1596 |
| 3 | 2037 |
| 4 | 1568 |
| 5 | 1782 |
| 6 | 1810 |
| 7 | 2041 |
| 8 | 1735 |
| 9 | 1468 |
| 10 | 1798 |
| 11 | 1419 |
| 12 | 1609 |

## Comparability caveat

Amplitude features are in **arbitrary ADC units**, not mV. They are not numerically comparable with GRABMyo. Only relative quantities — rankings, ranking agreement, retained-channel fraction, performance deltas — may be compared across datasets.
