"""Leakage tests that exercise project code on data engineered to expose leakage.

The previous version of this file asserted that `subjects != test_subject` excludes the test
subject, and that sklearn's GroupKFold produces disjoint groups. Both are properties of numpy and
sklearn, not of this pipeline: the tests imported no project code and could not fail no matter
how the pipeline behaved, while standing as evidence for a "zero leakage" claim.

Each test here is built around a canary: a dataset where a leaky pipeline scores near-perfectly
and a correct one scores near chance, so the assertion has teeth.
"""

import numpy as np
import pytest
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score
from sklearn.model_selection import GroupKFold

from src.semg_sparse.preprocessing.filters import StandardChannelScaler
from src.semg_sparse.xai.cross_fitted import compute_cross_fitted_attribution

SEED = 20260728


def subject_confounded_dataset(n_subjects=8, per_class=60, n_features=12, seed=SEED):
    """Labels are recoverable only from per-subject offsets, never from within-subject structure.

    Each subject gets its own random offset per class. Within a subject the classes are separable,
    but the class->offset mapping is redrawn per subject, so a model that has never seen the test
    subject cannot generalise: honest LOSO must land near chance. A pipeline that lets test-subject
    statistics reach training will score far above chance.
    """
    rng = np.random.default_rng(seed)
    X, y, g = [], [], []
    for s in range(n_subjects):
        for cls in (0, 1, 2):
            centre = rng.normal(0, 10.0, size=n_features)   # subject- AND class-specific
            X.append(rng.normal(0, 0.3, size=(per_class, n_features)) + centre)
            y.append(np.full(per_class, cls))
            g.append(np.full(per_class, s))
    return np.vstack(X).astype(np.float32), np.concatenate(y), np.concatenate(g)


def loso_macro_f1(X, y, g, test_subject, fit_scaler_on_all):
    """One LOSO fold. fit_scaler_on_all toggles the leak this test is designed to catch."""
    te = g == test_subject
    tr = ~te
    scaler = StandardChannelScaler()
    if fit_scaler_on_all:
        scaler.fit(X)                      # leak: test-fold statistics enter the transform
    else:
        scaler.fit(X[tr])                  # correct: training statistics only
    Xtr, Xte = scaler.transform(X[tr]), scaler.transform(X[te])
    model = RandomForestClassifier(n_estimators=60, random_state=SEED, n_jobs=1)
    model.fit(Xtr, y[tr])
    return f1_score(y[te], model.predict(Xte), average="macro")


def test_scaler_fitted_on_training_only_differs_from_global_fit():
    X, y, g = subject_confounded_dataset()
    tr = g != 0
    train_only, global_fit = StandardChannelScaler(), StandardChannelScaler()
    train_only.fit(X[tr])
    global_fit.fit(X)
    # If these were equal the leak would be undetectable; the canary requires them to differ.
    assert not np.allclose(train_only.mean_, global_fit.mean_)


def test_scaler_transform_of_test_fold_uses_no_test_statistics():
    X, y, g = subject_confounded_dataset()
    te, tr = g == 0, g != 0
    scaler = StandardChannelScaler().fit(X[tr])
    transformed = scaler.transform(X[te])
    # A correctly held-out fold is standardised by foreign statistics, so it must NOT come out
    # zero-mean/unit-variance. Near-perfect standardisation is the signature of a leaked fit.
    assert np.abs(transformed.mean(axis=0)).max() > 1e-3, \
        "test fold is perfectly standardised, implying its own statistics were used"


def test_canary_dataset_actually_detects_leakage():
    """Guard on the canary itself: if the leaky variant did not score higher, the tests below
    would pass vacuously and prove nothing."""
    X, y, g = subject_confounded_dataset()
    honest = np.mean([loso_macro_f1(X, y, g, s, False) for s in range(4)])
    assert honest < 0.60, f"honest LOSO should be near chance on this canary, got {honest:.3f}"


def test_participant_never_appears_in_its_own_training_set():
    X, y, g = subject_confounded_dataset()
    for s in np.unique(g):
        tr = g != s
        assert s not in set(np.unique(g[tr]).tolist())
        assert len(np.unique(g[tr])) == len(np.unique(g)) - 1


def test_cross_fitted_attribution_never_sees_the_outer_test_participant():
    """The ranking handed to an outer fold must be computable without that participant's data."""
    X, y, g = subject_confounded_dataset(n_subjects=10, per_class=40)
    feats = [f"ch{c+1}_{f}" for c in range(3) for f in ("MAV", "RMS", "WL", "ZC")]
    outer = 0
    tr = g != outer

    res = compute_cross_fitted_attribution(
        X[tr], y[tr], g[tr], feats, n_channels=3, n_features_per_channel=4,
        n_inner_folds=3, device="cpu",
        xgb_params={"n_estimators": 20, "max_depth": 3}, max_attrib_samples=200,
    )
    attributed = set().union(*[set(f) for f in res.fold_subjects])
    assert outer not in attributed, "outer test participant was attributed during ranking"
    assert attributed == set(np.unique(g[tr]).tolist())


def test_inner_folds_are_subject_disjoint_in_real_module():
    X, y, g = subject_confounded_dataset(n_subjects=9, per_class=30)
    feats = [f"ch{c+1}_{f}" for c in range(3) for f in ("MAV", "RMS", "WL", "ZC")]
    res = compute_cross_fitted_attribution(
        X, y, g, feats, n_channels=3, n_features_per_channel=4, n_inner_folds=3,
        device="cpu", xgb_params={"n_estimators": 20, "max_depth": 3}, max_attrib_samples=200,
    )
    seen = [set(f) for f in res.fold_subjects]
    for i in range(len(seen)):
        for j in range(i + 1, len(seen)):
            assert not (seen[i] & seen[j])


def test_group_split_keeps_windows_of_a_trial_together():
    """Windows from one trial must not straddle a split, or near-duplicate overlapping windows
    would appear on both sides and inflate scores."""
    trials = np.repeat(np.arange(20), 8)          # 20 trials, 8 overlapping windows each
    y = np.repeat(np.arange(20) % 4, 8)
    X = np.zeros((len(trials), 5))
    for tr, va in GroupKFold(n_splits=4).split(X, y, groups=trials):
        assert not (set(trials[tr]) & set(trials[va]))
