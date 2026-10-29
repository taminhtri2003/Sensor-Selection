"""
Automated Pipeline Component Test Suite.
Tests signal filtering, sliding window boundary isolation, feature extraction shapes,
scaler normalization, and non-inferiority bootstrap calculation.
"""

import pytest
import numpy as np

from src.semg_sparse.preprocessing.filters import bandpass_filter, notch_filter, StandardChannelScaler
from src.semg_sparse.segmentation.windowing import create_sliding_windows
from src.semg_sparse.features.handcrafted import extract_window_features, get_feature_mapping
from src.semg_sparse.selection.sparse_optimizer import geometry_spread_selection
from src.semg_sparse.statistics.non_inferiority import bootstrap_participant_metrics, evaluate_non_inferiority

def test_filtering_shape():
    data = np.random.randn(2048, 16) # 1 sec signal at 2048 Hz
    filt = bandpass_filter(data, fs=2048.0, lowcut=20.0, highcut=450.0)
    assert filt.shape == data.shape
    notch = notch_filter(filt, fs=2048.0, notch_freq=50.0)
    assert notch.shape == data.shape

def test_sliding_windows():
    data = np.random.randn(2048, 16) # 1 sec at 2048 Hz (2048 samples)
    # 250 ms window = 512 samples, 50% overlap = 256 step
    windows, bounds = create_sliding_windows(data, fs=2048.0, window_ms=250.0, overlap_pct=50.0)
    assert windows.ndim == 3
    assert windows.shape[1] == 512
    assert windows.shape[2] == 16
    assert len(bounds) == len(windows)

def test_feature_extraction_dimension():
    window = np.random.randn(512, 16)
    feats = extract_window_features(window, fs=2048.0)
    assert len(feats) == 16 * 10 # 16 channels x 10 features = 160

    names, ch_idx, f_idx = get_feature_mapping(16)
    assert len(names) == 160
    assert len(ch_idx) == 160

def test_scaler_zero_leakage():
    X_tr = np.array([[1.0, 10.0], [3.0, 30.0]])
    X_te = np.array([[2.0, 20.0]])

    scaler = StandardChannelScaler()
    scaler.fit(X_tr)

    assert scaler.mean_[0, 0] == 2.0
    assert scaler.mean_[0, 1] == 20.0

    X_te_sc = scaler.transform(X_te)
    assert X_te_sc[0, 0] == 0.0 # 2.0 is exact mean of train
    assert X_te_sc[0, 1] == 0.0

def test_geometry_spread_selection():
    sel_4 = geometry_spread_selection(16, 4)
    assert len(sel_4) == 4
    assert len(set(sel_4)) == 4
    assert all(0 <= c < 16 for c in sel_4)

def test_bootstrap_non_inferiority():
    scores_k = np.full(43, 0.84)
    scores_full = np.full(43, 0.85)

    res = evaluate_non_inferiority(scores_k, scores_full, margin_delta=0.02, n_resamples=1000)
    assert res['is_non_inferior'] is True # diff -0.01 > -0.02
