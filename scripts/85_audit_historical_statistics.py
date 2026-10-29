"""Recompute primary/historical secondary numerical reporting without changing original results."""
from pathlib import Path
import hashlib,importlib.util,json
import pandas as pd
ROOT=Path(__file__).resolve().parent.parent
REV=ROOT/'manuscript_revision/20261014';OUT=REV/'experiments/historical_statistics_recomputed';REPORT=REV/'reports/historical_statistics_reconstruction.json'

def module(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/'scripts'/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()

def main():
 REPORT.write_text(json.dumps({'status':'RUNNING'}),encoding='utf-8');OUT.mkdir(exist_ok=True)
 primary=module('primary_stats','28_statistics.py');primary.OUT=OUT
 if primary.main()!=0:raise RuntimeError('full primary statistical reconstruction failed')
 secondary=module('secondary_stats','37_secondary_statistics.py');secondary.OUT=OUT
 for fn in (secondary.h2_and_baselines,secondary.h3,secondary.h4,secondary.cross_session,secondary.db5_and_bipolar,secondary.h1_holm):fn()
 expected=['master_statistics.csv','model_comparisons.csv','non_inferiority_by_k.csv','h2_attribution_vs_random.csv','h2_srcfa_percentile_by_participant.csv','h2_srcfa_percentile.csv','baseline_pairwise_exploratory.csv','h3_lambda_vs_zero.csv','h4_faithfulness.csv','cross_session_tests.csv','db5_non_inferiority_by_k.csv','db5_bootstrap_seed_robustness.csv','bipolar_non_inferiority_by_k.csv','bipolar_bootstrap_seed_robustness.csv','h1_holm.csv']
 checked=[]
 for name in expected:
  historical=ROOT/'artifacts/statistics'/name;current=OUT/name
  a=pd.read_csv(historical);b=pd.read_csv(current)
  pd.testing.assert_frame_equal(a,b,check_dtype=False,check_exact=False,rtol=1e-10,atol=1e-12)
  checked.append({'file':name,'rows':len(b),'original_sha256':sha(historical),'recomputed_sha256':sha(current)})
  print('PASS: statistical table reconstructed: '+name,flush=True)
 a=json.loads((ROOT/'artifacts/statistics/analysis_provenance.json').read_text());b=json.loads((OUT/'analysis_provenance.json').read_text())
 if a!=b:raise ValueError('primary statistical protocol provenance differs')
 inputs=[ROOT/p for p in ['scripts/28_statistics.py','scripts/37_secondary_statistics.py','scripts/85_audit_historical_statistics.py','src/semg_sparse/statistics/non_inferiority.py','configs/statistics/frozen_analysis_plan.yaml','artifacts/metrics/loso_full_channel_subject_metrics_xgb.csv','artifacts/metrics/loso_full_channel_subject_metrics_svmrf.csv','artifacts/metrics/sparse_curve_subject_metrics.csv','artifacts/selection_baselines/selection_baseline_metrics.csv','artifacts/selection_baselines/random_subsets_raw.csv','artifacts/faithfulness/deletion_curves.csv','artifacts/cross_session/cross_session_metrics.csv','artifacts/db5/db5_sparse_curve.csv','artifacts/bipolar/bipolar_sparse_curve.csv']]
 REPORT.write_text(json.dumps({'status':'PASS','tables':checked,'primary_protocol_equal':True,'source_hashes':{str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in inputs},'interpretation':'Saved primary/secondary statistics independently regenerated from participant results and compared including labels and decision flags; original files unchanged; seed diagnostics keep original seeds1000-1199.'},indent=2),encoding='utf-8')
 print('PASS: all15 primary and historical secondary statistical tables reproduce',flush=True)
if __name__=='__main__':main()
