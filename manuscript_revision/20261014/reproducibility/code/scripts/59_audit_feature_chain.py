"""Reproducible spot checks linking raw recordings, feature cache and predictions.

These are selected technical checks, not an exhaustive re-extraction or a
statistical experiment. --refit-participant performs an optional cold refit.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parent.parent


def module(name, filename):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/filename)
    obj=importlib.util.module_from_spec(spec);spec.loader.exec_module(obj)
    return obj


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--refit-participant',type=int)
    args=ap.parse_args()
    extract=module('extract','20_extract_features_full.py')
    df=pd.read_parquet(ROOT/'data/features/grabmyo_features_full.parquet')
    rows=[]
    for pid,session,gesture in ((1,1,1),(22,2,9),(43,3,16)):
        qc,result=extract.process_record((session,pid,gesture,1))
        if result is None:
            raise ValueError(qc)
        _,features=result
        saved=df[(df.participant_id==pid)&(df.session_id==session)&(df.gesture_id==gesture)
                 &(df.trial_id==1)].sort_values('window_idx')[extract.FEAT_NAMES].to_numpy()
        passed=bool(np.array_equal(saved,features))
        rows.append({'participant':pid,'session':session,'gesture':gesture,'trial':1,
                     'n_windows':len(features),'max_absolute_difference':float(abs(saved-features).max()),'passed':passed})
        if not passed:
            raise ValueError('raw feature spot check differs from saved features')
    pd.DataFrame(rows).to_csv(ROOT/'reports/raw_feature_spotcheck_20260922.csv',index=False)
    bipolar=module('bipolar_extract','35_extract_bipolar_features.py')
    bipolar_saved=pd.read_parquet(ROOT/'data/features/grabmyo_bipolar_features.parquet')
    rows=[]
    for pid,session,gesture in ((1,1,1),(22,2,9),(43,3,16)):
        qc,result=bipolar.process_record((session,pid,gesture,1))
        if result is None:
            raise ValueError(qc)
        _,features=result
        b=bipolar_saved
        saved=b[(b.participant_id==pid)&(b.session_id==session)&(b.gesture_id==gesture)
                &(b.trial_id==1)].sort_values('window_idx')[bipolar.FEAT_NAMES].to_numpy()
        passed=bool(np.array_equal(saved,features))
        rows.append({'participant':pid,'session':session,'gesture':gesture,'trial':1,
                     'threshold':bipolar.BIPOLAR_THRESH,'n_windows':len(features),
                     'max_absolute_difference':float(abs(saved-features).max()),'passed':passed})
        if not passed:
            raise ValueError('bipolar feature file does not match corrected extraction protocol')
    pd.DataFrame(rows).to_csv(ROOT/'reports/bipolar_feature_spotcheck_20260922.csv',index=False)
    active=df[df.gesture_id<=16]
    for name,values in (('X',active[extract.FEAT_NAMES].to_numpy(np.float32)),
                       ('y',active.gesture_id.to_numpy()-1),
                       ('subj',active.participant_id.to_numpy()),('sess',active.session_id.to_numpy())):
        saved=np.load(ROOT/f'data/cache/loso_{name}.npy',mmap_mode='r')
        if not np.array_equal(saved,values):
            raise ValueError(f'LOSO {name} cache differs from extracted features')
    pred=pd.read_parquet(ROOT/'artifacts/predictions/loso_full_channel_predictions_xgb.parquet')
    for pid in range(1,44):
        p=pred[pred.participant_id==pid]
        a=active[active.participant_id==pid]
        if not (np.array_equal(p.y_true,a.gesture_id.to_numpy()-1)
                and np.array_equal(p.session_id,a.session_id)):
            raise ValueError(f'prediction labels/order differ within participant {pid}')
    print('PASS: spot-checked raw features, complete LOSO cache and prediction-label alignment',flush=True)
    if args.refit_participant is not None:
        if args.refit_participant not in range(1,44):
            raise ValueError('invalid participant')
        baseline=module('baseline','24_full_channel_loso_parallel.py')
        paths=tuple(str(ROOT/f'data/cache/loso_{n}.npy') for n in ('X','y','subj','sess'))
        fresh=baseline.run_fold((args.refit_participant,paths,['XGB'],'cuda',2))[0]
        old=pred[pred.participant_id==args.refit_participant]
        metrics=pd.read_csv(ROOT/'artifacts/metrics/loso_full_channel_subject_metrics_xgb.csv')
        saved=float(metrics[metrics.participant_id==args.refit_participant].macro_f1.iloc[0])
        report={'participant':args.refit_participant,'fresh_macro_f1':fresh['macro_f1'],
                'saved_macro_f1':saved,'difference':fresh['macro_f1']-saved,
                'prediction_agreement':float(np.mean(fresh['_pred']==old.y_pred.to_numpy())),
                'note':'A technical spot check, not a replacement of original results or a new hypothesis test.'}
        (ROOT/'reports/cold_refit_spotcheck_20260922.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(json.dumps(report),flush=True)


if __name__=='__main__':
    main()
