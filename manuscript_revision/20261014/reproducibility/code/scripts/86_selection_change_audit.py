"""Descriptive fixed-penalty site-set activity audit, explicitly post hoc (amendment08)."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(ROOT))
from src.semg_sparse.xai.validation import require_grid
REV=ROOT/'manuscript_revision/20261014';OUT=REV/'experiments/statistics'

def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()

def sites(value):return frozenset(map(int,value.split(';')))

def main():
 inputs={'fold':ROOT/'artifacts/metrics/sparse_curve_subject_metrics.csv','participant':REV/'experiments/attribution_extension/sparse_curve.csv'};summary=[];individual=[]
 for aggregation,path in inputs.items():
  d=pd.read_csv(path);require_grid(d,['participant_id','lambda','channels_k'],[range(1,44),[0.,.25,.5,1.],range(1,17)],aggregation+' selector activity')
  base=d[d['lambda']==0.].set_index(['participant_id','channels_k'])
  for penalty in (.25,.5,1.):
   for k in range(1,17):
    a=d[(d['lambda']==penalty)&(d.channels_k==k)].set_index('participant_id').sort_index();b=base.xs(k,level='channels_k').sort_index();changed=[];jaccard=[];metric_change=[]
    for pid in range(1,44):
     selected=sites(a.loc[pid,'channels']);reference=sites(b.loc[pid,'channels']);different=selected!=reference;j=len(selected&reference)/len(selected|reference);delta=float(a.loc[pid,'macro_f1']-b.loc[pid,'macro_f1'])
     if not different and not np.allclose(a.loc[pid,['macro_f1','accuracy','balanced_accuracy','weighted_f1']].astype(float),b.loc[pid,['macro_f1','accuracy','balanced_accuracy','weighted_f1']].astype(float),rtol=0,atol=1e-12):raise ValueError('identical site set has inconsistent fixed-protocol metrics')
     changed.append(different);jaccard.append(j);metric_change.append(abs(delta)>1e-12);individual.append({'aggregation':aggregation,'lambda':penalty,'k':k,'participant_id':pid,'subset_changed':different,'jaccard':j,'macro_f1_delta':delta})
    summary.append({'aggregation':aggregation,'lambda':penalty,'k':k,'n':43,'n_changed_subset':int(sum(changed)),'n_unchanged_subset':43-int(sum(changed)),'mean_jaccard':float(np.mean(jaccard)),'n_changed_macro_f1':int(sum(metric_change))})
 table=pd.DataFrame(summary);table.to_csv(OUT/'selection_change_audit.csv',index=False);pd.DataFrame(individual).to_csv(OUT/'selection_change_audit_participants.csv',index=False)
 sources=[Path(__file__),REV/'reproducibility/protocol_amendment_08.json',*inputs.values()]
 (REV/'reports/selection_change_audit.json').write_text(json.dumps({'status':'PASS','summary_rows':len(summary),'participant_rows':len(individual),'source_hashes':{str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in sources},'classification':'post-hoc descriptive diagnostic; no new model or tuning'},indent=2),encoding='utf-8')
 print(table[table.k==12].to_string(index=False));print('PASS: all fixed-penalty/count site-set changes recorded',flush=True)
if __name__=='__main__':main()
