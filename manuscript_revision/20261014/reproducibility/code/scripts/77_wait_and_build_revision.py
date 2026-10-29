"""Wait for existing experiment jobs, then perform the current revision's release build once."""
from pathlib import Path
import json,subprocess,sys,time
import pandas as pd
ROOT=Path(__file__).resolve().parent.parent;REV=ROOT/'manuscript_revision/20261014'
def coverage(path,col):
 if not path.exists():return 0
 try:return int(pd.read_csv(path)[col].nunique())
 except (OSError,pd.errors.EmptyDataError,pd.errors.ParserError):return 0

def main():
 previous=None
 while True:
  queue=(REV/'experiments/sensitivity_analyses/queue_v3.log').read_text(errors='replace');rf=(REV/'experiments/alternative_classifier_parallel_execution.log').read_text(errors='replace')
  geo_path=REV/'experiments/sensitivity_analyses/geometry_continuation.log';geo=geo_path.read_text(errors='replace') if geo_path.exists() else ''
  if 'Traceback (most recent call last)' in queue or 'Traceback (most recent call last)' in rf or 'Traceback (most recent call last)' in geo:raise RuntimeError('An experiment failed; preserve checkpoints and inspect its execution log')
  status={'geometric_curve':coverage(REV/'experiments/geometric_curve/sparse_curve_subject_metrics.csv','participant_id'),'window150':coverage(ROOT/'artifacts/completion_analyses/w150/sparse_curve_subject_metrics.csv','participant_id'),'matched_budget':coverage(REV/'experiments/matched_budget/participant_metrics.csv','participant_id'),'attribution_extension':coverage(REV/'experiments/attribution_extension/sparse_curve.csv','participant_id'),'RF':coverage(REV/'experiments/alternative_classifier/participant_metrics.csv','participant_id')}
  if status!=previous:
   print('Participant checkpoints: '+json.dumps(status),flush=True);previous=status
  (REV/'reports/live_experiment_status.json').write_text(json.dumps(status,indent=2),encoding='utf-8')
  if 'PASS: all revision GPU experiments complete' in queue and 'PASS: all RF sensitivity participants completed' in rf and 'PASS: extended geometric GPU continuation complete' in geo:
   if not all(n==43 for n in status.values()):raise ValueError('completion logs disagree with full participant coverage')
   break
  time.sleep(15)
 print('All experiment tracks completed; starting strict verification and compilation',flush=True)
 subprocess.run([sys.executable,str(ROOT/'scripts/69_build_revision.py')],cwd=ROOT,check=True)
 print('PASS: release built; visual inspection and final QC remain',flush=True)
if __name__=='__main__':main()
