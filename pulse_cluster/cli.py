
from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
from typing import Dict, List
from .io import load_series_from_dir, preprocess_all
from .metrics import correlation_distance, dtw_distance
from .divide_conquer import divide_and_conquer
from .closest_pair import closest_pair
from .kadane import most_active_interval
from .report import plot_series, write_json, write_markdown, summarize_clusters
import math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data_dir", type=str, default="data")
    ap.add_argument("--out_dir", type=str, default="reports")
    ap.add_argument("--metric", type=str, choices=["correlation","dtw"], default="correlation")
    ap.add_argument("--dtw_window", type=float, default=0.1, help="fraction of series length (for DTW)")
    ap.add_argument("--target_len", type=int, default=256)
    ap.add_argument("--max_depth", type=int, default=6)
    ap.add_argument("--min_cluster_size", type=int, default=20)
    ap.add_argument("--max_dispersion", type=float, default=None)
    args = ap.parse_args()

    out_dir = Path(args.out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    plots_dir = out_dir / "plots"; plots_dir.mkdir(parents=True, exist_ok=True)

    raw = load_series_from_dir(args.data_dir, min_len=50)
    if not raw:
        # Generate synthetic demo: 3 archetypes + noise, 100 segments
        import random
        random.seed(7); np.random.seed(7)
        n = 100
        L = args.target_len
        archetypes = []
        t = np.linspace(0, 2*np.pi, L)
        archetypes.append(np.sin(t))
        archetypes.append(np.sign(np.sin(3*t))*0.5 + 0.2*np.sin(7*t))
        ramp = np.linspace(-1, 1, L)
        archetypes.append(ramp + 0.1*np.sin(5*t))
        raw = {}
        for i in range(n):
            base = archetypes[i % 3]
            noisy = base + 0.15*np.random.randn(L)
            raw[f"synth_{i:04d}"] = noisy

    series = preprocess_all(raw, target_len=args.target_len)

    if args.metric == "correlation":
        dist_fn = correlation_distance
    else:
        win = max(1, int(args.dtw_window * args.target_len))
        dist_fn = lambda a,b: dtw_distance(a,b,window=win)

    ids = list(series.keys())
    clusters = divide_and_conquer(ids, series, dist_fn,
                                  max_depth=args.max_depth,
                                  min_cluster_size=args.min_cluster_size,
                                  max_dispersion=args.max_dispersion)

    # Closest pairs per cluster and Kadane intervals per series
    closest = {}
    for c_idx, cid_list in enumerate(clusters):
        if len(cid_list) >= 2:
            pair, d = closest_pair(cid_list, series, dist_fn)
            closest[f"c{c_idx}"] = {"pair": pair, "distance": float(d)}
        else:
            closest[f"c{c_idx}"] = {"pair": None, "distance": None}

    kadane_map = {}
    for sid, x in series.items():
        l, r, s = most_active_interval(x, transform="absdiff")
        kadane_map[sid] = {"l": int(l), "r": int(r), "score": float(s)}

    # Write reports
    write_json({"clusters": clusters, "summary": summarize_clusters(clusters, series)}, Path(args.out_dir) / "clusters.json")
    write_json(closest, Path(args.out_dir) / "closest_pairs.json")
    write_json(kadane_map, Path(args.out_dir) / "kadane.json")

    # Plots (one per series, annotated with its max-activity interval)
    count = 0
    for sid, x in series.items():
        plot_series(plots_dir, sid, x, annotate_kadane=True)
        count += 1
        if count >= 60:  # avoid too many images by default
            break

    # Markdown summary
    md = ["# Run Summary",
          f"- total series: **{len(series)}**",
          f"- clusters formed: **{len(clusters)}**",
          "- closest-pair computed per cluster",
          "- Kadane intervals saved to `kadane.json`",
          f"- Example plots saved under `{plots_dir}` (first {count} series)\n"]
    write_markdown("\n".join(md), Path(args.out_dir) / "SUMMARY.md")

if __name__ == "__main__":
    main()
