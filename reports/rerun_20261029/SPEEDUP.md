# Scheduling changes requested on 2026-10-29

The initial queue waited for complete batches, leaving GPU 6 idle after the full-channel baseline while ranking continued on GPU 0. Ready CPU work also waited behind the GPU batch.

The replacement scheduler follows the same scientific commands and input dependencies. It gives remaining independent ranking folds to two processes, each with one explicit GPU UUID and a disjoint CPU set. The original ranking implementation, participant exclusions, five inner folds, seed, 200,000 training-window cap and 20,000 attribution-window cap remain unchanged. Completed per-participant checkpoint files are reused and their hashes are checked across the switch.

Other experiments start when their inputs are complete and resources are free, instead of waiting for unrelated work. At most two GPU workers and eight physical CPU cores are allocated in total. The earlier download has ended, so CPUs 0-7 are available for this study. CPU-only stages receive disjoint CPU sets alongside GPU work. Random-forest baseline parallelism changes from two threads per fit to one; classifier settings, sampling and seeds are unchanged.

The scheduler reads the original commands, checks the entire dependency graph for missing nodes and cycles, preserves completed stages and continues using the original logs/status paths. GPU ownership and total user GPU usage on both hosts are checked before each new GPU allocation. A conflict blocks that allocation. Computation failures stop the queue and retain logs/checkpoints. The existing STOP file mechanism prevents new stages while active tasks finish.

Three operational tests cover real worker isolation, overlapping CPU/GPU work within the resource budget, and dependency/completion enforcement. The successful full-study regression run remains applicable because scientific sources are unchanged; source hashes are verified again before launch. Measured post-switch progress, rather than an assumed factor, determines the actual speed improvement.

Operational implementation: `outputs/rerun_20261029/operations/study_speedup.py`. Live state: `outputs/rerun_20261029/status.json`. Session: `tmux attach -t sensor-study-20261029`.
