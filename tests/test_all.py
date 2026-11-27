
import numpy as np
from pulse_cluster.kadane import kadane_max_subarray, most_active_interval
from pulse_cluster.metrics import dtw_distance, correlation_distance
from pulse_cluster.divide_conquer import divide_and_conquer

def test_kadane_basic():
    arr = np.array([-2, 1, -3, 4, -1, 2, 1, -5, 4])
    l, r, s = kadane_max_subarray(arr)
    assert (l, r, int(s)) == (3, 7, 6)

def test_most_active_interval():
    x = np.array([0, 1, 2, 10, 9, 8, 8, 8], dtype=float)
    l, r, s = most_active_interval(x, transform="absdiff")
    assert l < r and s > 0

def test_most_active_interval_finds_the_burst_not_the_whole_series():
    x = np.tile([0.05, -0.05], 50)  # a calm signal is still never perfectly flat
    x[40:60] = np.tile([1.0, -1.0], 10)
    l, r, s = most_active_interval(x, transform="absdiff")
    assert 35 <= l <= 41 and 58 <= r <= 62
    assert r - l < 30

def test_dtw():
    a = np.array([0,1,2,3], dtype=float)
    b = np.array([0,1,2,3], dtype=float)
    assert dtw_distance(a, b, window=1) == 0.0

def test_corr_distance():
    a = np.array([1,2,3,4], dtype=float)
    b = np.array([2,3,4,5], dtype=float)
    d = correlation_distance(a,b)
    assert 0 <= d <= 2

def test_divide_and_conquer_clusters():
    # 9 items, min_cluster_size=3 -> expect multiple clusters
    import math
    series = {f"s{i}": np.sin(np.linspace(0, 2*math.pi, 64) + 0.1*i) for i in range(9)}
    ids = list(series.keys())
    from pulse_cluster.metrics import correlation_distance
    clusters = divide_and_conquer(ids, series, correlation_distance, max_depth=4, min_cluster_size=3)
    assert sum(len(c) for c in clusters) == 9


def test_divide_and_conquer_is_reproducible_with_seed():
    import numpy as np
    from pulse_cluster.divide_conquer import divide_and_conquer

    rng = np.random.default_rng(1)
    series = {f"s{i}": rng.normal(size=50) for i in range(60)}
    dist = lambda a, b: float(np.linalg.norm(a - b))  # noqa: E731
    first = divide_and_conquer(sorted(series), series, dist, min_cluster_size=5, seed=7)
    second = divide_and_conquer(sorted(series), series, dist, min_cluster_size=5, seed=7)
    assert first == second
    assert sorted(s for c in first for s in c) == sorted(series)  # every series lands in exactly one cluster
