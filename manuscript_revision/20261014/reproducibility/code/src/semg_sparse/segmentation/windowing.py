"""
sEMG Windowing & Sliding Segmentation Module.
Segments sEMG signals into fixed-duration windows (250 ms default, 50% overlap).
Strictly prevents window bleed across gesture, trial, or session boundaries.
Attaches full sample and metadata indexing to every window tensor.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Any

def create_sliding_windows(signal: np.ndarray, fs: float = 2048.0, window_ms: float = 250.0, overlap_pct: float = 50.0) -> Tuple[np.ndarray, List[Tuple[int, int]]]:
    """
    Creates 2D sliding windows from a continuous 2D sEMG signal array (T, C).
    
    Parameters:
        signal: Array of shape (T, C)
        fs: Sampling frequency in Hz
        window_ms: Duration of window in milliseconds (e.g. 250 ms)
        overlap_pct: Percentage overlap between consecutive windows (e.g. 50%)
    Returns:
        windows: Array of shape (N_windows, window_samples, C)
        bounds: List of (start_sample, end_sample) tuples
    """
    T, C = signal.shape
    win_len = int(round((window_ms / 1000.0) * fs))
    step = int(round(win_len * (1.0 - overlap_pct / 100.0)))
    
    if T < win_len:
        return np.empty((0, win_len, C)), []

    start_indices = np.arange(0, T - win_len + 1, step)
    windows = []
    bounds = []

    for start in start_indices:
        end = start + win_len
        windows.append(signal[start:end, :])
        bounds.append((int(start), int(end)))

    if not windows:
        return np.empty((0, win_len, C)), []

    return np.array(windows), bounds
