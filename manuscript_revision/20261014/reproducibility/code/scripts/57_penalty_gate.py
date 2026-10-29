"""Post-hoc diagnostic of the upgraded penalty; no outer-outcome selection."""
import importlib.util
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parent.parent


def main():
    spec=importlib.util.spec_from_file_location('secondary',ROOT/'scripts/37_secondary_statistics.py')
    stats=importlib.util.module_from_spec(spec);spec.loader.exec_module(stats)
    folder=ROOT/'artifacts/participant_attribution'
    curve=pd.read_csv(folder/'sparse_curve.csv')
    if len(curve)!=43*4*16 or curve.duplicated(['participant_id','lambda','channels_k']).any():
        raise ValueError('penalty diagnostic requires the full extension cohort')
    rows=[]
    for lam in (.25,.5,1.):
        for k in (4,6,8,12):
            rows.append(stats.paired(stats.series(curve,**{'lambda':lam},channels_k=k),
                stats.series(curve,**{'lambda':0.},channels_k=k),
                **{'lambda':lam},k=k,comparison='participant penalty minus participant magnitude'))
    result=stats.finish(rows,'participant_penalty_posthoc',True)
    result['supports_penalty_benefit']=(result.mean_diff>0)&(result.p_holm<.05)
    result['supports_penalty_harm']=(result.mean_diff<0)&(result.p_holm<.05)
    result.to_csv(folder/'penalty_gate.csv',index=False)
    print('Post-hoc penalty diagnostic complete; all comparisons reported.')


if __name__=='__main__':
    main()
