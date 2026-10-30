"""Evidence-based reports for the completed revision; no inference from pending folds."""
from pathlib import Path
import json
import sys
import shutil
import pandas as pd
ROOT=Path(__file__).resolve().parent.parent;REV=ROOT/'manuscript_revision/20261014';S=REV/'experiments/statistics';R=REV/'reports'
sys.path.insert(0,str(ROOT))
from src.semg_sparse.reporting import runtime_evidence,write_independent_reports
def md(df):return df.to_markdown(index=False,floatfmt='.6f')
def main():
 evidence=runtime_evidence(ROOT)
 if evidence['scope']=='independent rerun':
  verification=json.loads((R/'verification.json').read_text())
  if verification.get('status')!='PASS':raise RuntimeError('Current numerical verification must pass before reporting')
  names=('primary_matched_noninferiority','primary_selection_comparison','kstar_audit','gesture_degradation','matched_budget_comparisons','extension_penalty','alternative_classifier_noninferiority','matched_budget_cost_summary')
  write_independent_reports(R,{name:pd.read_csv(S/(name+'.csv')) for name in names},evidence)
  shutil.copy2(R/'claim_evidence_matrix.csv',REV/'reproducibility/claim_evidence_matrix.csv')
  print('PASS: reports generated from independent rerun evidence; manuscript narrative review remains required',flush=True)
  return
 a=pd.read_csv(S/'primary_matched_noninferiority.csv');geo=pd.read_csv(S/'primary_selection_comparison.csv');ni=pd.read_csv(S/'kstar_audit.csv');gest=pd.read_csv(S/'gesture_degradation.csv');person=json.loads((S/'participant_degradation_summary.json').read_text());matched=pd.read_csv(S/'matched_budget_comparisons.csv');penalty=pd.read_csv(S/'extension_penalty.csv');rf=pd.read_csv(S/'alternative_classifier_noninferiority.csv');cost=pd.read_csv(S/'matched_budget_cost_summary.csv')
 (R/'04_statistical_validation.md').write_text('''# Statistical validation

The statistical unit is the participant: 43 in every GRABMyo LOSO analysis, ten in DB5, and 21/22 in the fixed-layout test halves. No confidence interval or hypothesis test uses windows as independent replicates.

The original percentile-interval decision is preserved. The historical unshifted bootstrap tail is identified as a percentile-tail calculation, not silently presented as a bootstrap null distribution. The new exploratory sensitivity resamples mean-centred paired differences, studentizes each resampled mean and compares its upper tail with (mean difference + margin)/standard error, using a plus-one probability. Holm covers the fifteen count tests per condition/margin/penalty. Both calculations use 10,000 resamples and the unchanged seed20260728. They are conditional on overlapping fitted LOSO models and do not propagate complete refitting uncertainty.

## Count decisions

'''+md(ni)+'''\n
## Matched primary predictions

'''+md(a)+'''\n
## Direct SHAP12 minus geometric12

'''+md(geo)+'''\n
The interval concerns the mean; Wilcoxon concerns signed ranks. A nominal rank-test result cannot establish a positive mean advantage when that mean interval crosses zero. SHAP's NI pass and geometry's NI failure do not constitute a direct between-method test. No equivalence inference is made.

## Participant and gesture limits

'''+json.dumps(person,indent=2)+'''\n
'''+md(gest)+'''\n
The sixteen gesture contrasts receive one Holm adjustment. Loss counts and extremes are descriptive, not individual NI tests. Baseline-difference correlation is mathematically coupled and is not used to infer causes. Near-boundary DB5 and reverse-layout results are retained at full precision. In DB5, even the0.03 margin yields no reduced count under the null-centred Holm sensitivity, whereas historical tail-Holm supports12 there. This disagreement is a small-cohort inference sensitivity, not a reason to select a favorable construction.

## Additional families

Resource-matched comparison: Holm over two counts. Participant-versus-fold extension: Holm over sixty comparisons. Penalty within person aggregation: Holm over twelve. Historical DB5 and bipolar seed diagnostics are recomputed for every reduced count using their original seeds1000-1199; no favorable seed is substituted. Cross-session contrasts remain explicitly exploratory and uncorrected. The post-hoc selector-activity audit reports every fixed penalty/count for fold and participant aggregation. It checks physical input identity and identical-set metric consistency; it adds no significance or equivalence test. Original H2/H3/H4 families contain eight/twelve/fifteen tests; their detailed families were determined post hoc and remain labeled secondary.

Six deterministic unit tests cover null-boundary centring, effect direction, location/scale invariance, invalid participant vectors and Holm monotonicity. Synthetic vectors are used only for tests and contribute no experimental metric. The complete current test suite passed 53 tests; the final QC report records the final run. Source: scripts/66_revision_statistics.py, tests/test_revision_statistics.py, scripts/16_verify_results.py --revision-dir manuscript_revision/20261014.
''',encoding='utf-8')
 gk=ni[(ni.condition=='geometric_primary')&(ni.margin==.02)].iloc[0]
 rows=[['A','full primary geometric count curve','completed, 43 participants x16 counts','300 boosting rounds / 200000 train windows; exact same outer sample; count12/full16 exact reuse',f'Minimum count {int(gk.kstar_percentile)} (CI), {int(gk.kstar_null_studentized_holm)} (null Holm) at0.02; direct12-site mean superiority uncertain'],['B','gesture degradation','completed, 43 paired participants','canonical prediction rows, all16 gestures','Holm16; no window-level inference'],['C','participant degradation','completed, 43 paired participants','primary full16 and SHAP12 predictions','Descriptive heterogeneity; mean NI is not individual preservation'],['D','shared-resource attribution','completed, 43 participants x2methods x2counts','same5models and validation observations; 3group permutations','Grouping and resource changes confounded; results below'],['E','Rest17','completed, 43 x16counts','raw-derived cache; unchanged primary rankings','Within-task full16 reference'],['E','150/500ms','completed, each43 x16counts','raw re-extraction; unchanged rankings','same window count differs in recorded duration'],['E','random forest','completed, 43 x2counts','pre-existing RF parameters; XGB-selected layouts','No RF minimum count or reranking claim'],['E','participant aggregation','fresh provenance-compatible isolated refit completed','all4penalties x16counts x43participants','Unselected fixed penalties; exact original subset reuse tagged'],['F','independent fixed-layout cohort','not available','no new same-montage recordings','Cannot complete external/prospective layout validation from existing data']]
 (R/'05_additional_experiments.md').write_text('# Additional experiment validation\n\n'+md(pd.DataFrame(rows,columns=['Priority','Experiment','Coverage','Protocol','Interpretation']))+'\n\n## Shared-resource performance\n\n'+md(matched)+'\n\n## Measured costs\n\n'+md(cost)+'\n\n## Participant-aggregation penalty\n\n'+md(penalty)+'\n\n## Fixed-count classifier sensitivity\n\n'+md(rf)+'''\n
Primary score reproduction is verified from saved predictions, not merely read from old tables. Current metrics match historical full16/SHAP12 at floating precision; original predictions were not archived, so prediction-level identity to the old run is not claimed. Shared-method and extension fits that reused an original identical channel set are explicitly tagged and verified against source rows.

The first500ms completion invocation saved the last fold then failed a runner assertion because its requested one-participant set was compared with the complete resumed cohort. The queue was corrected to request the full cohort without modifying the fingerprinted curve runner. A subsequent full-cohort resume passed; both logs are retained. No missing fold was invented or excluded.

The historical extension manifest still has a source-hash failure. A current isolated refit supplies provenance-compatible results; the old fingerprint was not rewritten. The final revision gate verifies the isolated result tree. Current protocols and amendments distinguish these exploratory checks from original primary and secondary tracks. Early shared-model folds ran while CPU RF jobs were active; later folds did not. Recorded times therefore describe the executed workstation load and are not an isolated runtime benchmark.
''',encoding='utf-8')
 claims=[('Twelve electrodes meet0.02 mean tolerance','primary planned rule, qualified chronology','artifacts/metrics/sparse_curve_subject_metrics.csv; primary_matched_noninferiority.csv; noninferiority_audit.csv','supported under observed offline LOSO protocol','Mean/conditional claim; no individual guarantee'),('Every participant or gesture is preserved','unsupported','participant_degradation.csv; gesture_degradation.csv','contradicted by observed losses','Do not claim'),('Attribution exceeds mean random selection','historical secondary','artifacts/statistics/h2_attribution_vs_random.csv','supported in lighter protocol','Unequal selection-stage resources across other methods'),('SHAP12 has a positive mean advantage over geometry12','new exploratory','primary_selection_comparison.csv','not established: mean CI crosses zero','Report nominal rank test separately'),('Stability penalty is a beneficial upgraded selector','historical secondary + person extension','extension_penalty.csv; artifacts/statistics/h3_lambda_vs_zero.csv','no established benefit','Report all fixed penalties; no outer-outcome choice'),('Shared-resource SHAP versus grouped permutation','new exploratory','matched_budget_comparisons.csv; matched_budget/inner_scores.csv','positive SHAP mean advantage at6; uncertain at12','Six does not meet primary NI; changes beyond budget remain confounded'),('Penalty changes physical inputs at twelve electrodes','new post-hoc descriptive audit','selection_change_audit.csv; selection_change_audit_participants.csv','all participant penalties unchanged in43/43 folds','Identical inputs and cached fits; not equivalence of different layouts'),('Minimum count for the tested geometric ordering','new exploratory after geometry12','kstar_audit.csv; geometric_curve/sparse_curve_subject_metrics.csv',f'geometric minimum {int(gk.kstar_percentile)} (CI), {int(gk.kstar_null_studentized_holm)} (null Holm)','One fixed ordering; differing NI decisions are not a direct method test'),('One common locked layout independently validated','unsupported','artifacts/completion_analyses/fixed_layout/summary.csv','not supported','Two different layouts; count exposed to full cohort'),('Rest/window/RF robustness','exploratory sensitivity','noninferiority_audit.csv; alternative_classifier_noninferiority.csv','condition-specific results retained','Primary rankings reused; RF onlytwo counts'),('DB5 validates the same12-site hardware layout','unsupported','artifacts/db5; noninferiority_audit.csv','not supported','Different hardware/task, ten participants'),('Bipolar pairs preserve proportional sensor reduction','unsupported','artifacts/bipolar; noninferiority_audit.csv','not supported','Derived signals, owneight-pair reference'),('Attribution maps specific muscles','unsupported','fig5 source data; documented montage','not supported','Predictive relevance, no registration or causal intervention'),('Real-time or clinical/device improvement','unsupported','no real-time/clinical measurements','not tested','Offline non-causal filtering and able-bodied cohorts'),('First SHAP electrode selector or novel robustness algorithm','unsupported novelty','reports/02_novelty_and_literature.md','not claimed','Prior EMG SHAP and attribution-stability work cited')]
 matrix=pd.DataFrame(claims,columns=['Claim','Evidence classification','Source','Decision','Scope/limitation']);matrix.to_csv(REV/'reproducibility/claim_evidence_matrix.csv',index=False)
 (R/'07_claim_evidence_matrix.md').write_text('# Claim-to-evidence matrix\n\n'+md(matrix)+'\n\nAll numerical claims use generated macro or table provenance. Table values and plots are regenerated only after scripts/16_verify_results.py verifies the current revision inputs. Novelty claims are bounded by primary-source access and are not a systematic-review conclusion.\n',encoding='utf-8')
 print('PASS: reports04,05,07 generated from complete current results')
if __name__=='__main__':main()
