"""Restart 17_selection_baselines from participant 1 on two GPUs (user request 2026-10-30).

Run only while the queue is drained (status HANDOFF_READY, HANDOFF present, no live workers).
Installs the staged coordinator, checks two-process/three-fit equivalence on synthetic data,
archives the nine one-GPU folds, then relaunches the queue in the study tmux session.
"""
import fcntl, json, os, shutil, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import switch_to_two_gpu_selection as sw
from src.semg_sparse.execution.safety import assert_no_live_workers
from src.semg_sparse.execution.provenance import verify_sources

ARCHIVE = sw.RUN / 'superseded/selection_baselines_one_gpu_9of43_20261030'


def main():
    s = sw.queue_state()
    if s.get('status') != 'HANDOFF_READY' or not (sw.RUN / 'HANDOFF').exists():
        raise RuntimeError('Queue is not drained; nothing changed')
    lock = (sw.ROOT / '.tmp/sensor-study.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    assert_no_live_workers(sw.WORK, s.get('active', {}))
    base_spec = __import__('importlib.util').util.spec_from_file_location('base', sw.ROOT / '.tmp/run_study_rerun.py')
    base = __import__('importlib.util').util.module_from_spec(base_spec)
    base_spec.loader.exec_module(base)
    base.gpu_gate(list(base.GPUS))

    staged = HERE / 'study_speedup.py'
    if sw.sha(staged) != sw.sha(sw.LIVE):
        backup, old = sw.install(staged)
    verify_sources(sw.WORK, sw.ROOT, sw.RUN, required_project_sources=('.tmp/study_speedup.py',))

    scratch = sw.ROOT / '.tmp/two_gpu_selection_check'
    shutil.rmtree(scratch, ignore_errors=True)
    env = base.env(None)
    env.update(OMP_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2', MKL_NUM_THREADS='2')
    check = subprocess.run(['taskset', '-c', '0-7', sw.PY, str(HERE / 'test_two_gpu_selection.py'),
                            str(sw.LIVE), str(scratch), ','.join(base.GPUS)],
                           env=env, capture_output=True, text=True, timeout=1800)
    (HERE / 'equivalence_check.log').write_text(check.stdout + check.stderr)
    if check.returncode or 'PASS two-process selection equivalence' not in check.stdout:
        raise RuntimeError('Equivalence check failed; queue left drained. See equivalence_check.log')
    print(check.stdout, flush=True)

    out = sw.OUT
    ARCHIVE.mkdir(parents=True, exist_ok=False)
    for f in sorted(out.iterdir()):
        shutil.move(str(f), ARCHIVE / f.name)
    (ARCHIVE / 'README.md').write_text(
        'Superseded on 2026-10-30 at the user\'s request: 9/43 participant folds from the one-GPU '
        'run of 17_selection_baselines. Stage 17 was restarted from participant 1 on two GPUs '
        '(3 concurrent fits per GPU). Not used by any later stage.\n')
    with (sw.RUN / 'logs/17_selection_baselines.log').open('a') as f:
        f.write(f'\nRESTART FROM PARTICIPANT 1 {time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}: '
                f'previous folds archived in {ARCHIVE}\n')

    (sw.RUN / 'HANDOFF').unlink()
    lock.close()
    cmd = ('export TEMP=/home/26tri.tm/Sensor-Selection/.tmp TMP=/home/26tri.tm/Sensor-Selection/.tmp '
           'TMPDIR=/home/26tri.tm/Sensor-Selection/.tmp PYTHONDONTWRITEBYTECODE=1; exec taskset -c 0-7 '
           + sw.PY + ' -u .tmp/study_speedup.py >> outputs/rerun_20261029/console.log 2>&1')
    has = subprocess.run(['tmux', 'has-session', '-t', 'sensor-study-20261029'], capture_output=True).returncode == 0
    tmux = (['tmux', 'new-window', '-d', '-t', 'sensor-study-20261029'] if has
            else ['tmux', 'new-session', '-d', '-s', 'sensor-study-20261029'])
    subprocess.run([*tmux, '-n', 'queue', '-c', str(sw.ROOT),
                    '-e', 'SSH_AUTH_SOCK=' + os.environ.get('SSH_AUTH_SOCK', ''), cmd], check=True)
    sw.status('RESUMED', result='stage 17 restarted from participant 1 on two GPUs, 3 fits per GPU; '
                                'equivalence check passed', archived=str(ARCHIVE))


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        sw.status('FAILED', error=str(exc))
        raise
