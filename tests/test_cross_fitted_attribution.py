"""Tests for cross-fitted attribution and stability-regularised ranking.

These exercise the actual project code on data with a known answer, rather than asserting
properties of numpy or sklearn on synthetic arrays. Each test is written so that it fails if the
behaviour it describes regresses.
"""

import numpy as np
import pytest

from src.semg_sparse.xai.cross_fitted import (
    CrossFittedAttribution,
    assert_channel_major,
    channel_importance_from_contribs,
    compute_cross_fitted_attribution,
)

N_CH = 6
N_FPC = 4
FEATS = [f"ch{c+1}_{f}" for c in range(N_CH) for f in ("MAV", "RMS", "WL", "ZC")]
INFORMATIVE = (1, 4)   # only these channels carry class signal


def make_dataset(n_subjects=10, per_class=40, seed=0):
    """Signal lives only in INFORMATIVE channels; the rest is subject-specific noise.

    Subject-specific offsets are deliberately large so that a method which leaks subject
    identity, or which attributes on training subjects, is tempted toward the noise channels.
    """
    rng = np.random.default_rng(seed)
    X, y, s = [], [], []
    for subj in range(n_subjects):
        offsets = rng.normal(0, 3.0, size=N_CH * N_FPC)
        for cls in (0, 1, 2):
            block = rng.normal(0, 1.0, size=(per_class, N_CH * N_FPC)) + offsets
            for ch in INFORMATIVE:
                block[:, ch * N_FPC:(ch + 1) * N_FPC] += cls * 6.0
            X.append(block)
            y.append(np.full(per_class, cls))
            s.append(np.full(per_class, subj))
    return (np.vstack(X).astype(np.float32), np.concatenate(y), np.concatenate(s))


def test_assert_channel_major_accepts_correct_layout():
    assert_channel_major(FEATS, N_CH, N_FPC)


def test_assert_channel_major_rejects_interleaved_layout():
    # Feature-major ordering (all MAVs, then all RMSs...) must be rejected: reshaping it as if it
    # were channel-major would silently blend channels and produce a meaningless ranking.
    interleaved = [f"ch{c+1}_{f}" for f in ("MAV", "RMS", "WL", "ZC") for c in range(N_CH)]
    with pytest.raises(ValueError, match="channel-major"):
        assert_channel_major(interleaved, N_CH, N_FPC)


def test_assert_channel_major_rejects_wrong_count():
    with pytest.raises(ValueError, match="expected"):
        assert_channel_major(FEATS[:-1], N_CH, N_FPC)


def test_channel_importance_drops_bias_and_averages_classes():
    n, n_cls, n_feat = 7, 3, N_CH * N_FPC
    contribs = np.zeros((n, n_cls, n_feat + 1))
    contribs[:, :, 2 * N_FPC:3 * N_FPC] = 5.0     # channel 2 carries all attribution
    contribs[:, :, -1] = 999.0                    # bias column must be ignored
    imp = channel_importance_from_contribs(contribs, N_CH, N_FPC)
    assert imp.shape == (N_CH,)
    assert imp.argmax() == 2
    assert np.allclose(imp[[0, 1, 3, 4, 5]], 0.0)


def test_recovers_informative_channels():
    X, y, s = make_dataset()
    res = compute_cross_fitted_attribution(
        X, y, s, FEATS, n_channels=N_CH, n_features_per_channel=N_FPC,
        n_inner_folds=5, device="cpu", xgb_params={"n_estimators": 40, "max_depth": 3},
        max_attrib_samples=500,
    )
    top2 = set(res.ranking(lam=0.0)[:2])
    assert top2 == set(INFORMATIVE), f"expected {INFORMATIVE}, got ranking {res.ranking()}"


def test_per_fold_matrix_is_retained_and_normalised():
    X, y, s = make_dataset()
    res = compute_cross_fitted_attribution(
        X, y, s, FEATS, n_channels=N_CH, n_features_per_channel=N_FPC,
        n_inner_folds=5, device="cpu", xgb_params={"n_estimators": 40, "max_depth": 3},
        max_attrib_samples=500,
    )
    # Fold identity must survive: stability cannot be computed from a pre-averaged vector.
    assert res.importance_norm.shape == (5, N_CH)
    assert np.allclose(res.importance_norm.sum(axis=1), 1.0)
    assert len(res.fold_subjects) == 5


def test_inner_folds_partition_subjects_without_overlap():
    X, y, s = make_dataset()
    res = compute_cross_fitted_attribution(
        X, y, s, FEATS, n_channels=N_CH, n_features_per_channel=N_FPC,
        n_inner_folds=5, device="cpu", xgb_params={"n_estimators": 20, "max_depth": 3},
        max_attrib_samples=300,
    )
    held = [set(f) for f in res.fold_subjects]
    for a in range(len(held)):
        for b in range(a + 1, len(held)):
            assert not (held[a] & held[b]), "a subject was attributed in two inner folds"
    assert set().union(*held) == set(range(10)), "every training subject should be attributed once"


def test_stability_penalty_demotes_an_erratic_channel():
    # Channel 0 is on average as important as channel 3, but wildly inconsistent across folds.
    # Plain magnitude ranking should tie them; the stability penalty must demote channel 0.
    # Rows are built to already sum to 1 so that row-normalisation is a no-op and the intended
    # tie in central magnitude actually survives into the ranking.
    imp = np.array([
        [0.40, 0.10, 0.10, 0.20, 0.10, 0.10],
        [0.00, 0.20, 0.20, 0.20, 0.20, 0.20],
        [0.40, 0.10, 0.10, 0.20, 0.10, 0.10],
        [0.00, 0.20, 0.20, 0.20, 0.20, 0.20],
    ])
    assert np.allclose(imp.sum(axis=1), 1.0)
    res = CrossFittedAttribution(
        importance_raw=imp, importance_norm=imp / imp.sum(1, keepdims=True),
        fold_subjects=[[0], [1], [2], [3]], n_attrib_samples=[10] * 4,
    )
    assert res.instability()[0] > res.instability()[3]
    assert res.ranking(lam=0.0)[0] == 0        # magnitude alone favours the erratic channel
    assert res.ranking(lam=2.0)[0] == 3        # stability regularisation prefers the steady one


def test_lambda_zero_matches_plain_magnitude_ranking():
    rng = np.random.default_rng(3)
    imp = rng.random((5, N_CH))
    res = CrossFittedAttribution(
        importance_raw=imp, importance_norm=imp / imp.sum(1, keepdims=True),
        fold_subjects=[[i] for i in range(5)], n_attrib_samples=[10] * 5,
    )
    assert res.ranking(lam=0.0) == list(np.argsort(-res.central()))
