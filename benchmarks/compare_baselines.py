"""Score the divide-and-conquer clustering against standard baselines.

The five signal families in data/ (ABP, ARR, ECG, PPG, STR) are encoded in the
file names, which gives ground truth for external validity metrics:

  * ARI  - adjusted Rand index (0 = chance, 1 = perfect)
  * NMI  - normalized mutual information
  * purity - share of series whose cluster's majority family matches their own

    python benchmarks/compare_baselines.py
"""

from __future__ import annotations

import time
from collections import Counter
from pathlib import Path

import numpy as np
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score

from pulse_cluster.divide_conquer import divide_and_conquer
from pulse_cluster.io import load_series_from_dir, preprocess_all
from pulse_cluster.metrics import correlation_distance

DATA = Path(__file__).resolve().parent.parent / "data"


def spectrum(x: np.ndarray, bins: int = 64) -> np.ndarray:
    """Phase-invariant representation: log magnitude of the low-frequency FFT bins."""
    mag = np.abs(np.fft.rfft(x))[1 : bins + 1]
    return np.log1p(mag / (mag.sum() + 1e-12) * bins)


def purity(labels_true: list[str], labels_pred: list[int]) -> float:
    total = 0
    for cluster in set(labels_pred):
        members = [t for t, p in zip(labels_true, labels_pred) if p == cluster]
        total += Counter(members).most_common(1)[0][1]
    return total / len(labels_true)


def evaluate(name: str, truth: list[str], pred: list[int], seconds: float) -> dict:
    return {
        "method": name,
        "clusters": len(set(pred)),
        "ARI": adjusted_rand_score(truth, pred),
        "NMI": normalized_mutual_info_score(truth, pred),
        "purity": purity(truth, pred),
        "seconds": seconds,
    }


def main() -> None:
    series = preprocess_all(load_series_from_dir(DATA))
    ids = sorted(series)
    truth = [sid.split("_")[0] for sid in ids]
    X = np.stack([series[i] for i in ids])
    k = len(set(truth))
    rows = []

    t = time.perf_counter()
    clusters = divide_and_conquer(ids, series, correlation_distance, max_depth=6, min_cluster_size=20, seed=0)
    label_of = {sid: c for c, members in enumerate(clusters) for sid in members}
    rows.append(evaluate("Divide-and-conquer (this repo, correlation distance)", truth, [label_of[i] for i in ids], time.perf_counter() - t))

    t = time.perf_counter()
    rows.append(evaluate(f"k-means, k={k} (z-normalized Euclidean)", truth, KMeans(k, n_init=10, random_state=0).fit_predict(X).tolist(), time.perf_counter() - t))

    t = time.perf_counter()
    corr = 1 - np.corrcoef(X)
    agg = AgglomerativeClustering(n_clusters=k, metric="precomputed", linkage="average").fit_predict(corr)
    rows.append(evaluate(f"Agglomerative, k={k} (correlation distance, average linkage)", truth, agg.tolist(), time.perf_counter() - t))

    t = time.perf_counter()
    S = np.stack([spectrum(x) for x in X])
    rows.append(evaluate(f"k-means, k={k} on FFT magnitude spectrum (phase-invariant)", truth, KMeans(k, n_init=10, random_state=0).fit_predict(S).tolist(), time.perf_counter() - t))

    t = time.perf_counter()
    spec = {sid: s_ for sid, s_ in zip(ids, S)}
    euclid = lambda a, b: float(np.linalg.norm(a - b))  # noqa: E731
    clusters = divide_and_conquer(ids, spec, euclid, max_depth=6, min_cluster_size=20, seed=0)
    label_of = {sid: c for c, members in enumerate(clusters) for sid in members}
    rows.append(evaluate("Divide-and-conquer on FFT spectrum", truth, [label_of[i] for i in ids], time.perf_counter() - t))

    print(f"{len(ids)} series, {k} signal families\n")
    print("| Method | Clusters | ARI | NMI | Purity | Time |\n|---|---|---|---|---|---|")
    for r in rows:
        print(f"| {r['method']} | {r['clusters']} | {r['ARI']:.3f} | {r['NMI']:.3f} | {r['purity']:.1%} | {r['seconds']:.1f}s |")


if __name__ == "__main__":
    main()
