"""Complete fixed geometric count curve under the primary protocol, amendment06."""
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
import importlib.util,hashlib,json,sys
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parent.parent;REV=ROOT/'manuscript_revision/20261014';OUT=REV/'experiments/geometric_curve'
def module(name,file):
 spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/file);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
p3=module('p3','26_sparse_sensor_curve.py');p4=module('p4','27_selection_baselines.py')
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def worker(pid,ranking):
 paths=tuple(str(ROOT/'data/cache'/name) for name in ['loso_X.npy','loso_y.npy','loso_subj.npy']);return p3.run_group((pid,[(0.,ranking)],[k for k in range(1,17) if k not in (12,16)],paths,'XGB','cuda',200000,2,4))
def main():
 OUT.mkdir(parents=True,exist_ok=True);inputs=json.loads((REV/'reproducibility/input_hashes.json').read_text());stamp={'inputs':inputs,'runner_sha256':sha(Path(__file__)),'amendment_sha256':sha(REV/'reproducibility/protocol_amendment_06.json'),'matched_prediction_metrics_sha256':sha(REV/'experiments/primary_predictions/participant_metrics.csv')}
 for rel,h in inputs.items():
  if sha(ROOT/rel)!=h:raise RuntimeError('geometry input changed: '+rel)
 mp=OUT/'input_manifest.json'
 if mp.exists() and json.loads(mp.read_text())!=stamp:raise RuntimeError('geometry resume manifest changed')
 mp.write_text(json.dumps(stamp,indent=2),encoding='utf-8');ranking=p4.geometric_selection(16);pd.DataFrame([{'outer_participant':p,'lambda':0.,'ranking':';'.join(map(str,ranking))} for p in range(1,44)]).to_csv(OUT/'rankings.csv',index=False)
 path=OUT/'sparse_curve_subject_metrics.csv';rows=pd.read_csv(path).to_dict('records') if path.exists() else [];done={int(pid) for pid,g in pd.DataFrame(rows).groupby('participant_id') if set(g.channels_k)==set(range(1,17))} if rows else set();matched=pd.read_csv(REV/'experiments/primary_predictions/participant_metrics.csv')
 for pid in range(1,44):
  if pid in done:continue
  with ProcessPoolExecutor(max_workers=1) as pool:new=pool.submit(worker,pid,ranking).result()
  for row in new:row.update(evaluation_source='new_primary_protocol_fit',source_condition='none')
  for k,name in [(12,'geom12'),(16,'full16')]:
   r=matched[(matched.participant_id==pid)&(matched.condition==name)].iloc[0];new.append({'participant_id':pid,'model':'M_XGB','lambda':0.,'channels_k':k,'channels':';'.join(map(str,ranking[:k])),**{key:float(r[key]) for key in ['macro_f1','accuracy','balanced_accuracy','weighted_f1']},'n_train_windows':int(r.n_train_windows),'n_test_windows':int(r.n_test_windows),'fit_seconds':0.,'evaluation_source':'matched_revision_prediction_reuse','source_condition':name})
  rows=[r for r in rows if int(r['participant_id'])!=pid]+new;tmp=path.with_suffix('.tmp');pd.DataFrame(rows).sort_values(['participant_id','channels_k']).to_csv(tmp,index=False);tmp.replace(path);print(f'{pid}/43: complete primary geometric count curve saved',flush=True)
 print('PASS: full primary geometric curve complete',flush=True)
if __name__=='__main__':main()
