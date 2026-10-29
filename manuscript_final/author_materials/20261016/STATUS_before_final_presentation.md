# Study status: 2026-10-14 computational and editorial revision complete

Current deliverables: manuscript_revision/20261014/. The previous September status is preserved under original/reports/STATUS_before_20261014_revision.md.

All required existing-data experiment tracks are complete. The current result-verification route passed4593 checks, the documented test suite passed53 tests, and all13 main plus14 supplementary PDF pages passed visual acceptance. Current verification command: python scripts/16_verify_results.py --revision-dir manuscript_revision/20261014.

At the0.02 mean Macro-F1 tolerance, the supported minimum is12 for the original cross-fitted SHAP procedure and15 for the tested fixed geometric ordering. Direct12-site mean superiority over geometry remains uncertain. Shared-resource SHAP exceeds grouped permutation at6, while its12-site mean advantage remains uncertain; six does not meet primary NI.

The isolated participant-attribution refit passes current provenance verification. The scientific stability-penalty improvement gate remains unsupported; all participant penalties select identical physical sets at12 in43/43 folds. The old historical source-hash mismatch is preserved, and the default historical verification route must not be confused with the current revision route.

Reports01-08, native sources, complete participant results, prediction files, vector figures, protocols and reproduction materials are in the dated package. Final archive and checksums: manuscript_revision/grabmyo_revision_20261014.zip and its SHA256 sidecar.

Ethics remains unresolved as requested. Funding, contributions, conflicts, acknowledgements and the permanent public archive require author confirmation. No independent new same-montage cohort was available. This is a computationally completed peer-review draft, not an author-approved submission or prospective device validation.
