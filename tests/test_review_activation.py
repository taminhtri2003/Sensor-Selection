"""Handoff tests never signal real processes or start training."""
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


def monitor():
    spec = importlib.util.spec_from_file_location('activation_unit_test', Path(__file__).parents[1] / '.tmp/activate_review.py')
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_child_before_chdir_is_not_hidden_from_handoff(monkeypatch, tmp_path):
    m = monitor()
    monkeypatch.setattr(m, 'WORK', tmp_path / 'workspace')
    monkeypatch.setattr(m, 'processes', lambda: [
        {'pid': 10, 'ppid': 1, 'pgid': 10, 'cwd': '/outside'},
        {'pid': 20, 'ppid': 10, 'pgid': 20, 'cwd': '/outside'},
        {'pid': 21, 'ppid': 20, 'pgid': 20, 'cwd': '/outside'}])
    assert m.unknown_workspace_groups({}, 10) == [20]
    assert m.unknown_workspace_groups({'stage': {'pid': 20}}, 10) == []


def test_freeze_waits_until_stopped_state_is_observed(monkeypatch):
    m = monitor()
    identity = {'pid': 10, 'start_ticks': 100, 'boot_id': 'test-boot'}
    monkeypatch.setattr(m, 'process_identity', lambda pid: identity)
    states = iter(['S', 'T'])
    observed = []
    def state(pid):
        result = next(states)
        observed.append(result)
        return result
    monkeypatch.setattr(m, 'process_state', state)
    monkeypatch.setattr(m.os, 'kill', lambda *args: None)
    monkeypatch.setattr(m.time, 'sleep', lambda seconds: None)
    m.stop_and_confirm(identity)
    assert observed == ['S', 'T']


def test_monitor_termination_is_cooperative():
    m = monitor()
    with pytest.raises(SystemExit) as exc:
        m.cooperative_termination(15, None)
    assert exc.value.code == 143


def test_deferred_source_stage_must_finish_before_handoff():
    m = monitor()
    plan = {'files': [{'after_stages': ['cpu_baseline', 'db5']}]}
    assert not m.deferred_ready(plan, ['cpu_baseline'])
    assert m.deferred_ready(plan, ['cpu_baseline', 'db5'])


def source_fixture(monkeypatch, tmp_path):
    m = monitor()
    root, run, work = tmp_path / 'project', tmp_path / 'run', tmp_path / 'run/workspace'
    root.mkdir(); work.mkdir(parents=True)
    monkeypatch.setattr(m, 'ROOT', root); monkeypatch.setattr(m, 'RUN', run); monkeypatch.setattr(m, 'WORK', work)
    (root / 'first.py').write_bytes(b'new')
    (work / 'first.py').write_bytes(b'old')
    digest = lambda value: hashlib.sha256(value).hexdigest()
    (run / 'source_manifest.json').write_text(json.dumps({'sources': {'first.py': digest(b'old')}}))
    (run / 'source_amendments.json').write_text(json.dumps({'version': 1, 'amendments': []}))
    plan = {'files': [{'path': 'first.py', 'sha256': digest(b'new'), 'after_stages': ['done']}]}
    return m, root, run, work, plan


def test_all_deferred_items_are_checked_before_first_write(monkeypatch, tmp_path):
    m, root, run, work, plan = source_fixture(monkeypatch, tmp_path)
    plan['files'].append({'path': 'missing.py', 'sha256': '0' * 64, 'after_stages': ['done']})
    with pytest.raises(FileNotFoundError):
        m.apply_deferred_sources(plan, ['done'])
    assert (work / 'first.py').read_bytes() == b'old'
    assert json.loads((run / 'source_amendments.json').read_text())['amendments'] == []


def test_partial_source_transaction_recovers_idempotently(monkeypatch, tmp_path):
    m, root, run, work, plan = source_fixture(monkeypatch, tmp_path)
    replace = Path.replace
    def fail_at_ledger(src, dst, *args, **kwargs):
        if Path(dst) == run / 'source_amendments.json':
            raise OSError('simulated interruption')
        return replace(src, dst, *args, **kwargs)
    with monkeypatch.context() as context:
        context.setattr(Path, 'replace', fail_at_ledger)
        with pytest.raises(OSError, match='simulated interruption'):
            m.apply_deferred_sources(plan, ['done'])
    assert (work / 'first.py').read_bytes() == b'new'
    assert json.loads((run / 'source_amendments.json').read_text())['amendments'] == []
    m.recover_source_transaction()
    m.recover_source_transaction()
    ledger = json.loads((run / 'source_amendments.json').read_text())
    assert ledger['amendments'][0]['new_sha256'] == hashlib.sha256(b'new').hexdigest()
    assert json.loads((run / 'review_source_transaction/journal.json').read_text())['state'] == 'COMMITTED'
