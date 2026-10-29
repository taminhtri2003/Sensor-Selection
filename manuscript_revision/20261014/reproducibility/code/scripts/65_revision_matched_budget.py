"""Exploratory shared-model cross-fitted SHAP versus grouped permutation, revision D."""
import hashlib,importlib.util,json,sys,time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import GroupKFold
from sklearn.metrics import f1_score,accuracy_score,balanced_accuracy_score
ROOT=Path(__file__).resolve().parent.parent;REV=ROOT/'manuscript_revision/20261014';OUT=REV/'experiments/matched_budget';sys.path.insert(0,str(ROOT))
from src.semg_sparse.xai.cross_fitted import channel_importance_from_contribs
spec=importlib.util.spec_from_file_location('p3',ROOT/'scripts/26_sparse_sensor_curve.py');p3=importlib.util.module_from_spec(spec);spec.loader.exec_module(p3)
SEED=20260728

def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def ah(a):return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def save_csv(d,path):
 t=path.with_suffix('.tmp');d.to_csv(t,index=False);t.replace(path)
def person_macro(y,p,s):return float(np.mean([f1_score(y[s==pid],p[s==pid],labels=range(16),average='macro',zero_division=0) for pid in sorted(set(s.tolist()))]))
def main():
 OUT.mkdir(parents=True,exist_ok=True);inputs=json.loads((REV/'reproducibility/input_hashes.json').read_text())
 for rel,h in inputs.items():
  if sha(ROOT/rel)!=h:raise RuntimeError('Input changed: '+rel)
 stamp={'inputs':inputs,'code_sha256':sha(Path(__file__)),'protocol':sha(REV/'reproducibility/exploratory_protocol.json'),'amendment':sha(REV/'reproducibility/protocol_amendment_02.json'),'xgboost':xgb.__version__}
 mp=OUT/'input_manifest.json'
 if mp.exists() and json.loads(mp.read_text())!=stamp:raise RuntimeError('Matched-budget resume manifest mismatch')
 mp.write_text(json.dumps(stamp,indent=2),encoding='utf-8')
 X=np.load(ROOT/'data/cache/loso_X.npy',mmap_mode='r');y=np.load(ROOT/'data/cache/loso_y.npy',mmap_mode='r');subjects=np.asarray(np.load(ROOT/'data/cache/loso_subj.npy',mmap_mode='r'))
 old=pd.read_csv(ROOT/'artifacts/metrics/sparse_curve_subject_metrics.csv');old=old[old['lambda']==0]
 result_path=OUT/'participant_metrics.csv';score_path=OUT/'inner_scores.csv';rank_path=OUT/'rankings.csv';cost_path=OUT/'costs.csv'
 rows=pd.read_csv(result_path).to_dict('records') if result_path.exists() else [];scores=pd.read_csv(score_path).to_dict('records') if score_path.exists() else [];ranks=pd.read_csv(rank_path).to_dict('records') if rank_path.exists() else [];costs=pd.read_csv(cost_path).to_dict('records') if cost_path.exists() else []
 done={int(p) for p,g in pd.DataFrame(rows).groupby('participant_id') if len(g)==4} if rows else set()
 rows=[r for r in rows if int(r['participant_id']) in done];scores=[r for r in scores if int(r['outer_participant']) in done];ranks=[r for r in ranks if int(r['outer_participant']) in done];costs=[r for r in costs if int(r['participant_id']) in done]
 for pid in range(1,44):
  if pid in done:continue
  outer=np.flatnonzero(subjects!=pid);test=np.flatnonzero(subjects==pid);xt=np.asarray(X[outer],np.float32);yt=np.asarray(y[outer]);st=subjects[outer];assert pid not in st
  fold_scores={'SHAP':[],'PERM_GROUP':[]};fold_meta=[];tfit=tshap=tperm=0.
  for fold,(tr,va) in enumerate(GroupKFold(n_splits=5).split(xt,yt,st)):
   held=sorted(set(st[va].tolist()));training=sorted(set(st[tr].tolist()));assert not(set(held)&set(training)) and pid not in held+training
   rngfit=np.random.default_rng(SEED+fold);fit=tr if len(tr)<=200000 else rngfit.choice(tr,200000,replace=False)
   mu=xt[tr].mean(axis=0);sd=xt[tr].std(axis=0)+1e-8
   model=xgb.XGBClassifier(device='cuda',**p3.XGB_PARAMS);t=time.perf_counter();model.fit((xt[fit]-mu)/sd,yt[fit]);fit_sec=time.perf_counter()-t;tfit+=fit_sec
   rngval=np.random.default_rng(SEED+100*pid+fold);quota=2000//len(held);idx=np.concatenate([rngval.choice(va[st[va]==p],min(quota,int((st[va]==p).sum())),replace=False) for p in held]);v=(xt[idx]-mu)/sd;yv=yt[idx];sv=st[idx]
   t=time.perf_counter();contrib=model.get_booster().predict(xgb.DMatrix(v),pred_contribs=True);raw=channel_importance_from_contribs(contrib,16,10);ns=raw/raw.sum();shap_sec=time.perf_counter()-t;tshap+=shap_sec
   t=time.perf_counter();baseline=person_macro(yv,model.predict(v),sv);drops=[]
   for ch in range(16):
    reps=[];cols=np.arange(ch*10,(ch+1)*10)
    for rep in range(3):
     vp=v.copy();rng=np.random.default_rng(SEED+10000*pid+1000*fold+100*ch+rep)
     for p in held:
      dest=np.flatnonzero(sv==p);src=rng.permutation(dest);vp[np.ix_(dest,cols)]=v[np.ix_(src,cols)]
     reps.append(baseline-person_macro(yv,model.predict(vp),sv))
    drops.append(float(np.mean(reps)))
   rp=np.array(drops);norm=np.abs(rp).sum();np_=rp/norm if norm else rp;perm_sec=time.perf_counter()-t;tperm+=perm_sec
   fold_scores['SHAP'].append(ns);fold_scores['PERM_GROUP'].append(np_)
   for ch in range(16):scores.append({'outer_participant':pid,'inner_fold':fold,'channel':ch+1,'shap_raw':raw[ch],'shap_norm':ns[ch],'permutation_raw':rp[ch],'permutation_norm':np_[ch],'n_validation_windows':len(idx),'n_validation_participants':len(held),'inner_held_subjects':';'.join(map(str,held)),'inner_train_subjects':';'.join(map(str,training))})
   fold_meta.append({'fold':fold,'held_subjects':held,'train_subjects':training,'train_index_sha256':ah(outer[fit]),'validation_indices':outer[idx].tolist(),'scaler_mu_sha256':ah(mu),'scaler_sd_sha256':ah(sd),'n_fit_windows':len(fit),'fit_seconds':fit_sec,'shap_seconds':shap_sec,'permutation_seconds':perm_sec,'objective':json.loads(model.get_booster().save_config())['learner']['objective']['name']})
   print(f'participant {pid}: inner fold {fold+1}/5 complete',flush=True)
  rankmap={m:(np.lexsort((np.arange(16),-np.median(np.array(vals),axis=0)))+1).tolist() for m,vals in fold_scores.items()}
  for m,r in rankmap.items():ranks.append({'outer_participant':pid,'method':m,'ranking':';'.join(map(str,r))})
  fit=p3.subsample(xt,yt,200000);finalx=xt[fit];finaly=yt[fit];xe=np.asarray(X[test],np.float32);ye=np.asarray(y[test])
  def final(job):
   method,k,ch=job;oldrow=old[(old.participant_id==pid)&(old.channels_k==k)].iloc[0]
   if set(map(int,oldrow.channels.split(';')))==set(ch):return {'participant_id':pid,'method':method,'channels_k':k,'channels':';'.join(map(str,ch)),**{m:float(oldrow[m]) for m in ('macro_f1','accuracy','balanced_accuracy','weighted_f1')},'n_train_windows':200000,'n_test_windows':len(ye),'evaluation_source':'original_P3_exact_subset','fit_seconds':0.}
   cols=p3.channel_columns(ch);a=finalx[:,cols];mu=a.mean(axis=0);sd=a.std(axis=0)+1e-8;model=xgb.XGBClassifier(device='cuda',**p3.XGB_PARAMS);t=time.perf_counter();model.fit((a-mu)/sd,finaly);yp=model.predict((xe[:,cols]-mu)/sd)
   return {'participant_id':pid,'method':method,'channels_k':k,'channels':';'.join(map(str,ch)),'macro_f1':f1_score(ye,yp,average='macro',labels=range(16),zero_division=0),'accuracy':accuracy_score(ye,yp),'balanced_accuracy':balanced_accuracy_score(ye,yp),'weighted_f1':f1_score(ye,yp,average='weighted',zero_division=0),'n_train_windows':200000,'n_test_windows':len(ye),'evaluation_source':'new_shared_budget_fit','fit_seconds':time.perf_counter()-t}
  with ThreadPoolExecutor(max_workers=4) as ex:new=list(ex.map(final,[(m,k,r[:k]) for m,r in rankmap.items() for k in (6,12)]))
  rows=[r for r in rows if int(r['participant_id'])!=pid]+new;costs.append({'participant_id':pid,'shared_training_seconds':tfit,'shap_selection_seconds':tshap,'permutation_selection_seconds':tperm,'inner_models':5,'max_train_windows_per_model':200000,'max_validation_windows_per_model':2000,'permutation_repeats':3})
  (OUT/f'p{pid:02d}_metadata.json').write_text(json.dumps(fold_meta,indent=2),encoding='utf-8')
  for data,path in ((scores,score_path),(ranks,rank_path),(costs,cost_path),(rows,result_path)):save_csv(pd.DataFrame(data),path)
  print(f'{pid}/43: matched-budget methods evaluated; shared training={tfit:.1f}s SHAP={tshap:.1f}s permutation={tperm:.1f}s',flush=True)
 print('PASS: all matched-budget folds complete',flush=True)
if __name__=='__main__':main()
