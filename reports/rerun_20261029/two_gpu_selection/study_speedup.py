"""Resource scheduling for the existing study commands; scientific sources stay unchanged."""
import argparse
import csv
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
import fcntl
import importlib.util
import json
import multiprocessing as mp
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import traceback

ROOT = Path('/home/26tri.tm/Sensor-Selection')
RUN = ROOT / 'outputs/rerun_20261029'
WORK = RUN / 'workspace'
PYTHON = '/home/26tri.tm/miniconda3/envs/sensor-selection/bin/python'
sys.path.insert(0, str(ROOT))
from src.semg_sparse.execution.safety import (
    assert_no_live_workers, handoff_ready, process_identity, processes,
    terminate_groups, validate_completed,
)
from src.semg_sparse.execution.provenance import verify_sources

OPERATIONAL_SOURCES = (
    '.tmp/run_study_rerun.py', '.tmp/study_speedup.py', '.tmp/study_cuda_smoke.py',
    '.tmp/study_extension_penalty.py', '.tmp/compare_study_rerun.py', '.tmp/rf_eight_core.py',
    'src/semg_sparse/execution/safety.py', 'src/semg_sparse/execution/provenance.py',
    'src/semg_sparse/execution/comparison.py',
)


def verify_execution_sources():
    return verify_sources(WORK, ROOT, RUN, required_project_sources=OPERATIONAL_SOURCES)

def pin_worker(slots):
    device, cpus = slots.get(timeout=30)
    os.environ['CUDA_VISIBLE_DEVICES'] = device
    os.sched_setaffinity(0, set(cpus))

class DevicePool(ProcessPoolExecutor):
    """One process per explicit GPU UUID, with disjoint inherited CPU allocations."""
    def __init__(self, max_workers, devices, cpus):
        if not 1 <= max_workers <= 2 or max_workers != len(devices) or len(cpus) < max_workers:
            raise ValueError('Invalid GPU worker resource allocation')
        context = mp.get_context('fork')
        self.slots = context.Queue()
        for i, device in enumerate(devices):
            self.slots.put((device, cpus[i::max_workers]))
        super().__init__(max_workers=max_workers, mp_context=context,
                         initializer=pin_worker, initargs=(self.slots,))

@dataclass
class Task:
    name: str
    command: list
    deps: set
    gpu_count: int = 0
    cores: int = 2

def choose_ready(tasks, completed, running, free_gpus, free_cpus):
    selected = []
    gpu_slots, cpu_slots = list(free_gpus), list(free_cpus)
    for t in tasks:
        if t.name in completed or t.name in running or not t.deps <= completed:
            continue
        if t.gpu_count > len(gpu_slots) or t.cores > len(cpu_slots):
            continue
        gpus, cpus = gpu_slots[:t.gpu_count], cpu_slots[:t.cores]
        selected.append((t, gpus, cpus))
        gpu_slots = gpu_slots[t.gpu_count:]
        cpu_slots = cpu_slots[t.cores:]
    return selected

def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m

def run_rankings():
    devices = os.environ['STUDY_GPU_UUIDS'].split(',')
    cpus = sorted(os.sched_getaffinity(0))
    m = module('study_rankings', WORK / 'scripts/25_cross_fitted_ranking.py')
    m.ProcessPoolExecutor = lambda max_workers: DevicePool(max_workers, devices, cpus)
    sys.argv = [str(m.__file__), '--device', 'cuda', '--workers', str(len(devices)),
                '--inner-folds', '5', '--max-attrib', '20000', '--max-train', '200000', '--resume']
    print('SCHEDULING ONLY: per-process GPU UUIDs', devices, 'CPU set', cpus, flush=True)
    return m.main()

# Concurrent subset fits per GPU process (user decision 2026-10-30; measured on participant 1:
# 4.29 s/fit at 1, 3.02 at 2, 2.93 at 3, 2.91 at 4, identical Macro-F1 in every case).
SELECTION_FIT_WORKERS = 3

def selection_argv(original_args, workers):
    """The original baseline arguments with only process and concurrent-fit counts replaced."""
    args = list(original_args)
    if args.count('--workers') != 1 or args.count('--fit-workers') != 1 or '--resume' not in args:
        raise ValueError('Unexpected selection-baseline command: ' + ' '.join(args))
    args[args.index('--workers') + 1] = str(workers)
    args[args.index('--fit-workers') + 1] = str(SELECTION_FIT_WORKERS)
    return args

def run_selection_baselines(original_args):
    # Each participant fold is independent and seeded by participant id, so assigning folds
    # to two single-GPU processes changes scheduling only; fits are mapped back in task order.
    devices = os.environ['STUDY_GPU_UUIDS'].split(',')
    cpus = sorted(os.sched_getaffinity(0))
    m = module('study_selection_baselines', WORK / 'scripts/27_selection_baselines.py')
    m.ProcessPoolExecutor = lambda max_workers: DevicePool(max_workers, devices, cpus)
    sys.argv = [str(m.__file__), *selection_argv(original_args, len(devices))]
    print('SCHEDULING ONLY: per-process GPU UUIDs', devices, 'CPU set', cpus,
          'argv', sys.argv[1:], flush=True)
    return m.main()

def selection_progress():
    path = WORK / 'artifacts/selection_baselines/selection_baseline_metrics.csv'
    try:
        with path.open(newline='') as stream:
            rows = list(csv.DictReader(stream))
    except (OSError, csv.Error):
        return None
    counts = {}
    for row in rows:
        counts[row.get('participant_id')] = counts.get(row.get('participant_id'), 0) + 1
    return sum(1 for n in counts.values() if n == 24)

def task_graph(base):
    commands = []
    freeze = base.new_inputs
    base.group = lambda *items: commands.extend(items)
    base.new_inputs = lambda: commands.append(('freeze_inputs', [], None))
    base.save = lambda: None
    base.log = lambda message: None
    base.pipeline()
    # Dependencies express input availability, rather than unrelated batch completion.
    deps = {
        '00_tests': [], '01_grabmyo_integrity': ['00_tests'], '02_download_db5': ['00_tests'],
        '03_db5_cohort': ['02_download_db5'], '04_db5_signal': ['03_db5_cohort'],
        '05_cuda_gpu6': ['01_grabmyo_integrity'], '06_cuda_gpu0': ['01_grabmyo_integrity'],
        '07_features250': ['01_grabmyo_integrity'], '08_build_cache': ['07_features250'],
        '09_full_xgb': ['08_build_cache'], '10_rankings': ['08_build_cache'],
        '11_primary_curve': ['10_rankings'], '12_full_svmrf': ['08_build_cache'],
        '13_db5_features': ['04_db5_signal'], '14_bipolar_features': ['01_grabmyo_integrity'],
        '15_db5_fits': ['13_db5_features'], '16_bipolar_fits': ['14_bipolar_features'],
        '17_selection_baselines': ['11_primary_curve'], '18_cross_session': ['08_build_cache'],
        '19_stability': ['10_rankings'], '20_faithfulness': ['17_selection_baselines'],
        '21_original_fixed_layout': ['08_build_cache'], '22_fixed_layout_lambdas': ['21_original_fixed_layout'],
        '23_redundancy': ['08_build_cache'], '24_thresholds': ['04_db5_signal','01_grabmyo_integrity'],
        '25_participant_extension': ['11_primary_curve'], '26_features150': ['14_bipolar_features'],
        '27_features500': ['26_features150'], '28_completion_caches': ['08_build_cache','27_features500'],
        '29_curve_rest17': ['28_completion_caches','10_rankings'],
        '29_curve_w150': ['28_completion_caches','10_rankings'],
        '29_curve_w500': ['28_completion_caches','10_rankings'],
        '30_feature_chain': ['09_full_xgb','14_bipolar_features'],
        '31_primary_statistics': ['09_full_xgb','11_primary_curve','12_full_svmrf'],
        '32_secondary_statistics': ['17_selection_baselines','19_stability','20_faithfulness',
                                    '18_cross_session','15_db5_fits','16_bipolar_fits','11_primary_curve'],
        '33_penalty_diagnostic': ['25_participant_extension'],
        'freeze_inputs': ['11_primary_curve'],
        '34_revision_predictions': ['freeze_inputs'], '35_revision_matched_budget': ['freeze_inputs'],
        '36_revision_extension': ['freeze_inputs','25_participant_extension'],
        '37_revision_geometry': ['34_revision_predictions'],
        '37b_revision_penalty': ['36_revision_extension'],
        '38_revision_rf': ['freeze_inputs'], '39_revision_rf_scheduling': ['38_revision_rf'],
        '40_seed_diagnostic': ['22_fixed_layout_lambdas'],
        '41_current_raw_integrity': ['02_download_db5','01_grabmyo_integrity'],
        '42_build_verified_revision': ['31_primary_statistics','32_secondary_statistics','33_penalty_diagnostic',
            '29_curve_rest17','29_curve_w150','29_curve_w500','30_feature_chain','24_thresholds',
            '23_redundancy','35_revision_matched_budget','37_revision_geometry','37b_revision_penalty',
            '39_revision_rf_scheduling','40_seed_diagnostic','41_current_raw_integrity'],
        '43_compare_delivered_results': ['42_build_verified_revision'],
    }
    tasks = []
    for name, cmd, gpu in commands:
        if name not in deps:
            raise ValueError('Missing dependency definition: ' + name)
        count, cores = (0 if gpu is None else 1), 2
        if name == '10_rankings':
            cmd = [PYTHON, str(Path(__file__).resolve()), '--ranking-worker']
            count, cores = 2, 4
        if name == '38_revision_rf':
            cmd, cores = [PYTHON, str(ROOT / '.tmp/rf_eight_core.py')], 8
        if name == '17_selection_baselines':
            if Path(cmd[1]).as_posix() != 'scripts/27_selection_baselines.py':
                raise ValueError('Unexpected selection-baseline script: ' + cmd[1])
            selection_argv(cmd[2:], 2)
            cmd = [PYTHON, str(Path(__file__).resolve()), '--selection-worker', '--', *cmd[2:]]
            count, cores = 2, 8
        if name == '12_full_svmrf':
            cmd = list(cmd)
            cmd[cmd.index('--rf-jobs') + 1] = '1'
        if name in ('09_full_xgb', '12_full_svmrf'):
            cmd = [*cmd, '--resume']
        tasks.append(Task(name, cmd, set(deps[name]), count, cores))
    # The selection baselines gate the faithfulness/statistics chain, so they claim both GPUs first.
    tasks.sort(key=lambda task: (task.name != '38_revision_rf', task.name != '17_selection_baselines'))
    names = {t.name for t in tasks}
    if names != set(deps) or any(t.deps - names for t in tasks):
        raise ValueError('Dependency graph does not cover the original pipeline')
    # Check acyclicity before touching any live process.
    covered = set()
    while covered != names:
        ready = {t.name for t in tasks if t.deps <= covered}
        if ready <= covered:
            raise ValueError('Dependency cycle')
        covered |= ready
    return tasks, freeze

def execute(plan_only=False):
    base = module('original_study_queue', ROOT / '.tmp/run_study_rerun.py')
    tasks, freeze = task_graph(base)
    if plan_only:
        print(json.dumps([dict(name=t.name, command=t.command, dependencies=sorted(t.deps),
                               gpu_workers=t.gpu_count, cpu_cores=t.cores) for t in tasks], indent=2))
        return
    lock = (ROOT / '.tmp/sensor-study.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    state = json.loads((RUN / 'status.json').read_text())
    names = {t.name for t in tasks}
    completed = validate_completed(names, state['completed'])
    assert_no_live_workers(WORK, state.get('active', {}))
    verify_execution_sources()
    os.sched_setaffinity(0, set(range(8)))
    state.update(active={}, failed=[], cpus=list(range(8)), scheduler='dependency-aware; up to two GPU workers')
    state['coordinator'] = process_identity(os.getpid())
    state.pop('error', None)
    active = {}
    def save():
        state['completed'] = [t.name for t in tasks if t.name in completed]
        state['updated_utc'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        state['progress'] = {'10_rankings': {'completed_participants': len(list((WORK / 'artifacts/rankings/cross_fitted_checkpoints').glob('outer_*.json'))), 'total_participants': 43},
                             '17_selection_baselines': {'completed_participants': selection_progress(), 'total_participants': 43}}
        tmp = RUN / 'status.tmp'
        tmp.write_text(json.dumps(state, indent=2))
        tmp.replace(RUN / 'status.json')
    def log(text):
        print(time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), text, flush=True)
    previous_sigterm = signal.getsignal(signal.SIGTERM)
    previous_sigint = signal.getsignal(signal.SIGINT)
    launching, pending_signal = False, None
    def sigterm(signum, frame):
        nonlocal pending_signal
        if launching:
            pending_signal = signum
            return
        raise SystemExit(128 + signum)
    signal.signal(signal.SIGTERM, sigterm)
    signal.signal(signal.SIGINT, sigterm)
    try:
        state['status'] = 'RUNNING'
        save()
        while not names <= completed:
            for name, (p, f) in list(active.items()):
                code = p.poll()
                if code is None:
                    continue
                info = state['active'][name]
                if code:
                    state['failed'].append({'stage': name, 'returncode': code})
                    raise RuntimeError(f'{name} failed with exit {code}; see {info["log"]}')
                if any(worker['pgid'] == info['pgid'] for worker in processes()):
                    continue
                f.close()
                del active[name]
                del state['active'][name]
                completed.add(name)
                log('PASS ' + name)
                save()
            if (RUN / 'HANDOFF').exists() and handoff_ready(active):
                # New coordinators support a boundary drain. The external launcher
                # starts the successor only after this process releases its lock.
                terminate_groups(state['active'], WORK)
                for name, (p, f) in active.items():
                    p.wait(timeout=10)
                    f.close()
                    state['active'][name]['terminated_for_handoff'] = True
                assert_no_live_workers(WORK, state['active'])
                state.update(status='HANDOFF_READY', study_complete=False)
                save()
                return
            if not (RUN / 'STOP').exists() and not (RUN / 'HANDOFF').exists():
                used_gpus = {g for info in state['active'].values() for g in info['gpus']}
                used_cpus = {c for info in state['active'].values() for c in info['cpus']}
                free_gpus = [g for g in base.GPUS if g not in used_gpus]
                free_cpus = [c for c in range(8) if c not in used_cpus]
                ready = choose_ready(tasks, completed, set(active), free_gpus, free_cpus)
                for t, gpus, cpus in ready:
                    if (RUN / 'STOP').exists() or (RUN / 'HANDOFF').exists():
                        break
                    verify_execution_sources()
                    if t.name == 'freeze_inputs':
                        freeze()
                        completed.add(t.name)
                        log('PASS freeze_inputs (independent rerun fingerprints)')
                        save()
                        continue
                    if gpus:
                        try:
                            base.gpu_gate(gpus)
                            state.pop('gpu_allocation_wait', None)
                        except Exception as exc:
                            state['gpu_allocation_wait'] = str(exc)
                            continue
                    if (RUN / 'STOP').exists() or (RUN / 'HANDOFF').exists():
                        break
                    dest = RUN / 'logs' / (t.name + '.log')
                    f = dest.open('a')
                    f.write('\nDEPENDENCY SCHEDULER COMMAND ' + json.dumps(t.command) + '\n')
                    f.flush()
                    e = base.env(None)
                    e.update(CUDA_VISIBLE_DEVICES=','.join(gpus), STUDY_GPU_UUIDS=','.join(gpus),
                             OMP_NUM_THREADS='2' if gpus else '1', OPENBLAS_NUM_THREADS='2' if gpus else '1',
                             MKL_NUM_THREADS='2' if gpus else '1', NUMEXPR_NUM_THREADS='2' if gpus else '1')
                    command = ['taskset','-c',','.join(map(str,cpus)), *t.command]
                    # Defer cooperative signals until ownership is durably recorded.
                    # Unlike masking, this does not pass blocked signals to the child.
                    launching = True
                    try:
                        p = subprocess.Popen(command, cwd=WORK, env=e, stdout=f, stderr=subprocess.STDOUT, start_new_session=True)
                        active[t.name] = (p, f)
                        identity = process_identity(p.pid) or {'pid': p.pid, 'pgid': p.pid}
                        state['active'][t.name] = dict(**identity, gpus=gpus, gpu=gpus[0] if len(gpus)==1 else None,
                            cpus=cpus, command=t.command, log=str(dest))
                        log(f'START {t.name} pid={p.pid} GPUs={gpus} CPUs={cpus}')
                        save()
                    finally:
                        launching = False
                    if pending_signal is not None:
                        raise SystemExit(128 + pending_signal)
            if (RUN / 'STOP').exists() and not active:
                state['status'] = 'STOPPED'
                save()
                return
            save()
            time.sleep(5)
        state.update(status='NUMERICAL_BUILD_COMPLETE_PENDING_VISUAL_REVIEW', study_complete=False)
        save()
    except BaseException as exc:
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        terminate_groups(state['active'], WORK)
        for name, (p, f) in active.items():
            try:p.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(p.pid, signal.SIGKILL)
                p.wait()
            f.close()
            state['active'][name]['terminated_after_queue_failure'] = True
        state.update(status='STOPPED' if isinstance(exc, SystemExit) else 'FAILED', error=str(exc), study_complete=False)
        save()
        raise
    finally:
        signal.signal(signal.SIGTERM, previous_sigterm)
        signal.signal(signal.SIGINT, previous_sigint)
        lock.close()

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--ranking-worker', action='store_true')
    ap.add_argument('--selection-worker', action='store_true',
                    help='run the original selection-baseline arguments given after -- on two GPUs')
    ap.add_argument('--plan', action='store_true')
    ap.add_argument('--handoff-request', action='store_true',
                    help='request a future coordinator to drain at a resumable boundary; sends no signals')
    argv = sys.argv[1:]
    passthrough = argv[argv.index('--') + 1:] if '--' in argv else []
    args = ap.parse_args(argv[:argv.index('--')] if '--' in argv else argv)
    try:
        if args.handoff_request:
            (RUN / 'HANDOFF').write_text(json.dumps({'requester': process_identity(os.getpid()),
                'requested_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}, indent=2))
            print('Handoff requested; coordinator must reach HANDOFF_READY and exit before replacement', flush=True)
            sys.exit(0)
        if args.ranking_worker:
            sys.exit(run_rankings())
        if args.selection_worker:
            sys.exit(run_selection_baselines(passthrough))
        execute(args.plan)
    except Exception:
        traceback.print_exc()
        raise
