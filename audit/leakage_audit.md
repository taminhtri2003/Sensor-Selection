# Leakage audit

**artifact_checks:** PASS

**outer_exclusion:** Every saved inner attribution partition excludes its outer test participant.

**subset_provenance:** Every sparse subset matches its own outer-training ranking.

**thresholds:** Originally pooled. Post-hoc leave-one-out rule yields identical thresholds; this is equivalence evidence, not proof of prospective fold-local estimation.

**lambda:** Four candidates reported. No lambda selection criterion was prespecified or implemented.

**historical_calibration:** Training budgets were calibrated on held-out folds 1 and 7 (Decision 17). Their prior use prevents an unconditional zero-leakage claim about study development.

**limits:** Artifacts cannot prove the full historical model-fitting process. Training/scaling isolation is additionally checked in source and regression tests.

**overall_verdict:** IMPLEMENTED_RANKING_EXCLUSION_VERIFIED_WITH_DISCLOSED_HISTORICAL_LIMITATIONS
