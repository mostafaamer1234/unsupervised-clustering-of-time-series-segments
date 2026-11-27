"""Export data for the static site.

site/data.json     example segments, spectra and intervals for the about page
site/library.json  every preprocessed segment (the analyzer's reference library), plus the
                   leave-one-out accuracy of the analyzer's nearest-neighbour signal-type guess

    python export_site_data.py
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from pulse_cluster.io import load_series_from_dir, preprocess_all
from pulse_cluster.kadane import most_active_interval

PER_FAMILY = 8
K_NEIGHBOURS = 5


def main() -> None:
    series = preprocess_all(load_series_from_dir("data", min_len=50), target_len=256)
    fams: dict[str, list[str]] = defaultdict(list)
    for sid in sorted(series):
        fams[sid.split("_")[0]].append(sid)
    rng = np.random.default_rng(0)
    out = {}
    for fam, ids in fams.items():
        picks = sorted(rng.choice(ids, PER_FAMILY, replace=False).tolist())
        items = []
        for sid in picks:
            x = series[sid]
            spec = np.abs(np.fft.rfft(x))[1:65]
            l, r, _ = most_active_interval(x)
            items.append({"id": sid, "x": np.round(x, 3).tolist(), "spec": np.round(spec / spec.max(), 4).tolist(), "l": int(l), "r": int(r)})
        out[fam] = items
    Path("site").mkdir(exist_ok=True)
    Path("site/data.json").write_text(json.dumps(out))
    print({k: len(v) for k, v in out.items()})

    ids = sorted(series)
    X = np.array([series[i] for i in ids])
    # Signal type is guessed from the autocorrelation (lags 0-127), which ignores where in the beat
    # a segment starts. Leave-one-out over the library picked it over the raw spectrum (85% vs 81%).
    A = np.array([np.correlate(x, x, "full")[len(x) - 1 : len(x) - 1 + 128] / len(x) for x in X])
    A = A - A.mean(axis=1, keepdims=True)
    A /= np.linalg.norm(A, axis=1, keepdims=True)
    dist = 1 - np.einsum("ij,kj->ik", A, A)  # correlation distance, as in pulse_cluster.metrics
    np.fill_diagonal(dist, np.inf)
    fam = np.array([i.split("_")[0] for i in ids])
    nn = np.argsort(dist, axis=1)[:, :K_NEIGHBOURS]
    votes = np.array([Counter(f).most_common(1)[0][0] for f in fam[nn]])
    acc = float(np.mean(votes == fam))
    per_family = {f: round(float(np.mean(votes[fam == f] == f)), 3) for f in sorted(set(fam))}
    Path("site/library.json").write_text(json.dumps({"ids": ids, "x": np.round(X, 2).tolist(), "k": K_NEIGHBOURS, "loo_accuracy": round(acc, 4), "per_family": per_family}, separators=(",", ":")))
    print(len(ids), "library segments, leave-one-out accuracy", round(acc, 4))


if __name__ == "__main__":
    main()
