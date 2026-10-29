"""Participant-level statistical validation for the 2026-10-14 revision."""
import argparse,hashlib,importlib.util,json,sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon,spearmanr
from sklearn.metrics import f1_score,confusion_matrix
ROOT=Path(__file__).resolve().parent.parent;REV=ROOT/'manuscript_revision/20261014';OUT=REV/'experiments/statistics';sys.path.insert(0,str(ROOT))
from src.semg_sparse.statistics.non_inferiority import bootstrap_participant_metrics
SEED=20260728;B=10000

def holm(p):
 p=np.asarray(p,float);order=np.argsort(p);a=np.empty(len(p));a[order]=np.minimum(1,np.maximum.accumulate((len(p)-np.arange(len(p)))*p[order]));return a

def null_studentized_p(d,margin,n_resamples=B,seed=SEED):
 d=np.asarray(d,float)
 if d.ndim!=1 or len(d)<2 or not np.isfinite(d).all() or not np.isfinite(margin) or margin<=0:raise ValueError('finite paired participant differences and positive margin required')
 n=len(d);mean=d.mean();se=d.std(ddof=1)/np.sqrt(n)
 if se==0:return 1/(n_resamples+1) if mean>-margin else 1.
 residual=d-mean;idx=np.random.default_rng(seed).choice(n,size=(n_resamples,n),replace=True);v=residual[idx];bm=v.mean(axis=1);bs=v.std(axis=1,ddof=1)/np.sqrt(n)
 bt=np.divide(bm,bs,out=np.zeros_like(bm),where=bs>0);bt[(bs==0)&(bm>0)]=np.inf;bt[(bs==0)&(bm<0)]=-np.inf
 observed=(mean+margin)/se
 return float((1+np.sum(bt>=observed))/(n_resamples+1))

def paired(d,**labels):
 d=np.asarray(d,float);mean,lo,hi=bootstrap_participant_metrics(d,n_resamples=B,seed=SEED);p=1. if np.all(d==0) else float(wilcoxon(d).pvalue)
 return {**labels,'n':len(d),'mean_diff':mean,'lcb95':lo,'ucb95':hi,'p_raw':p,'n_positive':int((d>0).sum()),'n_negative':int((d<0).sum()),'n_tied':int((d==0).sum())}

def require_grid(df,columns,values,label):
 from src.semg_sparse.xai.validation import require_grid as validate
 validate(df,columns,values,label)

def ni_table(curve,ref,condition):
 ks=sorted(set(curve.channels_k.astype(int))-{ref});pivot=curve.pivot(index='participant_id',columns='channels_k',values='macro_f1').sort_index();rows=[]
 for margin in (.01,.02,.03):
  part=[]
  for k in ks:
   d=(pivot[k]-pivot[ref]).to_numpy();mean,lo,hi=bootstrap_participant_metrics(d,n_resamples=B,seed=SEED)
   bm=d[np.random.default_rng(SEED).choice(len(d),size=(B,len(d)),replace=True)].mean(axis=1)
   part.append({'condition':condition,'margin':margin,'k':k,'n':len(d),'mean_k':pivot[k].mean(),'mean_reference':pivot[ref].mean(),'mean_diff':mean,'lcb95':lo,'ucb95':hi,'historical_percentile_tail':max(float((bm<=-margin).mean()),1/B),'p_null_studentized':null_studentized_p(d,margin),'ni_percentile_ci':lo>-margin})
  part=pd.DataFrame(part);part['historical_tail_holm']=holm(part.historical_percentile_tail);part['p_null_holm']=holm(part.p_null_studentized);part['ni_historical_holm']=part.historical_tail_holm<.025;part['ni_null_holm']=part.p_null_holm<.025;rows.append(part)
 return pd.concat(rows,ignore_index=True)

def load_curves():
 curves={}
 p=pd.read_csv(ROOT/'artifacts/metrics/sparse_curve_subject_metrics.csv')
 for lam in (0.,.25,.5,1.):
  d=p[p['lambda']==lam].copy();require_grid(d,['participant_id','channels_k'],[range(1,44),range(1,17)],'primary curve');curves[f'primary_lambda{lam:g}']=d
 for name in ('rest17','w150','w500'):
  d=pd.read_csv(ROOT/f'artifacts/completion_analyses/{name}/sparse_curve_subject_metrics.csv');require_grid(d,['participant_id','channels_k'],[range(1,44),range(1,17)],name);curves[name]=d
 e=pd.read_csv(REV/'experiments/attribution_extension/sparse_curve.csv')
 for lam in (0.,.25,.5,1.):
  d=e[e['lambda']==lam].copy();require_grid(d,['participant_id','channels_k'],[range(1,44),range(1,17)],'participant aggregation curve');curves[f'participant_lambda{lam:g}']=d
 g=pd.read_csv(REV/'experiments/geometric_curve/sparse_curve_subject_metrics.csv');require_grid(g,['participant_id','channels_k'],[range(1,44),range(1,17)],'geometric primary curve');curves['geometric_primary']=g
 curves['db5']=pd.read_csv(ROOT/'artifacts/db5/db5_sparse_curve.csv')
 b=pd.read_csv(ROOT/'artifacts/bipolar/bipolar_sparse_curve.csv');curves['bipolar']=b[b['lambda']==0.]
 return curves

def primary_predictions():
 folder=REV/'experiments/primary_predictions';m=pd.read_csv(folder/'participant_metrics.csv');require_grid(m,['participant_id','condition'],[range(1,44),['full16','shap12','geom12']],'revision predictions')
 per=[];conf=[]
 for pid in range(1,44):
  preds={name:np.load(folder/f'p{pid:02d}_{name}.npz') for name in ('full16','shap12','geom12')}
  for name,z in preds.items():
   base=preds['full16'];assert np.array_equal(z['row_index'],base['row_index']) and np.array_equal(z['y_true'],base['y_true'])
   f=f1_score(z['y_true'],z['y_pred'],labels=range(16),average=None,zero_division=0)
   cm=confusion_matrix(z['y_true'],z['y_pred'],labels=range(16));rate=cm/cm.sum(axis=1,keepdims=True)
   for g in range(16):per.append({'participant_id':pid,'condition':name,'gesture_id':g+1,'f1':f[g]})
   for a in range(16):
    for b in range(16):conf.append({'participant_id':pid,'condition':name,'true_gesture':a+1,'predicted_gesture':b+1,'count':int(cm[a,b]),'conditional_rate':rate[a,b]})
 per=pd.DataFrame(per);per.to_csv(OUT/'per_gesture_participant.csv',index=False);conf=pd.DataFrame(conf);conf.to_csv(OUT/'confusion_participant.csv',index=False)
 wide=m.pivot(index='participant_id',columns='condition',values='macro_f1').sort_index();rows=[]
 for name in ('shap12','geom12'):
  d=wide[name]-wide.full16
  for margin in (.01,.02,.03):
   row=paired(d,condition=name,margin=margin);row.update(p_null_studentized=null_studentized_p(d,margin),ni_percentile_ci=row['lcb95']>-margin);rows.append(row)
 pd.DataFrame(rows).to_csv(OUT/'primary_matched_noninferiority.csv',index=False)
 contrast=paired(wide.shap12-wide.geom12,comparison='primary SHAP12 minus geometry12');pd.DataFrame([contrast]).to_csv(OUT/'primary_selection_comparison.csv',index=False)
 gstat=[]
 for g in range(1,17):
  w=per[per.gesture_id==g].pivot(index='participant_id',columns='condition',values='f1').sort_index();gstat.append(paired(w.shap12-w.full16,gesture_id=g,mean_full16=w.full16.mean(),mean_shap12=w.shap12.mean()))
 gstat=pd.DataFrame(gstat);gstat['p_holm']=holm(gstat.p_raw);gstat.to_csv(OUT/'gesture_degradation.csv',index=False)
 for name in ('full16','shap12','geom12'):
  assert np.allclose(per[per.condition==name].groupby('participant_id').f1.mean().sort_index(),wide[name],atol=1e-12)
 delta=wide.shap12-wide.full16;desc={'n':len(delta),'mean':float(delta.mean()),'median':float(delta.median()),'sd':float(delta.std(ddof=1)),'min':float(delta.min()),'max':float(delta.max()),'n_improved':int((delta>0).sum()),'n_loss_over_margin002':int((delta<-.02).sum()),'baseline_difference_spearman':float(spearmanr(wide.full16,delta).statistic),'interpretation':'descriptive; baseline is mathematically coupled to its difference; no individual non-inferiority guarantee','worst_participant_id':int(delta.idxmin()),**{f'q{int(q*100):02d}':float(delta.quantile(q)) for q in (.05,.1,.25,.75,.9,.95)}}
 wide['delta_shap12']=delta;wide['delta_geom12']=wide.geom12-wide.full16;wide.to_csv(OUT/'participant_degradation.csv');(OUT/'participant_degradation_summary.json').write_text(json.dumps(desc,indent=2),encoding='utf-8')
 c=conf.groupby(['condition','true_gesture','predicted_gesture']).conditional_rate.mean().unstack('condition');c['delta_shap12']=c.shap12-c.full16;c.to_csv(OUT/'confusion_change.csv')

def matched_and_extension():
 m=pd.read_csv(REV/'experiments/matched_budget/participant_metrics.csv');require_grid(m,['participant_id','method','channels_k'],[range(1,44),['SHAP','PERM_GROUP'],[6,12]],'matched budget');rows=[]
 for k in (6,12):
  w=m[m.channels_k==k].pivot(index='participant_id',columns='method',values='macro_f1').sort_index();rows.append(paired(w.SHAP-w.PERM_GROUP,k=k,mean_shap=w.SHAP.mean(),mean_permutation=w.PERM_GROUP.mean()))
 d=pd.DataFrame(rows);d['p_holm']=holm(d.p_raw);d.to_csv(OUT/'matched_budget_comparisons.csv',index=False)
 costs=pd.read_csv(REV/'experiments/matched_budget/costs.csv');costs[['shared_training_seconds','shap_selection_seconds','permutation_selection_seconds']].agg(['mean','std','min','max']).T.to_csv(OUT/'matched_budget_cost_summary.csv')
 ext=pd.read_csv(REV/'experiments/attribution_extension/sparse_curve.csv');require_grid(ext,['participant_id','lambda','channels_k'],[range(1,44),[0.,.25,.5,1.],range(1,17)],'extension');rows=[]
 for lam in (.25,.5,1.):
  for k in (4,6,8,12):
   a=ext[(ext['lambda']==lam)&(ext.channels_k==k)].set_index('participant_id').macro_f1.sort_index();b=ext[(ext['lambda']==0)&(ext.channels_k==k)].set_index('participant_id').macro_f1.sort_index();rows.append(paired(a-b,**{'lambda':lam},k=k))
 d=pd.DataFrame(rows);d['p_holm']=holm(d.p_raw);d['supports_benefit']=(d.mean_diff>0)&(d.p_holm<.05);d['supports_harm']=(d.mean_diff<0)&(d.p_holm<.05);d.to_csv(OUT/'extension_penalty.csv',index=False);d['supports_penalty_benefit']=d.supports_benefit;d['supports_penalty_harm']=d.supports_harm;d.to_csv(REV/'experiments/attribution_extension/penalty_gate.csv',index=False)

def alternative_classifier():
 m=pd.read_csv(REV/'experiments/alternative_classifier/participant_metrics.csv');require_grid(m,['participant_id','channels_k'],[range(1,44),[12,16]],'RF fixed counts')
 ni_table(m,16,'RF_fixed_counts').to_csv(OUT/'alternative_classifier_noninferiority.csv',index=False)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--primary-only',action='store_true');args=ap.parse_args();OUT.mkdir(parents=True,exist_ok=True)
 primary_predictions()
 if not args.primary_only:
  allni=[]
  for name,d in load_curves().items():
   ref=8 if name=='bipolar' else 16;allni.append(ni_table(d,ref,name))
  ni=pd.concat(allni,ignore_index=True);ni.to_csv(OUT/'noninferiority_audit.csv',index=False);ks=[]
  for (name,margin),g in ni.groupby(['condition','margin']):ks.append({'condition':name,'margin':margin,'n':int(g.n.iloc[0]),'kstar_percentile':g[g.ni_percentile_ci].k.min(),'kstar_historical_holm':g[g.ni_historical_holm].k.min(),'kstar_null_studentized_holm':g[g.ni_null_holm].k.min()})
  pd.DataFrame(ks).to_csv(OUT/'kstar_audit.csv',index=False);matched_and_extension();alternative_classifier()
 print('PASS: revision participant-level statistics generated',flush=True)
if __name__=='__main__':main()
