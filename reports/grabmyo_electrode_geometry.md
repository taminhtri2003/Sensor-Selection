# GRABMyo forearm electrode geometry — and what "one sensor" means

This resolves a discrepancy that would otherwise have propagated into every sensor-reduction
claim in the study.

## The discrepancy

The dataset README and the WFDB headers describe **16 forearm channels** (`F1`…`F16`). The
GRABMyo data-descriptor paper and downstream literature describe GRABMyo as having
**8 forearm channels and 6 wrist channels**. Both are correct, and they count different things.

## What the electrode documentation shows

`Electrodelocation.pdf` labels the forearm montage explicitly as a **"2 × 8 channels forearm
setup"**: two circumferential rings of 8 electrodes each, with an **inter-ring distance of 2 cm**,
positioned relative to 1/3 of forearm length from the elbow crease. The wrist montage is
correspondingly a **"2 × 6 channels wrist setup"** (rings 3 and 4).

So the array is:

```
ring 1   F1  F2  F3  F4  F5  F6  F7  F8      <- 8 positions around the forearm
             (2 cm proximal-distal separation)
ring 2   F9 F10 F11 F12 F13 F14 F15 F16      <- same 8 circumferential positions
```

- **16** = monopolar electrodes (what is stored in the `.dat` files, referenced to a common reference)
- **8** = bipolar derivations, each formed from a vertically aligned pair `F_j − F_{j+8}`

The "8 forearm channels" in the literature are the **bipolar pairs**, which is the conventional
sEMG sensing unit.

## Why this matters for a sensor-selection paper

A claim of the form "*k* sensors suffice" is ambiguous until the unit is fixed:

| Unit | Count | Deployment meaning |
|---|---|---|
| Monopolar electrode | 16 | Selecting `F3` alone is **not** a deployable bipolar sensor — it needs a reference partner |
| Bipolar pair | 8 | Matches a conventional wearable sEMG sensor and the dataset's own convention |

Selecting freely among the 16 monopolar channels risks producing a "5-sensor" layout that no
conventional armband could actually instantiate, because the selected electrodes may not form
bipolar pairs. This is exactly the kind of claim a reviewer with an instrumentation background
would reject.

## Decision

- **Primary analysis stays on the 16 monopolar forearm channels**, as specified in the study
  brief, and for dimensional parity with NinaPro DB5 (also 16 channels). Every claim will state
  explicitly that the unit is a **monopolar electrode**, not a bipolar sensor.
- **A bipolar sensitivity analysis (8 derived channels, `F_j − F_{j+8}`) is required** before any
  deployment-flavoured claim is made. If the ranking concentrates on electrodes that do not pair
  up, that must be reported as a limitation on physical realisability.
- Wording throughout: "channel" for the monopolar unit; the phrase "sensor" is reserved for the
  bipolar pair. The current draft language of "eliminating 62.5% of physical electrodes" is only
  defensible under the monopolar reading and must be stated as such.

## Geometry available for the equispaced baseline

The montage gives real spatial coordinates, so the geometry-spread baseline (an algorithmic
farthest-point/equispaced selection, not a hand-picked set) can be defined properly:

- circumferential index `c(j) = ((j - 1) mod 8) + 1`, i.e. angular position `2π(c-1)/8`
- longitudinal level `r(j) = 1` for `F1..F8`, `2` for `F9..F16`, separated by 2 cm

A structural parallel holds for **NinaPro DB5**, which uses two Myo armbands of 8 electrodes at
two longitudinal positions — also a 2 × 8 arrangement. This makes the *methodological* comparison
between datasets meaningful even though absolute electrode locations are not transferable.

## What must not be claimed

Electrode-to-muscle registration was not performed in either dataset. Channel positions are
defined relative to forearm length and the elbow crease, not to identified muscle bellies. No
claim of the form "channel *n* corresponds to FDS/FDP/EDC" is supportable. Conservative spatial
language only ("a proximal-dorsal forearm region", "the ring-2 posterior aspect").
