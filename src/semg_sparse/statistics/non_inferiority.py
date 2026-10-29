"""
Statistical Non-Inferiority & Participant-Level Bootstrap Module.
Implements non-inferiority testing under prespecified margins delta in {0.01, 0.02, 0.03} Macro-F1.
Uses participant-level bootstrap (10,000 resamples) to compute percentile CIs and LCBs.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple

def bootstrap_participant_metrics(
    participant_scores: np.ndarray,
    n_resamples: int = 10000,
    confidence_level: float = 0.95,
    seed: int = 20260728
) -> Tuple[float, float, float]:
    """
    Computes participant-level mean and percentile bootstrap confidence interval.
    
    Parameters:
        participant_scores: 1D array of metric values per participant (N_subjects,)
        n_resamples: Number of bootstrap iterations (default: 10,000)
        confidence_level: Desired confidence level (default: 0.95)
        seed: Random seed for reproducibility
    Returns:
        mean: Sample mean score
        lcb: Lower confidence bound
        ucb: Upper confidence bound
    """
    participant_scores = np.asarray(participant_scores, dtype=float)
    if (participant_scores.ndim != 1 or len(participant_scores) < 2
            or not np.isfinite(participant_scores).all()):
        raise ValueError("bootstrap requires a finite one-dimensional participant score vector")
    if n_resamples < 1 or not 0 < confidence_level < 1:
        raise ValueError("invalid bootstrap resample count or confidence level")
    rng = np.random.default_rng(seed)
    N = len(participant_scores)
    
    # Resample whole participants with replacement
    boot_idx = rng.choice(N, size=(n_resamples, N), replace=True)
    boot_means = np.mean(participant_scores[boot_idx], axis=1)

    alpha = 1.0 - confidence_level
    lcb = np.percentile(boot_means, (alpha / 2.0) * 100.0)
    ucb = np.percentile(boot_means, (1.0 - alpha / 2.0) * 100.0)
    mean_val = np.mean(participant_scores)

    return float(mean_val), float(lcb), float(ucb)

def evaluate_non_inferiority(
    scores_k: np.ndarray,
    scores_full: np.ndarray,
    margin_delta: float = 0.02,
    n_resamples: int = 10000,
    seed: int = 20260728,
    participants_k: np.ndarray = None,
    participants_full: np.ndarray = None,
) -> Dict[str, float]:
    """
    Evaluates statistical non-inferiority of k-channel model vs 16-channel full array.
    Delta_p = score_k[p] - score_full[p]
    Non-inferior if LCB_95%(Delta) > -delta.

    The paired difference is only meaningful if the two score arrays are aligned participant by
    participant. Pass participants_k/participants_full to have that enforced rather than assumed;
    a silent misalignment would produce a plausible but meaningless paired difference.
    """
    scores_k = np.asarray(scores_k, dtype=float)
    scores_full = np.asarray(scores_full, dtype=float)
    if not np.isfinite(margin_delta) or margin_delta <= 0:
        raise ValueError("non-inferiority margin must be finite and positive")

    if scores_k.shape != scores_full.shape:
        raise ValueError(
            f"paired arrays must have equal length: {scores_k.shape} vs {scores_full.shape}"
        )
    if participants_k is not None or participants_full is not None:
        if participants_k is None or participants_full is None:
            raise ValueError("supply both participants_k and participants_full, or neither")
        pk = np.asarray(participants_k)
        pf = np.asarray(participants_full)
        if (pk.ndim != 1 or pf.ndim != 1 or len(pk) != len(scores_k)
                or len(pf) != len(scores_full) or len(np.unique(pk)) != len(pk)
                or len(np.unique(pf)) != len(pf)):
            raise ValueError("participant identifiers must be unique and match score lengths")
        if not np.array_equal(pk, pf):
            raise ValueError(
                "participant order differs between the two score arrays; the paired difference "
                f"would compare different people. k-order={pk[:5]}... full-order={pf[:5]}..."
            )

    deltas = scores_k - scores_full
    mean_diff, lcb, ucb = bootstrap_participant_metrics(deltas, n_resamples=n_resamples, seed=seed)

    is_non_inferior = lcb > (-margin_delta)

    return {
        "mean_diff": mean_diff,
        "lcb_95": lcb,
        "ucb_95": ucb,
        "margin_delta": margin_delta,
        "n_participants": int(len(deltas)),
        "is_non_inferior": bool(is_non_inferior)
    }

def find_optimal_k_star(
    metrics_per_k: Dict[int, np.ndarray],
    scores_full: np.ndarray,
    margin_delta: float = 0.02,
    n_resamples: int = 10000
) -> Tuple[int, pd.DataFrame]:
    """
    Identifies minimum non-inferior channel count k* = min { k : LCB_95(Delta_k) > -delta }.
    """
    results = []
    k_star = None

    sorted_ks = sorted(metrics_per_k.keys())
    for k in sorted_ks:
        res = evaluate_non_inferiority(metrics_per_k[k], scores_full, margin_delta=margin_delta, n_resamples=n_resamples)
        res['k'] = k
        results.append(res)
        if res['is_non_inferior'] and k_star is None:
            k_star = k

    df_res = pd.DataFrame(results)

    # k_star stays None when no channel count met the margin. It is NOT backfilled with the
    # largest k.
    #
    # The previous implementation did exactly that ("default to max if non-inferiority not met"),
    # which silently converts a null result into a positive-looking one: a caller receiving
    # k_star = 16 cannot tell whether 16 channels were found non-inferior or whether nothing was,
    # and the study's headline claim is precisely "k* channels suffice". A failure to establish
    # non-inferiority is a finding and must be reported as one -- see the frozen analysis plan,
    # which forbids relaxing the margin to manufacture a positive claim.
    return k_star, df_res
