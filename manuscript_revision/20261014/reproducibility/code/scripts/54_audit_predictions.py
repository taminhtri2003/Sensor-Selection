"""Recompute baseline metrics and participant-level gesture failure summaries."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, accuracy_score, balanced_accuracy_score

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
from src.semg_sparse.statistics.non_inferiority import bootstrap_participant_metrics


def main():
    out = ROOT / 'artifacts/prediction_audit'
    out.mkdir(parents=True, exist_ok=True)
    rows, per_class = [], []
    for tag in ('xgb','svmrf'):
        predictions = pd.read_parquet(ROOT / f'artifacts/predictions/loso_full_channel_predictions_{tag}.parquet')
        metrics = pd.read_csv(ROOT / f'artifacts/metrics/loso_full_channel_subject_metrics_{tag}.csv')
        for (pid,model), g in predictions.groupby(['participant_id','model']):
            saved = metrics[(metrics.participant_id == pid) & (metrics.model == model)]
            if len(saved) != 1 or set(g.y_true) != set(range(16)):
                raise ValueError('prediction identity or gesture coverage mismatch')
            calculated = {'macro_f1': f1_score(g.y_true,g.y_pred,average='macro'),
                'weighted_f1':f1_score(g.y_true,g.y_pred,average='weighted'),
                'accuracy':accuracy_score(g.y_true,g.y_pred),
                'balanced_accuracy':balanced_accuracy_score(g.y_true,g.y_pred)}
            for metric,value in calculated.items():
                if not np.isclose(value,saved.iloc[0][metric],atol=1e-10,rtol=0):
                    raise ValueError(f'prediction metric mismatch: {pid}, {model}, {metric}')
            rows.append({'participant_id':pid,'model':model,**calculated,'n_windows':len(g)})
            for gesture,value in enumerate(f1_score(g.y_true,g.y_pred,labels=range(16),average=None)):
                per_class.append({'participant_id':pid,'model':model,'gesture_id':gesture+1,'f1':value})
    audited = pd.DataFrame(rows)
    if not (audited.groupby('model').participant_id.nunique() == 43).all():
        raise ValueError('incomplete prediction cohort')
    audited.to_csv(out / 'recomputed_metrics.csv',index=False)
    classes = pd.DataFrame(per_class)
    classes.to_csv(out / 'participant_gesture_f1.csv',index=False)
    summary = []
    for (model,gesture),g in classes.groupby(['model','gesture_id']):
        mean,lo,hi=bootstrap_participant_metrics(g.f1.to_numpy())
        summary.append({'model':model,'gesture_id':gesture,'n_participants':len(g),
                        'mean_f1':mean,'lcb95':lo,'ucb95':hi})
    pd.DataFrame(summary).to_csv(out / 'gesture_summary.csv',index=False)
    print(f'PASS: {len(audited)} baseline model-participant metrics reconstructed from predictions')


if __name__ == '__main__':
    main()
