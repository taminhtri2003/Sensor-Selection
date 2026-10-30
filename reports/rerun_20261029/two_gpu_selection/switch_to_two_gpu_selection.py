"""Move 17_selection_baselines from one GPU to two at a saved participant boundary.

Steps, each fail-closed:
  1. wait for the next fully saved baseline participant (no fold is lost);
  2. request the coordinator's cooperative HANDOFF drain and wait for HANDOFF_READY;
  3. install the staged coordinator and record it as a project-scope source amendment;
  4. on the two drained study GPUs, check that a two-process run on synthetic data matches a
     one-process run exactly; on failure, restore the previous coordinator;
  5. relaunch the queue in the study tmux session with this shell's SSH agent.

--keep-code skips steps 3-4: the same drain/relaunch then only refreshes the SSH agent.
"""
import argparse, csv, fcntl, hashlib, json, os, shutil, subprocess, sys, time
from pathlib import Path

ROOT = Path('/home/26tri.tm/Sensor-Selection')
RUN = ROOT / 'outputs/rerun_20261029'
WORK = RUN / 'workspace'
PY = '/home/26tri.tm/miniconda3/envs/sensor-selection/bin/python'
HERE = Path(__file__).resolve().parent
LIVE = ROOT / '.tmp/study_speedup.py'
SNAPSHOT = RUN / 'operations/project/.tmp/study_speedup.py'
AMENDMENTS = RUN / 'source_amendments.json'
OUT = WORK / 'artifacts/selection_baselines'
STATUS = RUN / 'selection_two_gpu_switch_status.json'
REASON = ('User-requested two-GPU speedup (2026-10-30): 17_selection_baselines participant folds '
          'split across two single-GPU processes; arguments, seeds, one fit per process and '
          'outputs unchanged')
sys.path.insert(0, str(ROOT))
from src.semg_sparse.execution.safety import assert_no_live_workers
from src.semg_sparse.execution.provenance import verify_sources


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def status(msg, **extra):
    d = dict(status=msg, updated_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), **extra)
    tmp = STATUS.with_suffix('.tmp')
    tmp.write_text(json.dumps(d, indent=2))
    tmp.replace(STATUS)
    print(json.dumps(d), flush=True)


def saved_participants():
    """Participants whose 24 metric rows and 800 random draws are both on disk, else None."""
    try:
        with (OUT / 'selection_baseline_metrics.csv').open(newline='') as f:
            metrics = list(csv.DictReader(f))
        with (OUT / 'random_subsets_raw.csv').open(newline='') as f:
            raw = list(csv.DictReader(f))
    except (OSError, csv.Error):
        return None
    rows, draws = {}, {}
    for r in metrics:
        rows.setdefault(int(float(r['participant_id'])), set()).add((r['method'], int(float(r['channels_k']))))
    for r in raw:
        draws.setdefault(int(float(r['participant_id'])), {}).setdefault(int(float(r['channels_k'])), set()).add(int(float(r['draw'])))
    if set(rows) != set(draws):
        return None
    for pid, keys in rows.items():
        if len(keys) != 24 or {k for _, k in keys} != {4, 6, 8, 12}:
            return None
        if any(draws[pid].get(k) != set(range(n)) for k, n in ((4, 100), (6, 100), (8, 100), (12, 500))):
            return None
    return len(rows)


def queue_state():
    return json.loads((RUN / 'status.json').read_text())


def install(staged):
    old, new = sha(LIVE), sha(staged)
    doc = json.loads(AMENDMENTS.read_text())
    backup = HERE / 'previous_study_speedup.py'
    shutil.copy2(LIVE, backup)
    shutil.copy2(staged, LIVE)
    shutil.copy2(staged, SNAPSHOT)
    doc['amendments'].append(dict(scope='project', path='.tmp/study_speedup.py', old_sha256=old,
                                  new_sha256=new, reason=REASON,
                                  applied_utc=time.strftime('%Y-%m-%dT%H:%M:%S+00:00', time.gmtime())))
    AMENDMENTS.write_text(json.dumps(doc, indent=2))
    return backup, old


def restore(backup, old):
    shutil.copy2(backup, LIVE)
    shutil.copy2(backup, SNAPSHOT)
    doc = json.loads(AMENDMENTS.read_text())
    if doc['amendments'] and doc['amendments'][-1]['new_sha256'] != old:
        doc['amendments'].pop()
    AMENDMENTS.write_text(json.dumps(doc, indent=2))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--keep-code', action='store_true')
    ap.add_argument('--now', action='store_true',
                    help='drain immediately instead of waiting for the next saved participant')
    args = ap.parse_args()
    lock = (ROOT / '.tmp/selection_handoff.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    base_spec = __import__('importlib.util').util.spec_from_file_location('base', ROOT / '.tmp/run_study_rerun.py')
    base = __import__('importlib.util').util.module_from_spec(base_spec)
    base_spec.loader.exec_module(base)
    staged = HERE / 'study_speedup.py'
    if not args.keep_code:
        verify_sources(WORK, ROOT, RUN)
        out = subprocess.run([PY, str(staged), '--plan'], capture_output=True, text=True, check=True)
        plan = {t['name']: t for t in json.loads(out.stdout)}
        if plan['17_selection_baselines']['gpu_workers'] != 2:
            raise RuntimeError('Staged plan does not give the baselines two GPUs')

    s = queue_state()
    if s.get('status') != 'RUNNING' or '17_selection_baselines' not in s.get('active', {}):
        raise RuntimeError('Queue is not running the selection baselines; nothing switched')
    if (RUN / 'STOP').exists() or (RUN / 'HANDOFF').exists():
        raise RuntimeError('Another stop or handoff is pending')
    initial = saved_participants()
    if initial is None:
        raise RuntimeError('Current baseline checkpoint is inconsistent; leave run untouched')
    status('WAITING_FOR_NEXT_CHECKPOINT', saved_participants=initial)
    while not args.now:
        s = queue_state()
        if s.get('status') != 'RUNNING' or '17_selection_baselines' not in s.get('active', {}):
            raise RuntimeError('Queue state changed while waiting; nothing switched')
        if (RUN / 'STOP').exists() or (RUN / 'HANDOFF').exists():
            raise RuntimeError('Another stop or handoff appeared; nothing switched')
        count = saved_participants()
        if count is not None and count > initial:
            break
        time.sleep(2)
    (RUN / 'HANDOFF').write_text(json.dumps({'reason': 'two-GPU selection baselines', 'pid': os.getpid()}))
    status('DRAIN_REQUESTED', saved_participants=saved_participants())
    while True:
        s = queue_state()
        if s.get('status') == 'HANDOFF_READY':
            break
        if s.get('status') in ('FAILED', 'STOPPED'):
            raise RuntimeError('Coordinator did not reach the handoff boundary: ' + s.get('status'))
        time.sleep(2)
    ex = (ROOT / '.tmp/sensor-study.lock').open('a')
    for _ in range(300):
        try:
            fcntl.flock(ex, fcntl.LOCK_EX | fcntl.LOCK_NB)
            break
        except BlockingIOError:
            time.sleep(.2)
    else:
        raise RuntimeError('Coordinator lock still held')
    assert_no_live_workers(WORK, s.get('active', {}))
    count = saved_participants()
    if count is None:
        raise RuntimeError('Checkpoint inconsistent after drain; queue left stopped for inspection')

    result = 'agent refresh only'
    if not args.keep_code:
        backup, old = install(staged)
        try:
            verify_sources(WORK, ROOT, RUN, required_project_sources=('.tmp/study_speedup.py',))
            base.gpu_gate(list(base.GPUS))
            scratch = ROOT / '.tmp/two_gpu_selection_check'
            shutil.rmtree(scratch, ignore_errors=True)
            env = base.env(None)
            env.update(OMP_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2', MKL_NUM_THREADS='2')
            check = subprocess.run(['taskset', '-c', '0-3', PY, str(HERE / 'test_two_gpu_selection.py'),
                                    str(LIVE), str(scratch), ','.join(base.GPUS)],
                                   env=env, capture_output=True, text=True, timeout=1800)
            (HERE / 'equivalence_check.log').write_text(check.stdout + check.stderr)
            if check.returncode or 'PASS two-process selection equivalence' not in check.stdout:
                raise RuntimeError('Two-GPU equivalence check failed; see equivalence_check.log')
            result = 'two-GPU coordinator installed; equivalence check passed'
        except Exception as exc:
            restore(backup, old)
            result = 'kept previous coordinator: ' + str(exc)
    (RUN / 'HANDOFF').unlink()
    ex.close()
    cmd = ('export TEMP=/home/26tri.tm/Sensor-Selection/.tmp TMP=/home/26tri.tm/Sensor-Selection/.tmp '
           'TMPDIR=/home/26tri.tm/Sensor-Selection/.tmp PYTHONDONTWRITEBYTECODE=1; exec taskset -c 0-7 '
           + PY + ' -u .tmp/study_speedup.py >> outputs/rerun_20261029/console.log 2>&1')
    subprocess.run(['tmux', 'new-window', '-d', '-t', 'sensor-study-20261029', '-n', 'queue', '-c', str(ROOT),
                    '-e', 'SSH_AUTH_SOCK=' + os.environ.get('SSH_AUTH_SOCK', ''), cmd], check=True)
    status('RESUMED', saved_participants=count, result=result)


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        status('FAILED', error=str(exc))
        raise
