"""Matched primary-budget predictions for revision experiments A/B/C; outer subjects excluded."""
import argparse,hashlib,importlib.util,json,sys,time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import f1_score,accuracy_score,balanced_accuracy_score
ROOT=Path(__file__).resolve().parent.parent
REV=ROOT/'manuscript_revision/20261014'
OUT=REV/'experiments/primary_predictions'
sys.path.insert(0,str(ROOT))
def mod(name,path):
 spec=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
p3=mod('p3','scripts/26_sparse_sensor_curve.py');p4=mod('p4','scripts/27_selection_baselines.py')
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def arrsha(a):return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def atomic_csv(d,path):
 tmp=path.with_suffix('.tmp');d.to_csv(tmp,index=False);tmp.replace(path)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--participants',default='');ap.add_argument('--resume',action='store_true');args=ap.parse_args()
 OUT.mkdir(parents=True,exist_ok=True)
 inputs=json.loads((REV/'reproducibility/input_hashes.json').read_text())
 for rel,h in inputs.items():
  if sha(ROOT/rel)!=h:raise RuntimeError('input changed: '+rel)
 stamp={'inputs':inputs,'runner_sha256':sha(Path(__file__)),'protocol_sha256':sha(REV/'reproducibility/exploratory_protocol.json'),'xgboost':xgb.__version__}
 manifest=OUT/'input_manifest.json'
 if manifest.exists() and json.loads(manifest.read_text())!=stamp:raise RuntimeError('Incompatible checkpoint manifest')
 manifest.write_text(json.dumps(stamp,indent=2),encoding='utf-8')
 X=np.load(ROOT/'data/cache/loso_X.npy',mmap_mode='r');y=np.load(ROOT/'data/cache/loso_y.npy',mmap_mode='r');s=np.asarray(np.load(ROOT/'data/cache/loso_subj.npy',mmap_mode='r'))
 ranks=pd.read_csv(ROOT/'artifacts/rankings/cross_fitted_rankings.csv');ref=pd.read_csv(ROOT/'artifacts/metrics/sparse_curve_subject_metrics.csv');ranks=ranks[ranks['lambda']==0];ref=ref[ref['lambda']==0]
 pids=[int(v) for v in args.participants.split(',') if v] or list(range(1,44))
 path=OUT/'participant_metrics.csv';rows=pd.read_csv(path).to_dict('records') if args.resume and path.exists() else []
 done={int(r['participant_id']) for r in rows if sum(int(z['participant_id'])==int(r['participant_id']) for z in rows)==3}
 geo=p4.geometric_selection(12)
 for pid in pids:
  if pid in done:continue
  te=s==pid;tr=~te;tri=np.flatnonzero(tr);tei=np.flatnonzero(te)
  xt=np.asarray(X[tr],np.float32);yt=np.asarray(y[tr]);ix=p3.subsample(xt,yt,200000);xt=xt[ix];yt=yt[ix];fitrows=tri[ix]
  xe=np.asarray(X[te],np.float32);ye=np.asarray(y[te]);ranking=list(map(int,ranks[ranks.outer_participant==pid].ranking.iloc[0].split(';')))
  subsets={'full16':list(range(1,17)),'shap12':ranking[:12],'geom12':geo}
  def fit(item):
   name,ch=item;cols=p3.channel_columns(ch);a=xt[:,cols];mu=a.mean(axis=0);sd=a.std(axis=0)+1e-8
   model=xgb.XGBClassifier(device='cuda',**p3.XGB_PARAMS);start=time.perf_counter();model.fit((a-mu)/sd,yt);fitsec=time.perf_counter()-start
   start=time.perf_counter();yp=model.predict((xe[:,cols]-mu)/sd);predsec=time.perf_counter()-start
   values={'macro_f1':f1_score(ye,yp,average='macro',labels=range(16),zero_division=0),'accuracy':accuracy_score(ye,yp),'balanced_accuracy':balanced_accuracy_score(ye,yp),'weighted_f1':f1_score(ye,yp,average='weighted',zero_division=0)}
   gap=0.
   if name!='geom12':
    old=ref[(ref.participant_id==pid)&(ref.channels_k==len(ch))].iloc[0]
    gap=max(abs(float(old[k])-float(v)) for k,v in values.items())
    if gap>1e-6:raise RuntimeError(f'Primary reproduction mismatch pid={pid} {name} gap={gap}; preserve checkpoint and investigate')
   dest=OUT/f'p{pid:02d}_{name}.npz';tmp=dest.with_suffix('.tmp')
   with tmp.open('wb') as f:np.savez_compressed(f,row_index=tei,y_true=ye,y_pred=yp)
   tmp.replace(dest)
   return {'participant_id':pid,'condition':name,'channels':';'.join(map(str,ch)),'channels_k':len(ch),'n_train_windows':len(yt),'n_test_windows':len(ye),**values,'fit_seconds':fitsec,'predict_seconds':predsec,'primary_reproduction_max_abs':gap,'train_index_sha256':arrsha(fitrows),'test_index_sha256':arrsha(tei),'scaler_mu_sha256':arrsha(mu),'scaler_sd_sha256':arrsha(sd),'prediction_sha256':sha(dest)}
  with ThreadPoolExecutor(max_workers=3) as ex:new=list(ex.map(fit,subsets.items()))
  rows=[r for r in rows if int(r['participant_id'])!=pid]+new;atomic_csv(pd.DataFrame(rows).sort_values(['participant_id','condition']),path)
  (OUT/f'p{pid:02d}_metadata.json').write_text(json.dumps({'participant_id':pid,'training_participants':sorted(set(s[fitrows].tolist())),'test_participants':[pid],'model_parameters':p3.XGB_PARAMS,'geometric_rule':'scripts/27_selection_baselines.py','ranking_source':'artifacts/rankings/cross_fitted_rankings.csv'},indent=2),encoding='utf-8')
  print(f'{pid}/43: matched predictions saved; maximum reproduction gap {max(r["primary_reproduction_max_abs"] for r in new):.3g}',flush=True)
 print('PASS: requested prediction folds complete',flush=True)
if __name__=='__main__':main()
