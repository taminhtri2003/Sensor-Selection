# Rerun execution status

Verified 2026-10-30T16:15+07:00 (Asia/Saigon).

**STOPPED by the user at 2026-10-30 09:14 UTC, study incomplete.** The coordinator received SIGTERM, terminated its workers and recorded `STOPPED` in `outputs/rerun_20261029/status.json`; no study process or GPU allocation remains. Stage 17 had saved **2/43** participant folds of the two-GPU run; they are kept and `--resume` reuses them. To continue, relaunch `.tmp/study_speedup.py` in the `sensor-study-20261029` tmux session from a shell with a live SSH agent; stage 17 then claims both GPUs again with 3 fits per GPU, and its workers start on CPUs 0–7 (the 16-core widening was applied to the stopped processes and must be repeated).

Before the stop: The queue has completed **36/48 nodes** including the internal provenance action; 12 remain. Random Forest, cross-session, fixed-layout, redundancy, participant extension, and the rest-class curve have finished.

**Selection baselines restarted from participant 1 on two GPUs** (user request, 2026-10-30 08:18 UTC). All compute runs on vishc-server-2. `17_selection_baselines` used both study GPUs (GPU 0 and GPU 1) and CPUs 0–7: two processes, one per GPU, splitting the 43 participant folds, with 3 concurrent subset fits per process. Arguments, seeds and the comparison model are unchanged; only `--workers` (1→2) and `--fit-workers` (1→3) changed. The nine folds from the earlier one-GPU run were archived, not deleted, in `outputs/rerun_20261029/superseded/selection_baselines_one_gpu_9of43_20261030/` and are not used by any later stage.

Checks before the restart:

- On participant 1, k=12 fits took 4.29 s each at 1 concurrent fit, 3.02 s at 2, 2.93 s at 3 and 2.91 s at 4, with identical Macro-F1 at every setting.
- On the two GPUs, a two-process, three-fit run on synthetic data gave exactly the same metrics and random-subset rows as a one-process, one-fit run (`operations/staged_two_gpu_selection/equivalence_check.log`).
- The coordinator change is recorded as a project-scope amendment in `source_amendments.json`, with its snapshot in `operations/project/.tmp/study_speedup.py`.

Measured: the first two participants (one per GPU) finished in **32.1 minutes**, against 51.7 minutes per participant on one GPU before. At that rate stage 17 takes about 11.5 hours (finishing around 2026-10-30 19:50 UTC); this is an extrapolation. At 09:11 UTC the user raised the stage's CPU budget from 8 to 16 cores; the running workers' affinity was widened in place (worker on GPU 1: CPUs 0,2,4,6,32–35; worker on GPU 0: CPUs 1,3,5,7,36–39) without a restart. CPUs 32–39 are outside the coordinator's own 0–7 pool, so they are not handed to other stages. `29_curve_w150` was stopped by the drain and resumes from its checkpoints once a GPU is free; the selection baselines claim both GPUs first because `20_faithfulness` and the statistics depend on them. Other GPU stages, statistics, reports and final verification follow, so there is still no reliable full-study completion time.

The coordinator's GPU allocation check needs a live forwarded SSH agent for `cecs-server1`. If that agent expires, new GPU stages wait and nothing is lost; the drain/relaunch in `operations/staged_two_gpu_selection/switch_to_two_gpu_selection.py --keep-code`, run from a shell with a working agent, restores it.

Full-channel mean Macro-F1 (43 participants): XGBoost **0.5423**, SVM **0.5378**, Random Forest **0.5016**. These current-run results have not yet passed final whole-study verification.

RF acceleration retained the original model and data parameters. Across different participants, mean recorded fit-and-predict time for both RF models was 675.1 seconds with 2 threads (participants 1–17) and 183.7 seconds with 8 threads (participants 18–41), about 3.67 times faster; these are observational groups, not a controlled benchmark. All 43 RF participant checkpoints passed validation.

The original code review passed **117 tests**. See [CODE_REVIEW.md](CODE_REVIEW.md). Live progress and active PIDs are in `outputs/rerun_20261029/status.json`; inspect its update timestamp when checking health.

Completed preparation:

- GRABMyo integrity: **30,715/30,715** checksum entries passed; zero missing/mismatched files.
- NinaPro DB5: **10/10 archives** passed official checksum verification; **30/30 MATLAB files** passed structural validation; **10 participants**, **16 EMG channels**, **200 Hz**. Resumable prefetch completed and exited.
- Primary 250 ms feature extraction: **15,351/15,351 recordings OK**, **598,689 windows**, **43 participants**, all **3 sessions**, **17 gestures** including rest. Cohort assertion passed. Active-class LOSO caches were built successfully.
- Recorded environment: Python **3.10.22**, all **12 package pins** verified, `pip check` passed, **53 regression tests passed**. Initial setup failures and successful retries remain preserved in logs.
- CUDA XGBoost: both selected GPUs passed the real-record smoke checks, with exactly one device visible per child. Smoke checks are not study results.
- LaTeX: the manuscript class and preamble compiled. Final numerical verification, manuscript build, comparison with delivered results and fresh rendered-page inspection remain pending.

Ready stages start as their inputs and resource slots become available, subject to resource availability and the cross-host GPU check. The same 47 experiment/report stages are retained, with an additional internal provenance-freeze action.

The isolated workspace is `outputs/rerun_20261029/workspace`. No delivered experimental results, numeric tables, acceptance records or feature caches were copied into it. The 47-stage queue follows the current raw-data run order, preserves frozen seeds/budgets/penalties, generates its own provenance, verifies through script16, builds reports and compares fresh participant metrics with the delivered results. The original historical outputs remain at the project root.

Attach: `tmux attach -t sensor-study-20261029`

Console: `tail -f outputs/rerun_20261029/console.log`

Per-stage logs: `outputs/rerun_20261029/logs/`.

Create `outputs/rerun_20261029/STOP` to prevent the next queue stage. A failed check stops the queue and records its stage/log; no partial outputs count as a completed study. Cross-host checks use the existing forwarded-agent connection and fail closed if that host cannot be checked. No private keys were copied.

Temporary/cache environment paths point into this project's `.tmp/` on the Linux filesystem. There is no E: mount here. The existing conda installation remains at its original location. These configured paths do not relocate application-managed state. Official acquisition code can retain in-progress archive files alongside raw archives; final data remain in the isolated workspace.

Source datasets: [GRABMyo v1.1.0](https://physionet.org/content/grabmyo/1.1.0/) and [NinaPro DB5](https://zenodo.org/records/1000116). Optional unexecuted CNN/IG analyses and archived putEMG are outside the current two-dataset protocol.
