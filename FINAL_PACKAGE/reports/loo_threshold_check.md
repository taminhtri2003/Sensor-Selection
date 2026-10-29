# Leave-one-participant-out threshold check (post hoc, audit P0-1)

Rule: threshold = 1.15 x median |first difference|, one significant figure.

| representation | folds | folds with held-out in probe set | pooled median | LOO median range | used threshold | folds giving identical threshold |
|---|---|---|---|---|---|---|
| grabmyo_monopolar | 43 | 6 | 0.008736 | 0.00852-0.009452 | 0.01 | 43/43 |
| grabmyo_bipolar | 43 | 6 | 0.003399 | 0.003359-0.003551 | 0.005 | 0/43 |
| db5 | 10 | 10 | 6 | 6-6 | 7 | 10/10 |

## Bipolar threshold provenance

`scripts/35_extract_bipolar_features.py` states the bipolar threshold as 1.15 x a measured median |diff| of 4.35e-3 mV, but how that median was computed is not recorded. On the documented probe set the raw bipolar median is 0.0034 mV (filtered: 3.06e-3 mV), for which the rule gives 0.004 mV. The used value 5e-3 mV therefore cannot be reproduced from the documented rule. It is, however, constant across folds: the leave-one-out median varies only within 0.00336-0.00355 mV, so no single held-out participant determines it. Reported as a limitation of the exploratory bipolar analysis; not re-run.
