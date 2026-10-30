"""CPU-only regressions for execution ownership, resume and provenance."""
import hashlib
import importlib
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


def safety():
    return importlib.import_module('src.semg_sparse.execution.safety')


def fake_process(proc, pid, pgid, cwd, start=100):
    entry = proc / str(pid)
    entry.mkdir(parents=True)
    # /proc/PID/stat fields 3..22, including a command containing spaces.
    fields = ['S', '1', str(pgid), str(pgid)] + ['0'] * 15 + [str(start)]
    (entry / 'stat').write_text(f'{pid} (test worker) ' + ' '.join(fields))
    (entry / 'cmdline').write_bytes(b'python\0worker.py\0')
    (entry / 'cwd').symlink_to(cwd, target_is_directory=True)
    return entry


def test_restart_detects_orphaned_group_after_leader_disappears(tmp_path):
    work = tmp_path / 'workspace'; work.mkdir()
    proc = tmp_path / 'proc'; proc.mkdir()
    fake_process(proc, 102, 101, work)
    with pytest.raises(RuntimeError, match='102'):
        safety().assert_no_live_workers(work, {'task': {'pid': 101, 'pgid': 101}}, proc_root=proc)


def test_restart_detects_unrecorded_workspace_worker(tmp_path):
    work = tmp_path / 'workspace'; work.mkdir()
    proc = tmp_path / 'proc'; proc.mkdir()
    fake_process(proc, 102, 102, work)
    with pytest.raises(RuntimeError, match='102'):
        safety().assert_no_live_workers(work, {}, proc_root=proc)


def test_restart_ignores_current_coordinator_and_unrelated_process(tmp_path):
    work = tmp_path / 'workspace'; work.mkdir()
    proc = tmp_path / 'proc'; proc.mkdir()
    fake_process(proc, 102, 102, work)
    fake_process(proc, 103, 103, tmp_path)
    safety().assert_no_live_workers(work, {}, proc_root=proc, exclude_pids={102})


def test_process_identity_distinguishes_reused_pid(tmp_path):
    proc = tmp_path / 'proc'; proc.mkdir()
    fake_process(proc, 102, 101, tmp_path, start=777)
    identity = safety().process_identity(102, proc_root=proc)
    assert identity['pid'] == 102
    assert identity['ppid'] == 1
    assert identity['pgid'] == 101
    assert identity['start_ticks'] == 777


def test_unknown_completed_names_cannot_produce_completion():
    with pytest.raises(ValueError, match='Unknown'):
        safety().validate_completed({'a', 'b'}, {'bogus', 'other'})
    assert safety().validate_completed({'a', 'b'}, ['a']) == {'a'}


def test_handoff_waits_for_nonresumable_stages_only():
    assert not safety().handoff_ready({'12_full_svmrf': {}})
    assert not safety().handoff_ready({'38_revision_rf': {}})
    assert safety().handoff_ready({'10_rankings': {}, '11_primary_curve': {}})


def test_cleanup_rejects_pid_reuse_and_reaps_orphan_group(tmp_path):
    proc = tmp_path / 'proc'; proc.mkdir()
    work = tmp_path / 'workspace'; work.mkdir()
    fake_process(proc, 101, 101, tmp_path, start=888)
    signals = []
    safety().terminate_groups({'a': {'pid': 101, 'pgid': 101, 'start_ticks': 777}}, work,
                             proc_root=proc, send_signal=lambda *args: signals.append(args), timeout=0)
    assert signals == []
    (proc / '101' / 'stat').unlink(); (proc / '101' / 'cwd').unlink()
    (proc / '101' / 'cmdline').unlink(); (proc / '101').rmdir()
    fake_process(proc, 102, 101, work)
    safety().terminate_groups({'a': {'pid': 101, 'pgid': 101, 'start_ticks': 777}}, work,
                             proc_root=proc, send_signal=lambda *args: signals.append(args), timeout=0)
    assert {pgid for pgid, _ in signals} == {101}


def test_source_amendments_preserve_original_and_require_chains_and_snapshots(tmp_path):
    p = importlib.import_module('src.semg_sparse.execution.provenance')
    work = tmp_path / 'workspace'; work.mkdir()
    project = tmp_path / 'project'; project.mkdir()
    run = tmp_path / 'run'; run.mkdir()
    (work / 'science.py').write_text('old')
    old = hashlib.sha256(b'old').hexdigest()
    original = json.dumps({'sources': {'science.py': old}})
    (run / 'source_manifest.json').write_text(original)
    (work / 'science.py').write_text('new')
    (project / 'helper.py').write_text('helper')
    new = hashlib.sha256(b'new').hexdigest(); helper = hashlib.sha256(b'helper').hexdigest()
    changes = {'version': 1, 'amendments': [
        {'scope': 'workspace', 'path': 'science.py', 'old_sha256': old, 'new_sha256': new, 'reason': 'repair'},
        {'scope': 'project', 'path': 'helper.py', 'old_sha256': None, 'new_sha256': helper, 'reason': 'capture helper'},
    ]}
    (run / 'source_amendments.json').write_text(json.dumps(changes))
    with pytest.raises(RuntimeError, match='snapshot'):
        p.verify_sources(work, project, run, required_project_sources=['helper.py'])
    snapshot = run / 'operations/project/helper.py'; snapshot.parent.mkdir(parents=True)
    snapshot.write_text('helper')
    p.verify_sources(work, project, run, required_project_sources=['helper.py'])
    assert (run / 'source_manifest.json').read_text() == original
    changes['amendments'][0]['old_sha256'] = helper
    (run / 'source_amendments.json').write_text(json.dumps(changes))
    with pytest.raises(ValueError, match='chain'):
        p.verify_sources(work, project, run, required_project_sources=['helper.py'])


def test_comparison_rejects_empty_nonfinite_and_missing_grid():
    c = importlib.import_module('src.semg_sparse.execution.comparison')
    keys = ['participant_id', 'lambda', 'channels_k']
    expected = {'participant_id': [1, 2], 'lambda': [0.], 'channels_k': [1, 2]}
    good = pd.DataFrame([{'participant_id': p, 'lambda': 0., 'channels_k': k, 'macro_f1': .5}
                         for p in (1, 2) for k in (1, 2)])
    c.validate_grid(good, keys, expected, 'good')
    for bad in (good.iloc[:0], good.iloc[:-1], good.assign(macro_f1=np.nan),
                good.assign(macro_f1=np.inf), pd.concat([good, good.iloc[:1]])):
        with pytest.raises(ValueError):
            c.validate_grid(bad, keys, expected, 'bad')


def load_scheduler():
    import importlib.util
    import sys
    path = Path(__file__).resolve().parents[1] / '.tmp/study_speedup.py'
    spec = importlib.util.spec_from_file_location('execution_review_scheduler', path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_scheduler_rejects_unknown_stages_before_rewriting_status(tmp_path, monkeypatch):
    m = load_scheduler()
    (tmp_path / '.tmp').mkdir()
    run = tmp_path / 'run'; run.mkdir()
    original = json.dumps({'completed': ['unknown'], 'active': {'old': {'pid': 998877}}})
    (run / 'status.json').write_text(original)
    monkeypatch.setattr(m, 'ROOT', tmp_path); monkeypatch.setattr(m, 'RUN', run)
    monkeypatch.setattr(m, 'module', lambda *args: object())
    monkeypatch.setattr(m, 'task_graph', lambda base: ([m.Task('real', [], set())], None))
    with pytest.raises(ValueError, match='Unknown'):
        m.execute()
    assert (run / 'status.json').read_text() == original


def test_scheduler_refuses_live_workers_before_rewriting_status(tmp_path, monkeypatch):
    m = load_scheduler()
    (tmp_path / '.tmp').mkdir()
    run = tmp_path / 'run'; run.mkdir()
    original = json.dumps({'completed': [], 'active': {'old': {'pid': 998877}}})
    (run / 'status.json').write_text(original)
    monkeypatch.setattr(m, 'ROOT', tmp_path); monkeypatch.setattr(m, 'RUN', run)
    monkeypatch.setattr(m, 'module', lambda *args: object())
    monkeypatch.setattr(m, 'task_graph', lambda base: ([m.Task('real', [], set())], None))
    def refuse(*args, **kwargs):
        raise RuntimeError('live worker')
    monkeypatch.setattr(m, 'assert_no_live_workers', refuse, raising=False)
    with pytest.raises(RuntimeError, match='live worker'):
        m.execute()
    assert (run / 'status.json').read_text() == original


def isolated_scheduler(tmp_path, monkeypatch):
    from types import SimpleNamespace
    m = load_scheduler()
    (tmp_path / '.tmp').mkdir()
    run = tmp_path / 'run'; run.mkdir(); (run / 'logs').mkdir()
    work = run / 'workspace'; work.mkdir()
    (run / 'status.json').write_text(json.dumps({'completed': [], 'active': {}, 'failed': []}))
    monkeypatch.setattr(m, 'ROOT', tmp_path); monkeypatch.setattr(m, 'RUN', run)
    monkeypatch.setattr(m, 'WORK', work)
    monkeypatch.setattr(m, 'verify_execution_sources', lambda: None)
    monkeypatch.setattr(m, 'module', lambda *args: SimpleNamespace(GPUS=[], env=lambda gpu: os.environ.copy()))
    monkeypatch.setattr(m, 'task_graph', lambda base: ([m.Task('cpu', ['true'], set(), 0, 1)], None))
    return m, run


def test_handoff_request_drains_without_launching_new_work(tmp_path, monkeypatch):
    m, run = isolated_scheduler(tmp_path, monkeypatch)
    (run / 'HANDOFF').touch()
    m.execute()
    assert json.loads((run / 'status.json').read_text())['status'] == 'HANDOFF_READY'


def test_sigterm_handler_cleans_registered_groups_and_preserves_identity(tmp_path, monkeypatch):
    from types import SimpleNamespace
    import signal
    m, run = isolated_scheduler(tmp_path, monkeypatch)
    child = SimpleNamespace(pid=998877, poll=lambda: None, wait=lambda timeout=None: -15)
    monkeypatch.setattr(m.subprocess, 'Popen', lambda *args, **kwargs: child)
    real_identity = m.process_identity
    monkeypatch.setattr(m, 'process_identity', lambda pid: {'pid': pid, 'pgid': pid, 'start_ticks': 123,
                                                           'boot_id': 'test', 'cwd': str(m.WORK)}
                        if pid == child.pid else real_identity(pid))
    cleaned = []
    monkeypatch.setattr(m, 'terminate_groups', lambda active, work: cleaned.extend(active.values()))
    monkeypatch.setattr(m.time, 'sleep', lambda seconds: signal.getsignal(signal.SIGTERM)(signal.SIGTERM, None))
    with pytest.raises(SystemExit) as caught:
        m.execute()
    assert caught.value.code == 143
    assert cleaned[0]['start_ticks'] == 123
    state = json.loads((run / 'status.json').read_text())
    assert state['status'] == 'STOPPED'
    assert state['active']['cpu']['terminated_after_queue_failure']


def test_sigterm_during_spawn_is_deferred_until_child_is_registered(tmp_path, monkeypatch):
    from types import SimpleNamespace
    import signal
    m, run = isolated_scheduler(tmp_path, monkeypatch)
    child = SimpleNamespace(pid=998877, poll=lambda: None, wait=lambda timeout=None: -15)
    def spawn(*args, **kwargs):
        signal.getsignal(signal.SIGTERM)(signal.SIGTERM, None)
        return child
    monkeypatch.setattr(m.subprocess, 'Popen', spawn)
    real_identity = m.process_identity
    monkeypatch.setattr(m, 'process_identity', lambda pid: {'pid': pid, 'pgid': pid, 'start_ticks': 123,
                                                           'boot_id': 'test', 'cwd': str(m.WORK)}
                        if pid == child.pid else real_identity(pid))
    cleaned = []
    monkeypatch.setattr(m, 'terminate_groups', lambda active, work: cleaned.extend(active.values()))
    with pytest.raises(SystemExit):
        m.execute()
    assert cleaned and cleaned[0]['pid'] == child.pid


def test_restricted_sshd_requires_privileged_sshd_parent(tmp_path, monkeypatch):
    from types import SimpleNamespace
    m = safety()
    proc = tmp_path / 'proc'; proc.mkdir()
    child = fake_process(proc, 102, 102, tmp_path)
    (child / 'comm').write_text('sshd\n')
    parent = proc / '1'; parent.mkdir(); (parent / 'comm').write_text('sshd\n')
    original_stat = Path.stat
    def fake_stat(path, *args, **kwargs):
        if path == parent:
            return SimpleNamespace(st_uid=0)
        return original_stat(path, *args, **kwargs)
    monkeypatch.setattr(Path, 'stat', fake_stat)
    assert m.is_protected_system_daemon(child, 1, proc)
    (parent / 'comm').write_text('bash\n')
    assert not m.is_protected_system_daemon(child, 1, proc)


def test_unknown_restricted_cwd_fails_closed(tmp_path, monkeypatch):
    m = safety(); proc=tmp_path/'proc';proc.mkdir()
    fake_process(proc,102,102,tmp_path)
    old = Path.resolve
    def resolve(path, *args, **kwargs):
        if path.name == 'cwd': raise PermissionError('protected')
        return old(path,*args,**kwargs)
    monkeypatch.setattr(Path,'resolve',resolve)
    with pytest.raises(PermissionError): m.process_identity(102,proc)
