# GRABMyo feature extraction — complete cohort

- Expected records: **15351** (43 participants x 3 sessions x 17 gestures x 7 trials)
- Extracted OK: **15351**
- Status breakdown: `{'OK': 15351}`
- Total windows: **997815**
- Participants realised: **43**
- Sessions realised: **[np.int32(1), np.int32(2), np.int32(3)]**
- Gestures realised: **17**

## Preprocessing

- Channels: 16 forearm (F1..F16), validated by header name per record
- Bandpass: 20.0-450.0 Hz, order 4, zero-phase (filtfilt)
- Notch: 50.0 Hz, Q=30.0, zero-phase — 50 Hz confirmed empirically
- Window: 150.0 ms, 50.0% overlap, never crossing trial boundaries
- Features: 10 per channel x 16 channels = 160

