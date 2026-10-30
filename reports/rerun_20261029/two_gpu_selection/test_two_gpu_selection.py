"""Equivalence test on the two study GPUs: two-process selection baselines == one-process run.

Synthetic data only; run while the study queue is drained so no extra GPU worker is added.
"""
import importlib.util, os, shutil, subprocess, sys
from pathlib import Path
import numpy as np, pandas as pd

SRC_WORK = Path('/home/26tri.tm/Sensor-Selection/outputs/rerun_20261029/workspace')
STAGED = Path(sys.argv[1])
OUT = Path(sys.argv[2])
PY = sys.executable
DEVICES = sys.argv[3].split(',')
ARGS = ['--device', 'cuda', '--workers', '1', '--k-values', '4,6', '--k-star', '6', '--n-random', '3',
        '--n-random-at-k-star', '4', '--srcfa-lambda', '0.5', '--fit-workers', '1', '--resume']

def make_work(root):
    (root / 'scripts').mkdir(parents=True)
    shutil.copy(SRC_WORK / 'scripts/27_selection_baselines.py', root / 'scripts')
    rng = np.random.default_rng(0)
    n_per, pids = 11000, [1, 2, 3, 4]
    y = rng.integers(0, 4, n_per * len(pids))
    X = rng.normal(size=(len(y), 160)).astype(np.float32) + y[:, None] * rng.normal(size=160).astype(np.float32) * 0.3
    subj = np.repeat(pids, n_per)
    (root / 'data/cache').mkdir(parents=True)
    np.save(root / 'data/cache/loso_X.npy', X); np.save(root / 'data/cache/loso_y.npy', y); np.save(root / 'data/cache/loso_subj.npy', subj)
    (root / 'artifacts/rankings').mkdir(parents=True)
    rows = [dict(outer_participant=p, **{'lambda': lam}, ranking=';'.join(map(str, rng.permutation(16) + 1)))
            for p in pids for lam in (0.0, 0.5)]
    pd.DataFrame(rows).to_csv(root / 'artifacts/rankings/cross_fitted_rankings.csv', index=False)

one, two = OUT / 'one', OUT / 'two'
for d in (one, two):
    shutil.rmtree(d, ignore_errors=True); make_work(d)
subprocess.run([PY, 'scripts/27_selection_baselines.py', *ARGS], cwd=one, check=True,
               env={**os.environ, 'CUDA_VISIBLE_DEVICES': DEVICES[0]})

spec = importlib.util.spec_from_file_location('staged', STAGED); m = importlib.util.module_from_spec(spec)
sys.modules['staged'] = m; spec.loader.exec_module(m)
m.WORK = two
os.environ['STUDY_GPU_UUIDS'] = ','.join(DEVICES)
os.environ['CUDA_VISIBLE_DEVICES'] = ','.join(DEVICES)
seen = []
real = m.DevicePool
class Spy(real):
    def __init__(self, *a):
        seen.append(a[1]); super().__init__(*a)
m.DevicePool = Spy
assert m.run_selection_baselines(ARGS) == 0
assert seen == [DEVICES], seen
key = ['participant_id', 'method', 'channels_k']
for name, k in (('selection_baseline_metrics.csv', key), ('random_subsets_raw.csv', ['participant_id', 'channels_k', 'draw'])):
    a = pd.read_csv(one / 'artifacts/selection_baselines' / name).drop(columns=['fit_seconds'], errors='ignore').sort_values(k).reset_index(drop=True)
    b = pd.read_csv(two / 'artifacts/selection_baselines' / name).drop(columns=['fit_seconds'], errors='ignore').sort_values(k).reset_index(drop=True)
    pd.testing.assert_frame_equal(a, b, check_exact=True)
    print('IDENTICAL', name, len(a), 'rows')
try:
    m.selection_argv(['--device', 'cuda'], 2); raise SystemExit('selection_argv accepted a command without --workers')
except ValueError:
    pass
a2 = m.selection_argv(ARGS, 2)
assert a2[ARGS.index('--workers') + 1] == '2' and a2[ARGS.index('--fit-workers') + 1] == str(m.SELECTION_FIT_WORKERS)
print('PASS two-process selection equivalence')
