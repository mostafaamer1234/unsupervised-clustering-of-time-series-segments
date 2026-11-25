
from __future__ import annotations
from typing import Dict, List, Callable, Tuple
import numpy as np
import random

def _median_split(ids: List[str],
                  series: Dict[str, np.ndarray],
                  dist_fn: Callable[[np.ndarray, np.ndarray], float],
                  rng: random.Random | None = None) -> Tuple[List[str], List[str]]:
    """Pick a pivot medoid (random), compute distances, split by median distance."""
    pivot_id = (rng or random).choice(ids)
    pivot = series[pivot_id]
    dists = [(sid, dist_fn(series[sid], pivot)) for sid in ids if sid != pivot_id]
    if not dists:
        return ids, []
    med = np.median([d for _, d in dists])
    left = [sid for sid, d in dists if d <= med] + [pivot_id]
    right = [sid for sid, d in dists if d > med]
    return left, right

def _within_dispersion(ids: List[str],
                       series: Dict[str, np.ndarray],
                       dist_fn: Callable[[np.ndarray, np.ndarray], float]) -> float:
    """Average pairwise distance inside ids (O(k^2))."""
    if len(ids) < 2:
        return 0.0
    s = 0.0
    m = 0
    for i in range(len(ids)):
        for j in range(i+1, len(ids)):
            s += dist_fn(series[ids[i]], series[ids[j]])
            m += 1
    return s / m

def divide_and_conquer(ids: List[str],
                       series: Dict[str, np.ndarray],
                       dist_fn: Callable[[np.ndarray, np.ndarray], float],
                       max_depth: int = 6,
                       min_cluster_size: int = 20,
                       max_dispersion: float | None = None,
                       depth: int = 0,
                       seed: int | None = None,
                       _rng: random.Random | None = None) -> List[List[str]]:
    """Recursive top-down partitioning; stop on rules -> form a cluster.

    Pass `seed` for reproducible pivots; without it the global `random` state is used.
    """
    rng = _rng or (random.Random(seed) if seed is not None else None)
    if len(ids) <= min_cluster_size or depth >= max_depth:
        return [ids]
    if max_dispersion is not None:
        disp = _within_dispersion(ids, series, dist_fn)
        if disp <= max_dispersion:
            return [ids]
    left, right = _median_split(ids, series, dist_fn, rng)
    if not right:
        return [left]
    clusters = []
    clusters += divide_and_conquer(left, series, dist_fn, max_depth, min_cluster_size, max_dispersion, depth+1, _rng=rng)
    clusters += divide_and_conquer(right, series, dist_fn, max_depth, min_cluster_size, max_dispersion, depth+1, _rng=rng)
    return clusters
