"""Resume must reach a fit on a fresh DB5 destination, without training test models."""
import importlib.util
from pathlib import Path
import sys

import pandas as pd
import pytest


@pytest.mark.parametrize('existing', [(), ('db5_full_channel_metrics.csv',),
                                     ('db5_full_channel_metrics.csv', 'db5_rankings.csv')])
def test_fresh_or_partial_resume_reaches_fit(tmp_path, monkeypatch, existing):
    spec = importlib.util.spec_from_file_location('db5_resume_test', Path(__file__).parents[1] / 'scripts/34_db5_replication.py')
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    feature_file = tmp_path / 'features.parquet'
    pd.DataFrame({'dataset': ['unit-test'] * 2, 'participant_id': [1, 2],
                  'session_id': [1, 1], 'gesture_id': [1, 1], 'trial_id': [1, 1],
                  'window_idx': [0, 0], 'ch1_MAV': [.1, .2]}).to_parquet(feature_file)
    out = tmp_path / 'results'
    out.mkdir()
    for name in existing:
        key = 'outer_participant' if name == 'db5_rankings.csv' else 'participant_id'
        pd.DataFrame({key: [1]}).to_csv(out / name, index=False)
    monkeypatch.setattr(m, 'FEATURES', feature_file)
    monkeypatch.setattr(m, 'OUT', out)
    # A valid interrupted run wrote this fingerprint before its first fit.
    import json
    (out / 'db5_sparse_curve.protocol.json').write_text(json.dumps(m.protocol_for(5, list(range(1, 17)))))
    monkeypatch.setattr(sys, 'argv', ['34_db5_replication.py', '--resume'])
    def fit_boundary(*args, **kwargs):
        raise RuntimeError('fit boundary reached')
    monkeypatch.setattr(m, 'fit_eval', fit_boundary)
    with pytest.raises(RuntimeError, match='fit boundary reached'):
        m.main()


def test_changed_db5_input_refuses_existing_protocol(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location('db5_protocol_test', Path(__file__).parents[1] / 'scripts/34_db5_replication.py')
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    features = tmp_path / 'features.parquet'
    features.write_bytes(b'first input')
    monkeypatch.setattr(m, 'FEATURES', features)
    path = tmp_path / 'db5_sparse_curve.csv'
    m.ensure_protocol(path, m.protocol_for(5, [1, 16]), True)
    features.write_bytes(b'changed input')
    with pytest.raises(ValueError, match='changed'):
        m.ensure_protocol(path, m.protocol_for(5, [1, 16]), True)


def test_db5_resume_cannot_mix_cpu_and_cuda(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location('db5_device_test', Path(__file__).parents[1] / 'scripts/34_db5_replication.py')
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    features = tmp_path / 'features.parquet'
    features.write_bytes(b'unit-test input')
    monkeypatch.setattr(m, 'FEATURES', features)
    path = tmp_path / 'db5_sparse_curve.csv'
    m.ensure_protocol(path, m.protocol_for(5, [1, 16], device='cuda'), True)
    with pytest.raises(ValueError, match='changed'):
        m.ensure_protocol(path, m.protocol_for(5, [1, 16], device='cpu'), True)
