"""Scheduling-only parallel implementation of the fixed script71 RF protocol."""
from concurrent.futures import ProcessPoolExecutor,as_completed
from pathlib import Path
import importlib.util,json,hashlib,sys,time
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score,accuracy_score,balanced_accuracy_score
ROOT=Path(__file__).resolve().parent.parent;REV=ROOT/'manuscript_revision/20261014';OUT=REV/'experiments/alternative_classifier'
spec=importlib.util.spec_from_file_location('p3',ROOT/'scripts/26_sparse_sensor_curve.py');p3=importlib.util.module_from_spec(spec);spec.loader.exec_module(p3)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def worker(pid):
 X=np.load(ROOT/'data/cache/loso_X.npy',mmap_mode='r');y=np.load(ROOT/'data/cache/loso_y.npy',mmap_mode='r');s=np.asarray(np.load(ROOT/'data/cache/loso_subj.npy',mmap_mode='r'));r=pd.read_csv(ROOT/'artifacts/rankings/cross_fitted_rankings.csv');r=r[(r['lambda']==0)&(r.outer_participant==pid)];ranking=list(map(int,r.ranking.iloc[0].split(';')))
 tr=s!=pid;te=~tr;tei=np.flatnonzero(te);xt=np.asarray(X[tr],np.float32);yt=np.asarray(y[tr]);ix=p3.subsample(xt,yt,200000);xt=xt[ix];yt=yt[ix];xe=np.asarray(X[te],np.float32);ye=np.asarray(y[te]);rows=[]
 for k in (12,16):
  ch=ranking[:k];cols=p3.channel_columns(ch);a=xt[:,cols];mu=a.mean(axis=0);sd=a.std(axis=0)+1e-8;model=RandomForestClassifier(n_jobs=2,**p3.RF_PARAMS);t=time.perf_counter();model.fit((a-mu)/sd,yt);yp=model.predict((xe[:,cols]-mu)/sd);seconds=time.perf_counter()-t;dest=OUT/f'p{pid:02d}_k{k}.npz';tmp=dest.with_suffix('.tmp')
  with tmp.open('wb') as f:np.savez_compressed(f,row_index=tei,y_true=ye,y_pred=yp)
  tmp.replace(dest);rows.append({'participant_id':pid,'channels_k':k,'channels':';'.join(map(str,ch)),'n_train_windows':len(yt),'n_test_windows':len(ye),'macro_f1':f1_score(ye,yp,average='macro',labels=range(16),zero_division=0),'accuracy':accuracy_score(ye,yp),'balanced_accuracy':balanced_accuracy_score(ye,yp),'weighted_f1':f1_score(ye,yp,average='weighted',zero_division=0),'fit_predict_seconds':seconds,'prediction_sha256':sha(dest)})
 (OUT/f'p{pid:02d}_worker_metrics.json').write_text(json.dumps(rows,indent=2),encoding='utf-8');return rows

def main():
 stamp=json.loads((OUT/'input_manifest.json').read_text());assert stamp['runner_sha256']==sha(ROOT/'scripts/71_revision_random_forest.py')
 manifest={'parallel_runner_sha256':sha(Path(__file__)),'protocol_amendment_sha256':sha(REV/'reproducibility/protocol_amendment_05.json'),'original_runner_sha256':stamp['runner_sha256'],'workers':3,'threads_per_fit':2};mp=OUT/'parallel_execution_manifest.json'
 if mp.exists() and json.loads(mp.read_text())!=manifest:raise RuntimeError('parallel RF source changed')
 mp.write_text(json.dumps(manifest,indent=2),encoding='utf-8');path=OUT/'participant_metrics.csv';rows=pd.read_csv(path).to_dict('records');done={int(pid) for pid,g in pd.DataFrame(rows).groupby('participant_id') if len(g)==2};print(f'Preserved {len(done)} completed participants from script71',flush=True)
 with ProcessPoolExecutor(max_workers=3) as ex:
  jobs={ex.submit(worker,pid):pid for pid in range(1,44) if pid not in done}
  for future in as_completed(jobs):
   pid=jobs[future];new=future.result();rows=[r for r in rows if int(r['participant_id'])!=pid]+new;tmp=path.with_suffix('.tmp');pd.DataFrame(rows).sort_values(['participant_id','channels_k']).to_csv(tmp,index=False);tmp.replace(path);done.add(pid);print(f'{len(done)}/43: completed RF participant {pid}',flush=True)
 print('PASS: all RF sensitivity participants completed',flush=True)
if __name__=='__main__':main()
