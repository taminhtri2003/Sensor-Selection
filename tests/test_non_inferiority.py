"""Tests for participant-level bootstrap and non-inferiority decisions.

The decision rule these functions implement is the study's headline claim ("k channels are
non-inferior to 16"), so the tests focus on the ways that claim could be wrongly produced:
a null result silently reported as positive, or a paired comparison run on misaligned people.
"""

import numpy as np
import pytest

from src.semg_sparse.statistics.non_inferiority import (
    bootstrap_participant_metrics,
    evaluate_non_inferiority,
    find_optimal_k_star,
)

SEED = 20260728


def test_bootstrap_ci_brackets_the_mean():
    rng = np.random.default_rng(SEED)
    scores = rng.normal(0.55, 0.08, size=43)
    mean, lcb, ucb = bootstrap_participant_metrics(scores, n_resamples=2000, seed=SEED)
    assert lcb < mean < ucb
    assert np.isclose(mean, scores.mean())


def test_bootstrap_is_deterministic_under_fixed_seed():
    rng = np.random.default_rng(1)
    scores = rng.normal(0.5, 0.1, size=43)
    a = bootstrap_participant_metrics(scores, n_resamples=1000, seed=SEED)
    b = bootstrap_participant_metrics(scores, n_resamples=1000, seed=SEED)
    assert a == b


def test_bootstrap_ci_widens_with_fewer_participants():
    rng = np.random.default_rng(2)
    big = rng.normal(0.55, 0.08, size=43)
    small = big[:8]
    _, l_big, u_big = bootstrap_participant_metrics(big, n_resamples=3000, seed=SEED)
    _, l_small, u_small = bootstrap_participant_metrics(small, n_resamples=3000, seed=SEED)
    assert (u_small - l_small) > (u_big - l_big), \
        "a smaller cohort must not produce a tighter interval"


def test_clearly_non_inferior_case_is_detected():
    rng = np.random.default_rng(3)
    full = rng.normal(0.560, 0.06, size=43)
    k = full - rng.normal(0.002, 0.004, size=43)      # trivially worse
    res = evaluate_non_inferiority(k, full, margin_delta=0.02, n_resamples=3000, seed=SEED)
    assert res["is_non_inferior"]
    assert res["lcb_95"] > -0.02


def test_clearly_inferior_case_is_rejected():
    rng = np.random.default_rng(4)
    full = rng.normal(0.560, 0.06, size=43)
    k = full - rng.normal(0.080, 0.010, size=43)      # substantially worse
    res = evaluate_non_inferiority(k, full, margin_delta=0.02, n_resamples=3000, seed=SEED)
    assert not res["is_non_inferior"]
    assert res["lcb_95"] < -0.02


def test_k_star_is_none_when_nothing_is_non_inferior():
    """The regression this file exists for.

    The earlier implementation backfilled k_star with max(k) when no channel count met the
    margin, making a null result indistinguishable from a positive one.
    """
    rng = np.random.default_rng(5)
    full = rng.normal(0.560, 0.06, size=43)
    metrics = {k: full - rng.normal(0.10, 0.01, size=43) for k in (4, 6, 8, 12)}
    k_star, df = find_optimal_k_star(metrics, full, margin_delta=0.02, n_resamples=1500)
    assert k_star is None, "failure to establish non-inferiority must not be reported as k*=max"
    assert not df.is_non_inferior.any()


def test_k_star_picks_the_smallest_non_inferior_k():
    rng = np.random.default_rng(6)
    full = rng.normal(0.560, 0.06, size=43)
    metrics = {
        2: full - rng.normal(0.15, 0.01, size=43),    # inferior
        4: full - rng.normal(0.09, 0.01, size=43),    # inferior
        8: full - rng.normal(0.003, 0.003, size=43),  # non-inferior
        12: full - rng.normal(0.001, 0.002, size=43),  # non-inferior
    }
    k_star, df = find_optimal_k_star(metrics, full, margin_delta=0.02, n_resamples=1500)
    assert k_star == 8
    assert not df.set_index("k").loc[4, "is_non_inferior"]


def test_misaligned_participants_raise_rather_than_compare_strangers():
    rng = np.random.default_rng(7)
    full = rng.normal(0.56, 0.06, size=10)
    k = full - 0.005
    ids = np.arange(10)
    with pytest.raises(ValueError, match="participant order differs"):
        evaluate_non_inferiority(k, full, participants_k=ids, participants_full=ids[::-1],
                                 n_resamples=200)


def test_length_mismatch_raises():
    with pytest.raises(ValueError, match="equal length"):
        evaluate_non_inferiority(np.zeros(10), np.zeros(9), n_resamples=200)


def test_duplicate_participants_cannot_count_as_independent_people():
    with pytest.raises(ValueError, match='unique'):
        evaluate_non_inferiority(np.ones(3), np.ones(3), participants_k=[1,1,2],
                                participants_full=[1,1,2])


@pytest.mark.parametrize('scores', [[], [0.5], [0.5, np.nan], [[0.5,0.6],[0.7,0.8]]])
def test_bootstrap_rejects_missing_or_nonparticipant_arrays(scores):
    with pytest.raises(ValueError, match='participant score vector'):
        bootstrap_participant_metrics(np.asarray(scores))


def test_margin_sensitivity_is_monotone():
    """A stricter margin can never declare non-inferiority where a looser one did not."""
    rng = np.random.default_rng(8)
    full = rng.normal(0.56, 0.06, size=43)
    k = full - rng.normal(0.015, 0.006, size=43)
    verdicts = {
        m: evaluate_non_inferiority(k, full, margin_delta=m, n_resamples=2000,
                                    seed=SEED)["is_non_inferior"]
        for m in (0.01, 0.02, 0.03)
    }
    assert not (verdicts[0.01] and not verdicts[0.03])
