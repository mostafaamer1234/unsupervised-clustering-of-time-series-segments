
from __future__ import annotations
from typing import Dict, Tuple, List, Callable
import numpy as np

def closest_pair(indices: List[str],
                 series: Dict[str, np.ndarray],
                 dist_fn: Callable[[np.ndarray, np.ndarray], float]) -> Tuple[Tuple[str,str], float]:
    """Brute-force closest pair inside a subset. Returns ((id1,id2), distance)."""
    best = (None, None)
    best_d = 1e18
    n = len(indices)
    for i in range(n):
        for j in range(i+1, n):
            a = series[indices[i]]
            b = series[indices[j]]
            d = dist_fn(a, b)
            if d < best_d:
                best_d = d
                best = (indices[i], indices[j])
    return (best[0], best[1]), float(best_d)
