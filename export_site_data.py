"""Export example segments, spectra and intervals for the static site (site/data.json).

    python export_site_data.py
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import numpy as np

from pulse_cluster.io import load_series_from_dir, preprocess_all
from pulse_cluster.kadane import most_active_interval

PER_FAMILY = 8


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


if __name__ == "__main__":
    main()
