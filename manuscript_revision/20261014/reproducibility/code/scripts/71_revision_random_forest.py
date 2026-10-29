"""Fixed-count random-forest sensitivity; CPU-only, pre-existing parameters, unchanged XGB layout."""
from pathlib import Path
import importlib.util,json,sys,time,hashlib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score,accuracy_score,balanced_accuracy_score
ROOT=Path(__file__).resolve().parent.parent;REV=ROOT/'manuscript_revision/20261014';OUT=REV/'experiments/alternative_classifier'
spec=importlib.util.spec_from_file_location('p3',ROOT/'scripts/26_sparse_sensor_curve.py');p3=importlib.util.module_from_spec(spec);spec.loader.exec_module(p3)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 OUT.mkdir(parents=True,exist_ok=True);manifest={'runner_sha256':sha(Path(__file__)),'protocol_sha256':sha(REV/'reproducibility/protocol_amendment_04.json'),'inputs':json.loads((REV/'reproducibility/input_hashes.json').read_text())};path=OUT/'input_manifest.json'
 if path.exists() and json.loads(path.read_text())!=manifest:raise RuntimeError('RF checkpoint manifest changed')
 path.write_text(json.dumps(manifest,indent=2),encoding='utf-8')
 X=np.load(ROOT/'data/cache/loso_X.npy',mmap_mode='r');y=np.load(ROOT/'data/cache/loso_y.npy',mmap_mode='r');s=np.asarray(np.load(ROOT/'data/cache/loso_subj.npy',mmap_mode='r'));ranks=pd.read_csv(ROOT/'artifacts/rankings/cross_fitted_rankings.csv');ranks=ranks[ranks['lambda']==0]
 mp=OUT/'participant_metrics.csv';rows=pd.read_csv(mp).to_dict('records') if mp.exists() else [];done={int(p) for p,g in pd.DataFrame(rows).groupby('participant_id') if len(g)==2} if rows else set()
 for pid in range(1,44):
  if pid in done:continue
  tr=s!=pid;te=~tr;tri=np.flatnonzero(tr);tei=np.flatnonzero(te);xt=np.asarray(X[tr],np.float32);yt=np.asarray(y[tr]);ix=p3.subsample(xt,yt,200000);xt=xt[ix];yt=yt[ix];xe=np.asarray(X[te],np.float32);ye=np.asarray(y[te]);ranking=list(map(int,ranks[ranks.outer_participant==pid].ranking.iloc[0].split(';')));new=[]
  for k in (12,16):
   ch=ranking[:k];cols=p3.channel_columns(ch);a=xt[:,cols];mu=a.mean(axis=0);sd=a.std(axis=0)+1e-8;model=RandomForestClassifier(n_jobs=2,**p3.RF_PARAMS);t=time.perf_counter();model.fit((a-mu)/sd,yt);yp=model.predict((xe[:,cols]-mu)/sd);seconds=time.perf_counter()-t
   dest=OUT/f'p{pid:02d}_k{k}.npz';tmp=dest.with_suffix('.tmp')
   with tmp.open('wb') as f:np.savez_compressed(f,row_index=tei,y_true=ye,y_pred=yp)
   tmp.replace(dest)
   new.append({'participant_id':pid,'channels_k':k,'channels':';'.join(map(str,ch)),'n_train_windows':len(yt),'n_test_windows':len(ye),'macro_f1':f1_score(ye,yp,average='macro',labels=range(16),zero_division=0),'accuracy':accuracy_score(ye,yp),'balanced_accuracy':balanced_accuracy_score(ye,yp),'weighted_f1':f1_score(ye,yp,average='weighted',zero_division=0),'fit_predict_seconds':seconds,'prediction_sha256':sha(dest)})
  rows=[r for r in rows if int(r['participant_id'])!=pid]+new;tmp=mp.with_suffix('.tmp');pd.DataFrame(rows).to_csv(tmp,index=False);tmp.replace(mp);print(f'{pid}/43: RF12 and RF16 predictions saved',flush=True)
 print('PASS: random-forest fixed-count sensitivity complete',flush=True)
if __name__=='__main__':main()
