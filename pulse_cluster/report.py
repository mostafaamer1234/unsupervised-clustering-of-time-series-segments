
from __future__ import annotations
from typing import Dict, List, Callable, Tuple
from pathlib import Path
import json
import numpy as np
import matplotlib.pyplot as plt

from .kadane import most_active_interval

def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)

def plot_series(out_dir: Path, sid: str, x: np.ndarray, annotate_kadane: bool = True):
    ensure_dir(out_dir)
    plt.figure()
    plt.plot(x)
    if annotate_kadane:
        l, r, s = most_active_interval(x)
        # We'll annotate using default styles (no custom colors)
        plt.axvspan(l, r, alpha=0.2)
        plt.title(f"{sid} | max-activity [{l},{r}) score={s:.3f}")
    else:
        plt.title(sid)
    plt.xlabel("sample")
    plt.ylabel("z-scored value")
    fpath = out_dir / f"{sid}.png"
    plt.savefig(fpath, dpi=150, bbox_inches="tight")
    plt.close()
    return str(fpath)

def write_json(obj, path: Path):
    path.write_text(json.dumps(obj, indent=2))

def write_markdown(text: str, path: Path):
    path.write_text(text)

def summarize_clusters(clusters: List[List[str]], series: Dict[str, np.ndarray]) -> List[dict]:
    out = []
    for idx, ids in enumerate(clusters):
        lengths = [len(series[sid]) for sid in ids]
        out.append({
            "cluster_id": f"c{idx}",
            "size": len(ids),
            "median_len": int(np.median(lengths))
        })
    return out
