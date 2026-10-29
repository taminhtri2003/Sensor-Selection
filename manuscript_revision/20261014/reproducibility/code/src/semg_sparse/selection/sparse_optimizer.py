"""
Sparse Channel Selection & Optimization Module.
Implements selection methods:
1. Cross-fitted SHAP ranking
2. Random channel baseline (100 resamples)
3. Geometry-spread (uniform circumferential coverage)
4. Mutual Information (mRMR proxy)
5. Permutation Importance
"""

import numpy as np
from sklearn.feature_selection import mutual_info_classif
from typing import List, Dict, Tuple

def select_top_k_channels(channel_ranking: List[int], k: int) -> List[int]:
    """Selects top-k channels given an ordered ranking list (0-indexed)."""
    return list(channel_ranking[:k])

def generate_random_channel_subsets(n_channels: int, k: int, n_subsets: int = 100, seed: int = 20260728) -> List[List[int]]:
    """Generates n_subsets random combinations of k channels."""
    rng = np.random.default_rng(seed)
    subsets = []
    for _ in range(n_subsets):
        sub = list(rng.choice(n_channels, size=k, replace=False))
        subsets.append(sorted(sub))
    return subsets

def geometry_spread_selection(n_channels: int, k: int) -> List[int]:
    """
    Uniform geometry-spread baseline for 16-channel dual-ring circumferential sEMG array.
    Ring 1 (Upper): 0..7
    Ring 2 (Lower): 8..15
    Selection selects evenly spaced positions across both rings.
    """
    if k >= n_channels:
        return list(range(n_channels))
    if k == 1:
        return [0]
    
    # 8 channels per ring
    # Spread selection greedily maximising minimum angular distance
    ring1 = np.arange(8)
    ring2 = np.arange(8, 16)
    
    selected = []
    # Alternate between Ring 1 and Ring 2 to maximize spatial distribution
    r1_step = max(1, 8 // max(1, (k + 1) // 2))
    r2_step = max(1, 8 // max(1, k // 2))

    idx1 = 0
    idx2 = 0
    while len(selected) < k:
        if len(selected) < k and idx1 < 8:
            ch = int(ring1[int(idx1) % 8])
            if ch not in selected: selected.append(ch)
            idx1 += r1_step
        if len(selected) < k and idx2 < 8:
            ch = int(ring2[int(idx2) % 8])
            if ch not in selected: selected.append(ch)
            idx2 += r2_step
        if idx1 >= 16 and idx2 >= 16:
            for ch in range(n_channels):
                if ch not in selected:
                    selected.append(ch)
                    if len(selected) == k: break

    return sorted(selected[:k])

def mutual_information_selection(X_train: np.ndarray, y_train: np.ndarray, n_channels: int, n_features_per_channel: int = 10, k: int = 4) -> List[int]:
    """
    Selects top-k channels using Mutual Information scores with target labels.
    """
    # X_train shape: (N, n_channels * n_features_per_channel)
    mi_scores = mutual_info_classif(X_train, y_train, random_state=20260728)
    mi_reshaped = mi_scores.reshape(n_channels, n_features_per_channel)
    channel_mi = np.mean(mi_reshaped, axis=1) # (n_channels,)
    ranking = list(np.argsort(channel_mi)[::-1])
    return ranking[:k]
