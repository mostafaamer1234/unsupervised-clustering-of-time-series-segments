
from __future__ import annotations
import os
from pathlib import Path
import numpy as np
import pandas as pd
from typing import List, Tuple, Dict

def read_csv_series(path: Path) -> np.ndarray:
    """Read a single-column CSV into a 1D numpy array. Accepts 'value' header or no header."""
    try:
        df = pd.read_csv(path)
        if df.shape[1] == 1:
            arr = df.iloc[:,0].astype(float).values
        else:
            # look for 'value' column
            if 'value' in df.columns:
                arr = df['value'].astype(float).values
            else:
                raise ValueError(f"CSV {path} has {df.shape[1]} columns; expected 1 or a 'value' column.")
    except Exception:
        # try reading without header
        df = pd.read_csv(path, header=None)
        arr = df.iloc[:,0].astype(float).values
    return arr

def load_series_from_dir(data_dir: str | Path, min_len: int = 100) -> Dict[str, np.ndarray]:
    """Recursively load all CSVs from a directory into a dict id->array, filtering by min_len."""
    data_dir = Path(data_dir)
    series = {}
    for p in data_dir.rglob("*.csv"):
        try:
            arr = read_csv_series(p)
            if arr.size >= min_len:
                series[p.stem] = arr.astype(float)
        except Exception as e:
            # ignore unreadable files
            continue
    return series

def zscore(x: np.ndarray, eps: float = 1e-8) -> np.ndarray:
    mu = x.mean()
    sigma = x.std()
    return (x - mu) / (sigma + eps)

def preprocess_all(series: Dict[str, np.ndarray], target_len: int | None = None) -> Dict[str, np.ndarray]:
    """Z-score each series; optionally resample to target_len via simple linear interpolation."""
    out = {}
    for k, arr in series.items():
        arr2 = zscore(arr)
        if target_len is not None and len(arr2) != target_len:
            x = np.linspace(0, 1, len(arr2))
            xi = np.linspace(0, 1, target_len)
            arr2 = np.interp(xi, x, arr2)
        out[k] = arr2
    return out
