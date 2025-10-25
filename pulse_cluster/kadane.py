
from __future__ import annotations
import numpy as np
from typing import Tuple

def kadane_max_subarray(arr: np.ndarray) -> Tuple[int, int, float]:
    """Kadane's algorithm: returns (start_idx, end_idx_exclusive, max_sum)."""
    max_so_far = -1e18
    max_ending_here = 0.0
    start = 0
    best_l = 0
    best_r = 0
    for i, x in enumerate(arr):
        if max_ending_here <= 0:
            max_ending_here = x
            start = i
        else:
            max_ending_here += x
        if max_ending_here > max_so_far:
            max_so_far = max_ending_here
            best_l = start
            best_r = i + 1
    return best_l, best_r, float(max_so_far)

def most_active_interval(x: np.ndarray, transform: str = "absdiff"):
    """Compute the most active interval using Kadane on a transformed sequence.
    transform = 'absdiff' (default) or 'sqdiff'.
    Returns (l, r, score).
    """
    dx = np.diff(x)
    if transform == "sqdiff":
        y = dx * dx
    else:
        y = np.abs(dx)
    return kadane_max_subarray(y)
