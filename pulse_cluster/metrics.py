
from __future__ import annotations
import numpy as np
from typing import Optional

def correlation_distance(a: np.ndarray, b: np.ndarray) -> float:
    """1 - Pearson correlation in [-1,1] -> distance in [0,2]."""
    if a.size != b.size:
        L = min(len(a), len(b))
        a = a[:L]; b = b[:L]
    if a.std() < 1e-8 or b.std() < 1e-8:
        return 1.0
    r = np.corrcoef(a, b)[0,1]
    return float(1.0 - r)

def dtw_distance(a: np.ndarray, b: np.ndarray, window: Optional[int] = None) -> float:
    """Classic DTW (O(n^2)) with optional Sakoe-Chiba window in samples."""
    n, m = len(a), len(b)
    if window is None:
        window = max(n, m)
    window = max(window, abs(n - m))
    INF = 1e18
    D = np.full((n+1, m+1), INF, dtype=float)
    D[0,0] = 0.0
    for i in range(1, n+1):
        j_start = max(1, i - window)
        j_end = min(m, i + window)
        for j in range(j_start, j_end+1):
            cost = (a[i-1] - b[j-1])**2
            D[i,j] = cost + min(D[i-1,j], D[i,j-1], D[i-1,j-1])
    return float(np.sqrt(D[n,m]))
