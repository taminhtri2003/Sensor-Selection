"""
Cross-Fitted SHAP Explainability & Channel Ranking Module.
Implements leak-free out-of-fold SHAP attribution aggregation across outer training participants.
Computes multiclass TreeSHAP attributions and derives subject-independent channel rankings.
"""

import numpy as np
import pandas as pd
import shap
from sklearn.model_selection import GroupKFold
from typing import List, Dict, Tuple
from ..models.classifiers import build_xgboost_model

def compute_cross_fitted_shap(
    X_train: np.ndarray,
    y_train: np.ndarray,
    subjects_train: np.ndarray,
    n_channels: int,
    n_features_per_channel: int = 10,
    n_inner_folds: int = 5
) -> Tuple[np.ndarray, List[int]]:
    """
    Computes cross-fitted out-of-fold (OOF) TreeSHAP attributions on training participants.
    
    Parameters:
        X_train: Feature matrix of shape (N_samples, n_channels * n_features_per_channel)
        y_train: Label array of shape (N_samples,)
        subjects_train: Subject ID array of shape (N_samples,)
        n_channels: Number of channels (e.g. 16)
        n_features_per_channel: Number of features per channel (e.g. 10)
        n_inner_folds: Number of inner validation folds
    Returns:
        channel_importance: Array of shape (n_channels,) containing mean absolute SHAP values
        channel_ranking: List of 0-indexed channel IDs sorted from most to least important
    """
    gkf = GroupKFold(n_splits=n_inner_folds)
    unique_subs = np.unique(subjects_train)
    actual_splits = min(n_inner_folds, len(unique_subs))
    gkf = GroupKFold(n_splits=actual_splits)

    oof_shap_values = np.zeros_like(X_train, dtype=np.float32)

    for train_idx, val_idx in gkf.split(X_train, y_train, groups=subjects_train):
        X_tr, y_tr = X_train[train_idx], y_train[train_idx]
        X_va, y_va = X_train[val_idx], y_train[val_idx]

        model = build_xgboost_model()
        model.fit(X_tr, y_tr)

        explainer = shap.TreeExplainer(model)
        shap_vals = explainer.shap_values(X_va)

        # Handle multiclass SHAP shapes:
        # shap_vals can be list of arrays [class_0, class_1, ...] or ndarray (N, F, C_classes)
        if isinstance(shap_vals, list):
            # List of (N_val, N_feats)
            abs_sum = np.zeros_like(X_va, dtype=np.float32)
            for c_shap in shap_vals:
                abs_sum += np.abs(c_shap)
            oof_shap_values[val_idx] = abs_sum / len(shap_vals)
        elif isinstance(shap_vals, np.ndarray):
            if shap_vals.ndim == 3:
                oof_shap_values[val_idx] = np.mean(np.abs(shap_vals), axis=-1)
            else:
                oof_shap_values[val_idx] = np.abs(shap_vals)

    # Reshape feature dimensions to (N, n_channels, n_features_per_channel)
    N_samples = len(X_train)
    shap_reshaped = oof_shap_values.reshape(N_samples, n_channels, n_features_per_channel)

    # Compute global channel importance: mean over samples and features
    channel_importance = np.mean(shap_reshaped, axis=(0, 2)) # (n_channels,)

    # Derive channel ranking (descending order of importance)
    channel_ranking = list(np.argsort(channel_importance)[::-1])

    return channel_importance, channel_ranking
