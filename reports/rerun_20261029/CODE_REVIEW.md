# Study code review and fixes

Reviewed 2026-10-29T18:58:57+07:00 (Asia/Saigon). The review covered the operative scientific core, resume/recovery, confirmatory input validation, independent reporting and the current full-study scheduler. It was a targeted correctness/reliability review, not a new literature review or a redesign of the frozen analysis plan.

| Priority | Finding | Correction and scope |
|---|---|---|
| High | Fresh DB5 `--resume` crashed on missing output columns | Fresh/partial initialization fixed, fingerprints and atomic CSV writes added. Already staged before the DB5 job started; that job is now running. Additional CPU/CUDA fingerprint separation is canonical and deferred until its existing batch finishes. |
| High | Sparse resume could mix inputs/budgets or retain duplicate/incomplete groups | Cache/ranking/source/model/version fingerprints, finite/unique/subset checks, complete-group reuse and atomic output. Staged before the primary curve started. |
| High | Missing whole model/penalty/count groups could evade confirmatory validation | Exact primary files and complete participant/model/lambda/k grids required before writing confirmatory statistics. Invalid inputs fail even in partial mode. |
| High | Restart could forget surviving workers and launch duplicate writers | Same-user process/group/workspace ownership guards, PID/start/boot identities, signal-safe child registration and cleanup. On disk and snapshotted; coordinator activation waits at a safe boundary. Legacy launch commands delegate to guarded code. |
| High | Baseline interruption lost predictions from completed fits | New opt-in `--resume` and atomic per-participant NPZ prediction checkpoints with protocol and alignment validation. Existing live SVM/RF batch intentionally remains on its original code until completion. |
| Medium | Fake/unknown completion labels could end the queue early | Reject unknown stage names; require the actual required-name set. |
| Medium | Empty/NaN comparison tables could appear successful | Complete finite expected participant grids required for each comparison. |
| Medium | Mutable external helpers were absent from source provenance | Immutable initial manifest plus explicit chained amendments, verified helper snapshots and retained source versions. |
| Medium | Build metadata and narratives could repeat historical settings/outcomes | Runtime evidence is read from the matching run. Independent reports derive current mean-CI claims from current tables; historical events/test counts are not substituted. Compiled manuscripts remain pending narrative and visual review. |
| Medium | Bare pytest collected duplicate archived test modules | Canonical discovery scoped to `tests/` in pyproject.toml. |

## Verification

- **117 canonical tests passed** in the latest full run (`review_final_tests.log`); GPU model fitting was not used for these checks.
- Original baseline fit/cache functions, sparse fitting/sampling/channel functions and DB5 fit/channel functions have unchanged ASTs versus the delivered Git sources (`review_numerical_code_checks.json`).
- The guarded statistical implementation reproduced the delivered master table, model comparisons, non-inferiority table and analysis provenance unchanged in scratch checks (rtol1e-10/atol1e-12). Those checks are historical compatibility evidence, not acceptance of the still-running new study.
- Independent reviews checked the scientific and execution fixes. Active scientific sources were not modified mid-fit.
- Source verification passed across the original manifest and reviewed amendments. `git -c core.whitespace=cr-at-eol diff --check` passed.

## Current deployment

The current queue is **RUNNING**. Ranking has completed all43 outer folds. DB5 fitting is now complete; primary sparse fitting, bipolar fitting and the old CPU baseline continue. No training job was stopped for this review.

The activation monitor is **WAITING_FOR_NONRESUMABLE_STAGES**. It will wait for every non-resumable stage and all explicitly deferred source-producing batches to complete. It confirms the old parent is stopped before checking descendant ownership; it then cleans checkpointable groups, waits for the execution lock, verifies all sources and starts the reviewed coordinator. Deferred source copies have a recoverable transaction journal and preserve the versions actually used by completed fits. Monitor signals, ambiguous processes or fingerprint mismatches fail closed. The monitor itself runs in the `review-handoff` window of `sensor-study-20261029`.

Live activation state: `outputs/rerun_20261029/review_activation.json`. Deferred files: `review_deferred_sources.json`. Evidence/source snapshots: `source_amendments.json`, `source_versions/`, `operations/project/`. Source transactions, if interrupted, can be finished with the guarded `.tmp/activate_review.py --recover-source-transaction` path after all workspace workers have exited.

Legacy checkpoint files without fingerprints are deliberately rejected; use a fresh output directory rather than inventing provenance. Existing archived study results and initial source fingerprints remain preserved. Frozen seeds, margins, sample budgets, participant exclusions and fitting algorithms are unchanged. Previously disclosed historical development-exposure and inference limitations remain applicable.

The active old CPU batch has no recoverable prediction checkpoints; it is being allowed to finish. Full-study result verification, new manuscript compilation, comparison and fresh narrative/PDF review remain pending.
