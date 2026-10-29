# GRABMyo bipolar feature extraction (8 conventional sensors)

- Derivation: `bipolar_j = F_j - F_(j+8)`, j = 1..8 (ring 1 minus vertically aligned ring 2 partner, 2 cm apart)
- Records expected: **15351**, extracted OK: **15351**
- Status breakdown: `{'OK': 15351}`
- Windows: **598689**
- Channels: **8** x 10 features = 80

## Why this exists

The primary analysis selects among 16 **monopolar** electrodes. Under that unit a 'k sensor' claim is ambiguous, because an arbitrary subset of monopolar electrodes need not form deployable bipolar pairs. This representation uses the conventional sensing unit so the study's conclusions can be checked against what a real armband could instantiate.

Bipolar derivation also cancels common-mode content shared by the electrode pair, so this is a genuinely different representation rather than a coarser view of the same information.
