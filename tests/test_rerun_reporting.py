"""Independent reruns must report current evidence rather than historical conclusions."""
import importlib
import json
from pathlib import Path

import pandas as pd


def reporting():
    path = Path(__file__).parents[1] / 'src/semg_sparse/reporting.py'
    assert path.exists(), 'Rerun-aware reporting is missing'
    return importlib.import_module('src.semg_sparse.reporting')


def test_runtime_metadata_uses_matching_scheduler_state(tmp_path):
    m = reporting()
    work = tmp_path / 'workspace'
    work.mkdir()
    state = {'workspace': str(work), 'scheduler': 'test scheduler', 'cpus': [2, 3],
             'gpus': ['gpu-unit'], 'active': {'build': {'pid': 123, 'cpus': [2, 3], 'gpus': []}}}
    (tmp_path / 'status.json').write_text(json.dumps(state))
    evidence = m.runtime_evidence(work)
    assert evidence['scope'] == 'independent rerun'
    assert evidence['configured_cpu_set'] == [2, 3]
    assert evidence['configured_gpu_uuids'] == ['gpu-unit']
    assert 'RF_parallelism' not in evidence
    assert 'one experiment track' not in json.dumps(evidence)


def test_foreign_runtime_state_is_not_attributed_to_build(tmp_path):
    m = reporting()
    (tmp_path / 'status.json').write_text(json.dumps({'workspace': '/another/run'}))
    evidence = m.runtime_evidence(tmp_path / 'workspace')
    assert evidence['scope'] == 'standalone build; no matching scheduler state'


def test_independent_claims_follow_current_ni_and_interval(tmp_path):
    m = reporting()
    tables = {'primary_matched_noninferiority': pd.DataFrame([
        {'condition': 'shap12', 'margin': .02, 'ni_percentile_ci': False},
        {'condition': 'geom12', 'margin': .02, 'ni_percentile_ci': True}]),
        'primary_selection_comparison': pd.DataFrame([{'mean_diff': -.05, 'lcb95': -.1, 'ucb95': -.01}]),
        'kstar_audit': pd.DataFrame([{'condition': 'geometric_primary', 'kstar_percentile': None}])}
    m.write_independent_reports(tmp_path, tables, {'scope': 'independent rerun'})
    claims = pd.read_csv(tmp_path / 'claim_evidence_matrix.csv')
    assert claims.set_index('Claim').loc['SHAP12 mean NI at margin 0.02', 'Decision'] == 'Not established'
    assert claims.set_index('Claim').loc['Geometric12 mean NI at margin 0.02', 'Decision'] == 'Established under the evaluated mean-CI rule'
    assert claims.set_index('Claim').loc['SHAP12 minus geometric12 mean difference', 'Decision'] == 'Negative mean interval excludes zero'
    for path in tmp_path.glob('*.md'):
        text = path.read_text()
        assert '53 tests' not in text
        assert '43/43 folds unchanged' not in text
    assert 'independent rerun' in (tmp_path / '04_statistical_validation.md').read_text()
