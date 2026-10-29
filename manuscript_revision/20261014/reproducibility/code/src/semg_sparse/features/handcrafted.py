"""
Handcrafted sEMG Feature Extraction Module.
Extracts 8 core time-domain and 2 frequency-domain features per window per channel:
MAV, RMS, Variance, WL, ZC, SSC, IEMG, WAMP, MNF, MDF.
Produces a feature matrix of shape (n_windows, n_channels * n_features) with full indexing metadata.
"""

import numpy as np
from scipy.signal import welch

FEATURE_NAMES = [
    "MAV", "RMS", "VAR", "WL", "ZC", "SSC", "IEMG", "WAMP", "MNF", "MDF"
]

# Amplitude thresholds in mV, derived from the empirical signal audit of raw GRABMyo
# (reports/signal_properties_audit.md): median |x| = 2.31e-2 mV, median |diff(x)| = 8.74e-3 mV.
#
# The previous defaults (zc/ssc 1e-5 mV, wamp 1e-4 mV) sat 1-2 orders of magnitude below the
# median first difference, so the threshold never gated anything: WAMP counted almost every
# sample and saturated at its ceiling of T-1 (median 509/511, 17.9% of values exactly at max),
# carrying essentially no information. Thresholds are now set just above the median |diff| so
# the counts span their dynamic range.
#
# These are fixed constants applied identically to every window of every participant. They are
# never fitted from data, so they introduce no train/test leakage.
DEFAULT_ZC_THRESH_MV = 1.0e-2
DEFAULT_SSC_THRESH_MV = 1.0e-2
DEFAULT_WAMP_THRESH_MV = 1.0e-2


def extract_window_features(window: np.ndarray, fs: float = 2048.0,
                            zc_thresh: float = DEFAULT_ZC_THRESH_MV,
                            ssc_thresh: float = DEFAULT_SSC_THRESH_MV,
                            wamp_thresh: float = DEFAULT_WAMP_THRESH_MV) -> np.ndarray:
    """
    Extracts feature vector for a single window of sEMG signal.
    
    Parameters:
        window: np.ndarray of shape (time_samples, n_channels)
        fs: Sampling frequency in Hz
        zc_thresh: Threshold for Zero Crossings
        ssc_thresh: Threshold for Slope Sign Changes
        wamp_thresh: Threshold for Willison Amplitude
    Returns:
        1D feature array of length (n_channels * len(FEATURE_NAMES))
    """
    T, C = window.shape
    feats = []

    # 1. MAV: Mean Absolute Value
    mav = np.mean(np.abs(window), axis=0) # (C,)
    
    # 2. RMS: Root Mean Square
    rms = np.sqrt(np.mean(window**2, axis=0)) # (C,)
    
    # 3. VAR: Variance
    var = np.var(window, axis=0) # (C,)
    
    # 4. WL: Waveform Length
    diff = np.diff(window, axis=0) # (T-1, C)
    wl = np.sum(np.abs(diff), axis=0) # (C,)
    
    # 5. ZC: Zero Crossings
    prod = window[:-1, :] * window[1:, :]
    zc_cond = (prod < 0) & (np.abs(diff) >= zc_thresh)
    zc = np.sum(zc_cond, axis=0) # (C,)
    
    # 6. SSC: Slope Sign Changes
    diff1 = window[1:-1, :] - window[:-2, :]
    diff2 = window[1:-1, :] - window[2:, :]
    ssc_cond = (diff1 * diff2 > 0) & ((np.abs(diff1) >= ssc_thresh) | (np.abs(diff2) >= ssc_thresh))
    ssc = np.sum(ssc_cond, axis=0) # (C,)
    
    # 7. IEMG: Integrated EMG
    iemg = np.sum(np.abs(window), axis=0) # (C,)
    
    # 8. WAMP: Willison Amplitude
    wamp = np.sum(np.abs(diff) >= wamp_thresh, axis=0) # (C,)
    
    # 9 & 10. MNF & MDF (Power Spectral Density)
    mnf = np.zeros(C)
    mdf = np.zeros(C)
    
    # Welch PSD per channel. Deliberately not wrapped in try/except: a spectral failure must
    # surface as an error rather than silently emitting zeros that look like valid features.
    freqs, psd = welch(window, fs=fs, nperseg=min(T, 256), axis=0)
    psd_sum = np.sum(psd, axis=0) + 1e-12
    mnf = np.sum(freqs[:, None] * psd, axis=0) / psd_sum

    cum_psd = np.cumsum(psd, axis=0)
    half_psd = psd_sum / 2.0
    for c in range(C):
        idx = np.searchsorted(cum_psd[:, c], half_psd[c])
        idx = min(idx, len(freqs) - 1)
        mdf[c] = freqs[idx]

    # Stack features per channel: shape (C, F)
    # Ordering: [MAV_ch1, RMS_ch1, ..., MAV_ch2, RMS_ch2, ...]
    feature_matrix = np.column_stack([mav, rms, var, wl, zc, ssc, iemg, wamp, mnf, mdf]) # (C, 10)
    return feature_matrix.flatten()

def get_feature_mapping(n_channels: int):
    """
    Returns list of feature names, channel mapping, and index dict.
    """
    names = []
    channel_index = []
    feature_index = []
    
    for c in range(n_channels):
        for f_name in FEATURE_NAMES:
            names.append(f"ch{c+1}_{f_name}")
            channel_index.append(c)
            feature_index.append(f_name)

    return names, channel_index, feature_index
