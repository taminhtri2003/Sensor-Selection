"""Current-run provenance and reports, independent of historical narrative templates."""
import json
import math
import os
from pathlib import Path
import shutil

import pandas as pd


def runtime_evidence(workspace):
    workspace = Path(workspace).resolve()
    evidence = {'scope': 'standalone build; no matching scheduler state',
                'current_process': {
                    'cpu_affinity': sorted(os.sched_getaffinity(0)) if hasattr(os, 'sched_getaffinity') else None,
                    'cuda_visible_devices': os.environ.get('CUDA_VISIBLE_DEVICES'),
                    'thread_limits': {key: os.environ.get(key) for key in (
                        'OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS')}}}
    status = workspace.parent / 'status.json'
    if status.exists():
        state = json.loads(status.read_text())
        if Path(state.get('workspace', '')).resolve() == workspace:
            evidence.update(scope='independent rerun', scheduler=state.get('scheduler'),
                            configured_cpu_set=state.get('cpus'), configured_gpu_uuids=state.get('gpus'),
                            active_at_build={name: {key: value for key, value in info.items()
                                                   if key in ('pid', 'gpus', 'gpu', 'cpus', 'command')}
                                             for name, info in state.get('active', {}).items()})
    return evidence


def snapshot_run_provenance(workspace, destination):
    """Keep execution helpers and their amendment history with the new scientific package."""
    workspace, destination = Path(workspace), Path(destination)
    evidence = runtime_evidence(workspace)
    if evidence['scope'] != 'independent rerun':
        return evidence
    source = workspace.parent
    destination.mkdir(parents=True, exist_ok=True)
    for name in ('source_manifest.json', 'source_amendments.json', 'scheduling_change.json',
                 'environment.json', 'status.json', 'gpu_checks.jsonl'):
        if (source / name).is_file():
            shutil.copy2(source / name, destination / name)
    for name in ('operations', 'source_versions'):
        if (source / name).is_dir():
            shutil.copytree(source / name, destination / name, dirs_exist_ok=True)
    return evidence


def _boolean(value):
    if str(value).lower() in ('true', '1'):
        return True
    if str(value).lower() in ('false', '0'):
        return False
    raise ValueError('Non-inferiority decision must be a recorded boolean')


def write_independent_reports(destination, tables, evidence):
    """Render current full-precision evidence and derive only supported mean-level claims."""
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    matched = tables['primary_matched_noninferiority']
    direct = tables['primary_selection_comparison']
    claims = []
    for condition, title in (('shap12', 'SHAP12'), ('geom12', 'Geometric12')):
        row = matched[(matched.condition == condition) & (matched.margin == .02)]
        if len(row) != 1:
            raise ValueError('Missing or duplicate matched non-inferiority condition: ' + condition)
        decision = 'Established under the evaluated mean-CI rule' if _boolean(row.iloc[0].ni_percentile_ci) else 'Not established'
        claims.append({'Claim': title + ' mean NI at margin 0.02', 'Decision': decision,
                       'Source': 'experiments/statistics/primary_matched_noninferiority.csv'})
    if len(direct) != 1:
        raise ValueError('Direct mean comparison must contain exactly one row')
    lo, hi = float(direct.iloc[0].lcb95), float(direct.iloc[0].ucb95)
    if not math.isfinite(lo) or not math.isfinite(hi) or lo > hi:
        raise ValueError('Invalid direct-comparison mean interval')
    decision = ('Positive mean interval excludes zero' if lo > 0 else
                'Negative mean interval excludes zero' if hi < 0 else
                'Mean interval includes zero; direction not established')
    claims.append({'Claim': 'SHAP12 minus geometric12 mean difference', 'Decision': decision,
                   'Source': 'experiments/statistics/primary_selection_comparison.csv'})
    matrix = pd.DataFrame(claims)
    matrix.to_csv(destination / 'claim_evidence_matrix.csv', index=False)
    intro = ('This is an independent rerun. Numerical tables below come from the current result files; '
             'historical conclusions, events and test counts are not carried forward as fresh evidence. '
             'Participant-level mean inference does not establish preservation for each person or gesture. '
             'The frozen protocol and its disclosed development limitations remain applicable.\n\n')
    content = '# Statistical validation: independent rerun\n\n' + intro
    for name, table in tables.items():
        content += '## ' + name.replace('_', ' ') + '\n\n'
        content += table.to_markdown(index=False, floatfmt='.6f') + '\n\n'
        content += f'Source: `experiments/statistics/{name}.csv`.\n\n'
    (destination / '04_statistical_validation.md').write_text(content, encoding='utf-8')
    (destination / '05_additional_experiments.md').write_text(
        '# Independent rerun execution scope\n\n' + intro +
        'The paired conditions and count curves are documented by the complete tables in report04. '
        'Missing minimum counts remain missing findings. No unexecuted CNN/IG, new-cohort, '
        'clinical or device result is inferred.\n\nExecution evidence at build time:\n\n```json\n' +
        json.dumps(evidence, indent=2) + '\n```\n', encoding='utf-8')
    (destination / '07_claim_evidence_matrix.md').write_text(
        '# Current-result claim evidence\n\n' + intro + matrix.to_markdown(index=False) +
        '\n\nOther exploratory effects and multiplicity decisions remain in the full-precision tables. '
        'Numerical build acceptance and fresh visual/narrative manuscript review are separate requirements.\n',
        encoding='utf-8')
