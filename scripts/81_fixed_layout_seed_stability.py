"""Fixed-layout near-boundary seed diagnostic; preserves the original decision."""
from pathlib import Path
import json,hashlib,sys
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parent.parent;REV=ROOT/'manuscript_revision/20261014';OUT=REV/'experiments/fixed_layout_seed_diagnostic';sys.path.insert(0,str(ROOT))
from src.semg_sparse.statistics.non_inferiority import bootstrap_participant_metrics

def main():
 OUT.mkdir(parents=True,exist_ok=True);source=ROOT/'artifacts/completion_analyses/fixed_layout/per_participant.csv';df=pd.read_csv(source);df=df[df['lambda']==0];seeds=np.random.default_rng(20260728).integers(0,2**31-1,size=200);rows=[];summaries=[]
 for split,g in df.groupby('split'):
  d=g.sort_values('test_participant').diff_12_minus_16.to_numpy();expected=21 if split=='dev_odd_test_even' else 22
  if len(d)!=expected or g.test_participant.nunique()!=expected:raise ValueError('fixed split participant coverage wrong')
  for seed in seeds:
   mean,lo,hi=bootstrap_participant_metrics(d,n_resamples=10000,seed=int(seed));rows.append({'split':split,'n':len(d),'seed':int(seed),'mean_diff':mean,'lcb95':lo,'ucb95':hi,'noninferior002':lo>-.02})
  r=pd.DataFrame([x for x in rows if x['split']==split]);summaries.append({'split':split,'n':len(d),'n_seeds':len(r),'n_pass':int(r.noninferior002.sum()),'fraction_pass':r.noninferior002.mean(),'min_lcb95':r.lcb95.min(),'max_lcb95':r.lcb95.max(),'median_lcb95':r.lcb95.median()})
 pd.DataFrame(rows).to_csv(OUT/'all_seeds.csv',index=False);pd.DataFrame(summaries).to_csv(OUT/'summary.csv',index=False);(OUT/'input_manifest.json').write_text(json.dumps({'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'runner_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'protocol_sha256':hashlib.sha256((REV/'reproducibility/protocol_amendment_07.json').read_bytes()).hexdigest(),'interpretation':'numerical decision stability only; original bootstrap seed retained'},indent=2),encoding='utf-8');print(pd.DataFrame(summaries).to_string(index=False));print('PASS: all fixed-layout seed outcomes reported',flush=True)
if __name__=='__main__':main()

