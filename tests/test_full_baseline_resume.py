"""Full-channel resume uses prediction fixtures and never fits a model."""
import importlib.util
import json
from concurrent.futures import Future
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('full_baseline_resume', ROOT / 'scripts/24_full_channel_loso_parallel.py')
baseline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(baseline)


def result(pid=1):
    return [dict(participant_id=pid, model='M_XGBoost', channels_k=16,
                 macro_f1=1., accuracy=1., balanced_accuracy=1., weighted_f1=1.,
                 n_train_windows=3, n_test_windows=3, fit_seconds=1.25,
                 _pred=np.array([0, 1, 0], np.int16), _true=np.array([0, 1, 0], np.int16),
                 _sess=np.array([1, 2, 3], np.int16))]


def read(path, **overrides):
    args = dict(pid=1, want=['XGB'], row_index=np.array([0, 1, 2]),
                y_true=np.array([0, 1, 0]), sessions=np.array([1, 2, 3]),
                n_train=3, protocol_hash='protocol1')
    args.update(overrides)
    return baseline.load_fold_checkpoint(path, **args)


def test_complete_prediction_checkpoint_preserves_all_fit_outputs(tmp_path):
    path = tmp_path / 'outer_01.npz'
    original = result()
    baseline.write_fold_checkpoint(path, original, np.array([0, 1, 2]), 'protocol1')
    restored = read(path)
    assert len(restored) == 1
    for key, value in original[0].items():
        if isinstance(value, np.ndarray): np.testing.assert_array_equal(restored[0][key], value)
        else: assert restored[0][key] == value


@pytest.mark.parametrize('bad', ['protocol', 'identity', 'models', 'row_order', 'labels', 'sessions', 'metric', 'partial', 'torn'])
def test_corrupt_or_incomplete_checkpoint_is_refused(tmp_path, bad):
    path = tmp_path / 'outer_01.npz'
    values = result()
    if bad == 'metric': values[0]['macro_f1'] = .2
    if bad == 'partial': values = []
    baseline.write_fold_checkpoint(path, values, np.array([0, 1, 2]), 'protocol1')
    kwargs = {}
    if bad == 'protocol': kwargs['protocol_hash'] = 'protocol2'
    elif bad == 'identity': kwargs['pid'] = 2
    elif bad == 'models': kwargs['want'] = ['XGB', 'RF']
    elif bad == 'row_order': kwargs['row_index'] = np.array([2, 1, 0])
    elif bad == 'labels': kwargs['y_true'] = np.array([1, 1, 1])
    elif bad == 'sessions': kwargs['sessions'] = np.array([3, 2, 1])
    elif bad == 'torn': path.write_bytes(b'PK\x03\x04broken')
    with pytest.raises(ValueError): read(path, **kwargs)


def test_failed_atomic_checkpoint_write_preserves_previous_fit(tmp_path, monkeypatch):
    path = tmp_path / 'outer_01.npz'
    baseline.write_fold_checkpoint(path, result(), np.array([0, 1, 2]), 'protocol1')
    before = path.read_bytes()
    def fail(*args, **kwargs): raise RuntimeError('interrupted write')
    monkeypatch.setattr(np, 'savez_compressed', fail)
    with pytest.raises(RuntimeError):
        baseline.write_fold_checkpoint(path, result(), np.array([0, 1, 2]), 'protocol1')
    assert path.read_bytes() == before
    assert list(tmp_path.iterdir()) == [path]


def fixture_cache(tmp_path):
    paths = tuple(tmp_path / f'loso_{n}.npy' for n in ('X', 'y', 'subj', 'sess'))
    for path, values in zip(paths, (np.zeros((6, 2), np.float32), [0, 1, 0, 0, 1, 0],
                                   [1, 1, 1, 2, 2, 2], [1, 2, 3, 1, 2, 3])):
        np.save(path, values)
    return (*paths, ['ch1_A', 'ch2_A'])


def test_protocol_changes_with_data_model_or_settings(tmp_path):
    *paths, names = fixture_cache(tmp_path)
    stamp = baseline.checkpoint_protocol(paths, names, ['XGB'], 'cpu', 1)
    assert stamp != baseline.checkpoint_protocol(paths, names, ['RF'], 'cpu', 1)
    assert stamp != baseline.checkpoint_protocol(paths, names[::-1], ['XGB'], 'cpu', 1)
    changed = np.load(paths[0]); changed[0, 0] = 1; np.save(paths[0], changed)
    assert stamp != baseline.checkpoint_protocol(paths, names, ['XGB'], 'cpu', 1)


class InlinePool:
    def __init__(self, **kwargs): pass
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def submit(self, fn, job):
        future = Future()
        try: future.set_result(fn(job))
        except Exception as exc: future.set_exception(exc)
        return future


def test_main_recovers_completed_fits_and_rebuilds_predictions(tmp_path, monkeypatch):
    cache = fixture_cache(tmp_path)
    monkeypatch.setattr(baseline, 'build_cache', lambda: cache)
    monkeypatch.setattr(baseline, 'OUT_METRICS', tmp_path / 'metrics')
    monkeypatch.setattr(baseline, 'OUT_PRED', tmp_path / 'predictions')
    monkeypatch.setattr(baseline, 'ProcessPoolExecutor', InlinePool)
    calls = []
    def fitted(job): calls.append(job[0]); return result(job[0])
    monkeypatch.setattr(baseline, 'run_fold', fitted)
    monkeypatch.setattr(baseline.sys, 'argv', ['24_full_channel_loso_parallel.py', '--models', 'XGB', '--device', 'cpu', '--workers', '1'])
    assert baseline.main() == 0
    assert sorted(calls) == [1, 2]
    original = pd.read_parquet(baseline.OUT_PRED / 'loso_full_channel_predictions.parquet')
    original_metrics = pd.read_csv(baseline.OUT_METRICS / 'loso_full_channel_subject_metrics.csv')
    (baseline.OUT_PRED / 'loso_full_channel_predictions.parquet').unlink()
    (baseline.OUT_METRICS / 'loso_full_channel_subject_metrics.csv').unlink()
    calls.clear()
    monkeypatch.setattr(baseline.sys, 'argv', [*baseline.sys.argv, '--resume'])
    assert baseline.main() == 0
    assert calls == []
    restored = pd.read_parquet(baseline.OUT_PRED / 'loso_full_channel_predictions.parquet')
    pd.testing.assert_frame_equal(original.sort_values(list(original.columns)).reset_index(drop=True),
                                  restored.sort_values(list(restored.columns)).reset_index(drop=True))
    restored_metrics = pd.read_csv(baseline.OUT_METRICS / 'loso_full_channel_subject_metrics.csv')
    pd.testing.assert_frame_equal(original_metrics.sort_values('participant_id').reset_index(drop=True),
                                  restored_metrics.sort_values('participant_id').reset_index(drop=True))
    checkpoints = baseline.OUT_PRED / 'loso_full_channel_checkpoints'
    preserved = (checkpoints / 'outer_01.npz').read_bytes()
    (checkpoints / 'outer_02.npz').unlink()
    calls.clear()
    assert baseline.main() == 0
    assert calls == [2]
    assert (checkpoints / 'outer_01.npz').read_bytes() == preserved
    calls.clear()
    changed = np.load(cache[0]); changed[0, 0] = 9; np.save(cache[0], changed)
    with pytest.raises(ValueError, match='protocol'):
        baseline.main()
    assert calls == []
