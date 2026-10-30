"""Checkpoint guards use tiny artificial tables; no study fits are run."""
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('sparse_curve_guards', ROOT / 'scripts/26_sparse_sensor_curve.py')
curve = importlib.util.module_from_spec(spec)
spec.loader.exec_module(curve)


def rows():
    return pd.DataFrame([
        dict(participant_id=p, model='M_XGB', **{'lambda': 0.}, channels_k=k,
             channels=';'.join(map(str, range(1, k + 1))), macro_f1=.5,
             accuracy=.5, balanced_accuracy=.5, weighted_f1=.5,
             n_train_windows=100, n_test_windows=10)
        for p, ks in ((1, (1, 2)), (2, (1,))) for k in ks])


def test_resume_discards_incomplete_groups_before_recomputation():
    saved, complete = curve.validated_resume_rows(rows(), [1, 2], [0.], [1, 2],
                                                 'XGB', {(1, 0.): [1, 2], (2, 0.): [1, 2]})
    assert complete == {(1, 0.)}
    assert saved.participant_id.tolist() == [1, 1]


@pytest.mark.parametrize('bad', ['duplicate', 'nan', 'subset', 'model', 'participant'])
def test_resume_rejects_corrupt_rows(bad):
    frame = rows()
    if bad == 'duplicate':
        frame = pd.concat([frame, frame.iloc[[0]]])
    elif bad == 'nan':
        frame.loc[0, 'macro_f1'] = np.nan
    elif bad == 'subset':
        frame.loc[0, 'channels'] = '2'
    elif bad == 'model':
        frame.loc[0, 'model'] = 'M_RF'
    else:
        frame.loc[0, 'participant_id'] = 3
    with pytest.raises(ValueError):
        curve.validated_resume_rows(frame, [1, 2], [0.], [1, 2], 'XGB',
                                    {(1, 0.): [1, 2], (2, 0.): [1, 2]})


def test_resume_requires_unchanged_fingerprint(tmp_path):
    target = tmp_path / 'curve.csv'
    target.write_text('old result')
    with pytest.raises(ValueError, match='fingerprint'):
        curve.ensure_protocol(target, {'budget': 1}, resume=True)
    target.unlink()
    curve.ensure_protocol(target, {'budget': 1}, resume=True)
    target.write_text('result')
    curve.ensure_protocol(target, {'budget': 1}, resume=True)
    with pytest.raises(ValueError, match='protocol'):
        curve.ensure_protocol(target, {'budget': 2}, resume=True)


def test_atomic_csv_keeps_old_result_if_serialization_fails(tmp_path, monkeypatch):
    target = tmp_path / 'curve.csv'
    target.write_text('old result')
    def fail(*args, **kwargs):
        raise RuntimeError('interrupted write')
    monkeypatch.setattr(pd.DataFrame, 'to_csv', fail)
    with pytest.raises(RuntimeError):
        curve.atomic_csv(rows(), target)
    assert target.read_text() == 'old result'
    assert list(tmp_path.iterdir()) == [target]
