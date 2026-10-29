# GRABMyo electrode-selection revision -2026-10-14

Computational and editorial peer-review draft, with author declarations deferred. This package does not claim a submission-ready ethics/funding/conflict statement or prospective validation of a locked physical interface.

- Read manuscript/main.pdf and manuscript/supplementary.pdf. Their editable TeX, bibliography, class and local inputs are in manuscript/.
- Reports01-08 document the scientific/literature/method/statistical audits, additional experiments, revisions, claim evidence and final quality control. reports/unresolved_author_inputs.md preserves all outstanding author decisions.
- figures/ contains six main and seven supplementary figures as vector PDF/SVG,300dpi previews, source data and provenance.
- experiments/ and tables/ retain complete participant/gesture outputs, paired predictions, rankings, compute measurements and full-precision inference.
- reproducibility/README.md and RUN_ORDER.md distinguish frozen-record verification from a raw-data rerun. Current requirements, source snapshots, original inputs, protocols and checksums accompany them.
- reports/verification.json records the scripts/16_verify_results.py revision gate. reports/visual_acceptance.json records every inspected PDF page and its fingerprint. The final QC report explains the remaining scientific limits.

The primary claim concerns mean recognition performance under the evaluated offline protocol. Participant/gesture losses, uncertain direct geometric mean superiority, penalty findings and transfer boundaries remain visible in the manuscript. Negative scientific findings are not converted into positive results by changing seeds, margins or penalties.

original/ preserves superseded sources and selected records. These are history, not current results. In particular, the old invalid preliminary package and historical source-hash finding are explicitly distinguished from the current verified outputs. Raw recordings are obtained from the cited public repositories and are not duplicated here.

The package manifest hashes every file inside the dated package except itself. Archive CRC and an external SHA256 sidecar verify the accompanying zip. Any later edit or recompilation requires renewed verification and PDF-page inspection.
