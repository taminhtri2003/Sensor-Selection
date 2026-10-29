"""
Signal Preprocessing Module for sEMG.
Implements zero-phase Butterworth bandpass filtering, notch filtering, and normalizers.
All preprocessing parameters are zero-leakage and strictly training-data derived.
"""

import numpy as np
from scipy.signal import butter, filtfilt, iirnotch

def bandpass_filter(data: np.ndarray, fs: float, lowcut: float = 20.0, highcut: float = 450.0, order: int = 4) -> np.ndarray:
    """
    Applies zero-phase 4th-order Butterworth bandpass filter to sEMG signal.
    
    Parameters:
        data: sEMG array of shape (time_samples, n_channels)
        fs: Sampling frequency in Hz
        lowcut: Lower cutoff frequency in Hz (default: 20.0 Hz)
        highcut: Upper cutoff frequency in Hz (default: min(450.0, 0.45*fs))
        order: Filter order (default: 4)
    Returns:
        Filtered sEMG array of same shape
    """
    nyq = 0.5 * fs
    effective_highcut = min(highcut, 0.45 * nyq * 2.0 - 1.0)
    if lowcut >= effective_highcut:
        # For lower sampling rates (e.g. 200 Hz), adjust lowcut/highcut safely
        lowcut = 10.0
        effective_highcut = 90.0

    low = lowcut / nyq
    high = effective_highcut / nyq
    b, a = butter(order, [low, high], btype='bandpass')
    
    # Apply zero-phase filtering along time axis (axis 0)
    filtered = filtfilt(b, a, data, axis=0)
    return filtered

def notch_filter(data: np.ndarray, fs: float, notch_freq: float = 50.0, quality_factor: float = 30.0) -> np.ndarray:
    """
    Applies zero-phase IIR notch filter for powerline interference removal.
    
    Parameters:
        data: sEMG array of shape (time_samples, n_channels)
        fs: Sampling frequency in Hz
        notch_freq: Frequency to reject in Hz (e.g. 50.0 or 60.0 Hz)
        quality_factor: Quality factor Q
    Returns:
        Filtered sEMG array of same shape
    """
    nyq = 0.5 * fs
    if notch_freq >= nyq:
        return data # Frequency beyond Nyquist limit
    
    w0 = notch_freq / nyq
    b, a = iirnotch(w0, quality_factor)
    filtered = filtfilt(b, a, data, axis=0)
    return filtered

class StandardChannelScaler:
    """
    StandardScaler per channel fitted ONLY on training data.
    Ensures zero leakage across outer validation participants.
    """
    def __init__(self):
        self.mean_ = None
        self.std_ = None

    def fit(self, X: np.ndarray):
        """X shape: (n_samples, n_channels) or (n_windows, n_channels, time)"""
        if X.ndim == 2:
            self.mean_ = np.mean(X, axis=0, keepdims=True)
            self.std_ = np.std(X, axis=0, keepdims=True) + 1e-8
        elif X.ndim == 3:
            # (n_windows, n_channels, n_time)
            self.mean_ = np.mean(X, axis=(0, 2), keepdims=True)
            self.std_ = np.std(X, axis=(0, 2), keepdims=True) + 1e-8
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        if self.mean_ is None:
            raise ValueError("StandardChannelScaler is not fitted yet.")
        return (X - self.mean_) / self.std_

    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        return self.fit(X).transform(X)
