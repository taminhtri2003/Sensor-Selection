"""Linux coordinator ownership checks; never infer ownership from a PID alone."""
import os
from pathlib import Path
import signal
import time

NONRESUMABLE = frozenset({'09_full_xgb', '12_full_svmrf', '13_db5_features',
                         '14_bipolar_features', '26_features150', '27_features500',
                         '38_revision_rf', '21_original_fixed_layout', '22_fixed_layout_lambdas'})


def is_protected_system_daemon(entry, ppid, proc_root):
    """Identify protected SSH/systemd session helpers from their trusted parent."""
    try:
        name = (entry / 'comm').read_text().strip()
        parent = Path(proc_root) / str(ppid)
        parent_name = (parent / 'comm').read_text().strip()
        uid = parent.stat().st_uid
        if name == 'sshd' and parent_name == 'sshd' and uid == 0:
            return True
        if name == '(sd-pam)' and parent_name == 'systemd' and uid == os.getuid():
            return (parent / 'exe').resolve(strict=True) == Path('/usr/lib/systemd/systemd').resolve(strict=True)
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        return False
    return False


def process_identity(pid, proc_root=Path('/proc')):
    entry = Path(proc_root) / str(pid)
    try:
        if entry.stat().st_uid != os.getuid():
            return None
        fields = (entry / 'stat').read_text().rsplit(')', 1)[1].split()
        if fields[0] == 'Z':
            return None
        boot = Path(proc_root) / 'sys/kernel/random/boot_id'
        boot_id = boot.read_text().strip() if boot.exists() else None
        try:
            cwd = str((entry / 'cwd').resolve(strict=True))
        except FileNotFoundError:
            cwd = None
        except PermissionError:
            if not is_protected_system_daemon(entry, int(fields[1]), proc_root):
                raise
            cwd = None
        return {'pid': int(pid), 'ppid': int(fields[1]), 'pgid': int(fields[2]), 'start_ticks': int(fields[19]),
                'boot_id': boot_id, 'cwd': cwd}
    except (FileNotFoundError, ProcessLookupError):
        return None


def processes(proc_root=Path('/proc')):
    result = []
    for entry in Path(proc_root).iterdir():
        if entry.name.isdigit():
            info = process_identity(int(entry.name), proc_root)
            if info is not None:
                result.append(info)
    return result


def in_workspace(info, workspace):
    return bool(info['cwd'] and Path(info['cwd']).is_relative_to(Path(workspace).resolve()))


def assert_no_live_workers(workspace, recorded_active, proc_root=Path('/proc'), exclude_pids=()):
    """Fail closed on persisted process groups or unrecorded workspace processes."""
    groups = {int(info.get('pgid', info['pid'])) for info in recorded_active.values() if 'pid' in info}
    excluded = set(exclude_pids) | {os.getpid()}
    live = [p for p in processes(proc_root)
            if p['pid'] not in excluded and (p['pgid'] in groups or in_workspace(p, workspace))]
    if live:
        raise RuntimeError(f'Refusing coordinator restart with live workspace workers: {live}')


def validate_completed(stage_names, completed):
    known, done = set(stage_names), set(completed)
    unknown = done - known
    if unknown:
        raise ValueError('Unknown completed stages: ' + ', '.join(sorted(unknown)))
    return done


def handoff_ready(active, nonresumable=NONRESUMABLE):
    return not set(active) & set(nonresumable)


def terminate_groups(active, workspace, proc_root=Path('/proc'), send_signal=os.killpg, timeout=10):
    """Terminate only registered owned groups; escalate surviving descendants too."""
    groups = set()
    snapshot = processes(proc_root)
    for info in active.values():
        pid = int(info['pid']); pgid = int(info.get('pgid', pid))
        leader = next((p for p in snapshot if p['pid'] == pid), None)
        if leader is not None:
            if ('start_ticks' not in info or leader['start_ticks'] != info['start_ticks']
                    or info.get('boot_id') != leader.get('boot_id') or leader['pgid'] != pgid):
                continue
        elif not any(p['pgid'] == pgid and in_workspace(p, workspace) for p in snapshot):
            continue
        if pgid != os.getpgrp():
            groups.add(pgid)
    def signal_groups(selected, sig):
        for pgid in selected:
            try:
                send_signal(pgid, sig)
            except ProcessLookupError:
                pass
    signal_groups(groups, signal.SIGTERM)
    deadline = time.monotonic() + timeout
    while groups and time.monotonic() < deadline:
        groups &= {p['pgid'] for p in processes(proc_root)}
        if groups:
            time.sleep(.1)
    remaining = groups & {p['pgid'] for p in processes(proc_root)}
    signal_groups(remaining, signal.SIGKILL)
    return remaining
