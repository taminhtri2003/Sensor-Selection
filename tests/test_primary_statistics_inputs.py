"""Confirmatory input completeness is checked before any inference or writes."""
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('primary_stats_guards', ROOT / 'scripts/28_statistics.py')
stats = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stats)


def full_fixture():
    return pd.DataFrame([dict(participant_id=p, model=m, channels_k=16, macro_f1=.5)
                         for p in range(1, 44) for m in ('M_XGBoost', 'M_SVM', 'M_RandomForest')])


def curve_fixture():
    return pd.DataFrame([dict(participant_id=p, model='M_XGB', channels_k=k,
                              **{'lambda': lam}, macro_f1=.5)
                         for p in range(1, 44) for lam in (0., .25, .5, 1.)
                         for k in range(1, 17)])


def test_complete_confirmatory_grids_are_accepted():
    assert stats.validate_inputs(full_fixture(), curve_fixture()) == []


@pytest.mark.parametrize('missing', ['model', 'participant', 'lambda', 'k', 'curve'])
def test_missing_whole_confirmatory_groups_are_rejected(missing):
    full, curve = full_fixture(), curve_fixture()
    if missing == 'model': full = full[full.model != 'M_RandomForest']
    elif missing == 'participant': full = full[full.participant_id != 43]
    elif missing == 'lambda': curve = curve[curve['lambda'] != 1.]
    elif missing == 'k': curve = curve[curve.channels_k != 1]
    else: curve = None
    with pytest.raises(ValueError, match='incomplete|missing'):
        stats.validate_inputs(full, curve)


@pytest.mark.parametrize('bad', ['duplicate', 'nan', 'wrong_cohort'])
def test_corrupt_statistics_inputs_are_rejected_even_for_partial(bad):
    full = full_fixture()
    if bad == 'duplicate': full = pd.concat([full, full.iloc[[0]].assign(macro_f1=.9)])
    elif bad == 'nan': full.loc[0, 'macro_f1'] = np.nan
    else: full.loc[0, 'participant_id'] = 44
    with pytest.raises(ValueError):
        stats.validate_inputs(full, curve_fixture(), allow_partial=True)


def test_partial_remains_explicitly_provisional():
    full = full_fixture().query('participant_id < 4')
    curve = curve_fixture().query('participant_id < 4')
    assert stats.validate_inputs(full, curve, allow_partial=True)


def test_full_input_paths_do_not_include_tagged_audits(tmp_path):
    for name in ('loso_full_channel_subject_metrics_xgb.csv',
                 'loso_full_channel_subject_metrics_svmrf.csv',
                 'loso_full_channel_subject_metrics_audit.csv'):
        (tmp_path / name).touch()
    assert [p.name for p in stats.full_input_paths(tmp_path)] == [
        'loso_full_channel_subject_metrics_svmrf.csv', 'loso_full_channel_subject_metrics_xgb.csv']


@pytest.mark.parametrize('missing', ['curve', 'model', 'lambda', 'k'])
def test_main_refuses_incomplete_inputs_before_creating_outputs(tmp_path, monkeypatch, missing):
    metrics = tmp_path / 'metrics'
    metrics.mkdir()
    full, curve = full_fixture(), curve_fixture()
    if missing == 'model': full = full[full.model != 'M_RandomForest']
    elif missing == 'lambda': curve = curve[curve['lambda'] != 1.]
    elif missing == 'k': curve = curve[curve.channels_k != 1]
    full[full.model == 'M_XGBoost'].to_csv(metrics / 'loso_full_channel_subject_metrics_xgb.csv', index=False)
    full[full.model != 'M_XGBoost'].to_csv(metrics / 'loso_full_channel_subject_metrics_svmrf.csv', index=False)
    if missing != 'curve': curve.to_csv(metrics / 'sparse_curve_subject_metrics.csv', index=False)
    monkeypatch.setattr(stats, 'METRICS', metrics)
    monkeypatch.setattr(stats, 'OUT', tmp_path / 'statistics')
    monkeypatch.setattr(stats.sys, 'argv', ['28_statistics.py'])
    assert stats.main() == 3
    assert not stats.OUT.exists()
