"""One-time continuation of the current GPU queue, not a scheduled recurring job."""
from pathlib import Path
import subprocess,sys,time
ROOT=Path(__file__).resolve().parent.parent;REV=ROOT/'manuscript_revision/20261014'
def main():
 while True:
  text=(REV/'experiments/sensitivity_analyses/queue_v3.log').read_text(errors='replace')
  if 'Traceback (most recent call last)' in text:raise RuntimeError('existing GPU queue failed')
  if 'PASS: all revision GPU experiments complete' in text:break
  time.sleep(15)
 print('RUN full primary geometric count curve',flush=True)
 with (REV/'experiments/sensitivity_analyses/geometric_full_curve.log').open('a',encoding='utf-8') as f:subprocess.run([sys.executable,str(ROOT/'scripts/79_primary_geometric_curve.py')],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,check=True)
 print('PASS: extended geometric GPU continuation complete',flush=True)
if __name__=='__main__':main()
