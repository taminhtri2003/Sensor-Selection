"""Wait for this run's checkpointed experiments, then execute the strict build.

This is a local continuation of an active run, not a scheduler or recurring task.
"""
import subprocess
import sys
import time
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parent.parent


def main():
    previous=None
    while True:
        for name in ('p11_bipolar_completion_20260922.log','participant_attribution_20260922.log'):
            log=ROOT/'runs'/name
            if log.exists() and 'Traceback (most recent call last)' in log.read_text(errors='replace'):
                raise RuntimeError(f'experiment failed: {name}')
        counts=[]
        for relative,expected in (('bipolar/bipolar_sparse_curve.csv',43*4*8),
                                  ('participant_attribution/sparse_curve.csv',43*4*16)):
            path=ROOT/'artifacts'/relative
            try:
                count=len(pd.read_csv(path))
            except (FileNotFoundError,pd.errors.EmptyDataError,pd.errors.ParserError):
                count=0
            counts.append((count,expected))
        if counts!=previous:
            print(f'Checkpoint rows: bipolar={counts[0]}, participant attribution={counts[1]}',flush=True)
            previous=counts
        ready=all(n==expected for n,expected in counts)
        ready=ready and (ROOT/'artifacts/bipolar/bipolar_provenance.json').exists()
        ready=ready and (ROOT/'artifacts/participant_attribution/non_inferiority.csv').exists()
        if ready:
            break
        time.sleep(30)
    print('Experiments complete; starting strict study build.',flush=True)
    subprocess.run([sys.executable,str(ROOT/'scripts/55_complete_study.py')],cwd=ROOT,check=True)


if __name__=='__main__':
    main()
