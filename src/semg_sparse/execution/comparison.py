"""Participant-grid checks used before producing independent-run comparisons."""
from itertools import product

import numpy as np


def validate_grid(frame, keys, expected, label):
    required = set(keys) | {'macro_f1'}
    if not required <= set(frame.columns) or frame.empty:
        raise ValueError(label + ': missing columns or empty participant grid')
    if frame[keys].isna().any().any() or frame.duplicated(keys).any():
        raise ValueError(label + ': null or duplicate participant keys')
    actual = set(frame[keys].itertuples(index=False, name=None))
    grid = set(product(*(expected[key] for key in keys)))
    if actual != grid:
        raise ValueError(f'{label}: participant grid mismatch ({len(actual)} versus {len(grid)})')
    if not np.isfinite(frame['macro_f1'].to_numpy(dtype=float)).all():
        raise ValueError(label + ': nonfinite macro_f1')
    if not frame['macro_f1'].between(0, 1).all():
        raise ValueError(label + ': macro_f1 outside [0, 1]')
