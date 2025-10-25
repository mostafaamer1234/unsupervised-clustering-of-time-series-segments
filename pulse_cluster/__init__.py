"""
PulseDB Time-Series Clustering via Divide-and-Conquer

This package implements algorithmic (non-ML) clustering and analysis of PulseDB 
10-second physiological signal segments (ECG/PPG/ABP) using divide-and-conquer 
strategies, closest-pair algorithms, and Kadane's algorithm.
"""

__version__ = "1.0.0"
__author__ = "PulseDB Analysis Team"

from .divide_conquer import divide_and_conquer
from .closest_pair import closest_pair
from .kadane import kadane_max_subarray, most_active_interval
from .metrics import correlation_distance, dtw_distance
from .io import load_series_from_dir, preprocess_all
from .report import plot_series, write_json, write_markdown, summarize_clusters
from .cli import main

__all__ = [
    "divide_and_conquer",
    "closest_pair", 
    "kadane_max_subarray",
    "most_active_interval",
    "correlation_distance",
    "dtw_distance",
    "load_series_from_dir",
    "preprocess_all",
    "plot_series",
    "write_json",
    "write_markdown", 
    "summarize_clusters",
    "main"
]
