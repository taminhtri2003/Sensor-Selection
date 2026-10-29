"""Adversarial tests of publication-gate and subject-aggregation invariants."""
import numpy as np
import pandas as pd
import pytest

from src.semg_sparse.xai.cross_fitted import CrossFittedAttribution, compute_cross_fitted_attribution
from src.semg_sparse.xai.validation import (require_grid, finite_values,
    validate_sparse_subsets, validate_attribution_tables)


def test_subject_heterogeneity_survives_fold_pooling():
    pooled = np.array([[.5, .5], [.5, .5]])
    att = CrossFittedAttribution(pooled, pooled, [[1, 2], [3, 4]], [2, 2],
        per_subject_norm={1: np.array([.9,.1]), 2: np.array([.1,.9]),
                          3: np.array([.9,.1]), 4: np.array([.1,.9])})
    assert np.allclose(att.instability(), 0)
    assert np.allclose(att.instability("subject"), .4)
    att.per_subject_norm.pop(4)
    with pytest.raises(ValueError, match="every"):
        att.ranking(unit="subject")


def test_outer_subject_guard_precedes_fit():
    with pytest.raises(ValueError, match="outer held-out"):
        compute_cross_fitted_attribution(np.ones((4, 2)), np.array([0,1,0,1]),
            np.array([1,1,2,2]), ['ch1_A', 'ch2_A'], n_channels=2,
            n_features_per_channel=1, excluded_subjects=(2,))


def test_grid_rejects_duplicate_replacing_missing_cell():
    frame = pd.DataFrame({'pid': [1,1,2,2], 'k': [1,2,1,1]})
    with pytest.raises(ValueError, match="duplicate"):
        require_grid(frame, ['pid','k'], [[1,2],[1,2]], 'example')


def test_metric_nan_is_not_a_complete_result():
    with pytest.raises(ValueError, match="nonfinite"):
        finite_values(pd.DataFrame({'macro_f1': [.5,np.nan]}), ['macro_f1'], 'example', True)


def test_sparse_subset_must_follow_its_own_outer_ranking():
    ranks = pd.DataFrame({'outer_participant':[1], 'lambda':[0.], 'ranking':['2;1']})
    curve = pd.DataFrame({'participant_id':[1,1], 'lambda':[0.,0.], 'channels_k':[1,2],
                         'channels':['1','2;1'], 'macro_f1':[.5,.6], 'accuracy':[.5,.6],
                         'balanced_accuracy':[.5,.6], 'weighted_f1':[.5,.6]})
    with pytest.raises(ValueError, match="subset"):
        validate_sparse_subsets(curve, ranks, [1], n_channels=2, lambdas=(0.,))


def attribution_fixture():
    # Small artificial unit-test fixture only; never written as study results.
    long, people, scores, ranks = [], [], [], []
    for outer in (1,2,3):
        for fold,held in enumerate(sorted({1,2,3}-{outer})):
            for ch,value in ((1,.6),(2,.4)):
                long.append(dict(outer_participant=outer,inner_fold=fold,channel=ch,
                    importance_raw=value,importance_norm=value,inner_held_subjects=str(held)))
                people.append(dict(outer_participant=outer,attributed_subject=held,
                                   channel=ch,importance_norm=value))
        for ch,value in ((1,.6),(2,.4)):
            scores.append({'outer_participant':outer,'channel':ch,'A_central':value,
                           'U_instability':0.,'Q_lam0.0':value})
        ranks.append({'outer_participant':outer,'lambda':0.,'ranking':'1;2'})
    return [pd.DataFrame(rows) for rows in (long,people,scores,ranks)]


def test_reconstructed_attribution_gate_accepts_coherent_tables():
    validate_attribution_tables(*attribution_fixture(),[1,2,3],n_channels=2,n_folds=2,lambdas=(0.,))


@pytest.mark.parametrize('corruption', ['outer_leak','person_missing','score_changed','ranking_changed'])
def test_reconstructed_attribution_gate_rejects_corruption(corruption):
    long,people,scores,ranks=attribution_fixture()
    if corruption=='outer_leak':
        long.loc[(long.outer_participant==1)&(long.inner_fold==0),'inner_held_subjects']='1'
    elif corruption=='person_missing':
        people=people.iloc[1:]
    elif corruption=='score_changed':
        scores.loc[0,'A_central']=.9
    else:
        ranks.loc[0,'ranking']='2;1'
    with pytest.raises(ValueError):
        validate_attribution_tables(long,people,scores,ranks,[1,2,3],n_channels=2,n_folds=2,lambdas=(0.,))
