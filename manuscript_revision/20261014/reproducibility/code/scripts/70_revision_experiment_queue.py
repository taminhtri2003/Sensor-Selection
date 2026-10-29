"""Sequential GPU queue for the active manuscript revision; not a recurring scheduler."""
import sys,time,subprocess
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parent.parent;REV=ROOT/'manuscript_revision/20261014'
def run(args,name):
 p=REV/'experiments/sensitivity_analyses'/f'{name}.log';print('RUN',name,flush=True)
 with p.open('a',encoding='utf-8') as f:subprocess.run([sys.executable,*args],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,check=True)
def main():
 while True:
  log=(REV/'experiments/primary_predictions/execution.log').read_text(errors='replace')
  if 'Traceback (most recent call last)' in log:raise RuntimeError('Primary prediction experiment failed')
  p=REV/'experiments/primary_predictions/participant_metrics.csv'
  if p.exists() and len(pd.read_csv(p))==129:break
  time.sleep(30)
 run(['scripts/26_sparse_sensor_curve.py','--model','XGB','--device','cuda','--group-lambdas','--lambdas','0.0','--train-subsample','200000','--k-workers','4','--cache-dir','data/cache/w500','--out-dir','artifacts/completion_analyses/w500','--resume'],'window500_completion')
 run(['scripts/26_sparse_sensor_curve.py','--model','XGB','--device','cuda','--group-lambdas','--lambdas','0.0','--train-subsample','200000','--k-workers','4','--cache-dir','data/cache/w150','--out-dir','artifacts/completion_analyses/w150','--resume'],'window150_full_curve')
 run(['scripts/65_revision_matched_budget.py'],'matched_budget')
 run(['scripts/53_participant_attribution.py','--out-dir','manuscript_revision/20261014/experiments/attribution_extension'],'attribution_provenance_refit')
 print('PASS: all revision GPU experiments complete',flush=True)
if __name__=='__main__':main()
