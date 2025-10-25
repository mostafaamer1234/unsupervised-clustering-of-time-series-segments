# Report: Time-Series Clustering and Segment Analysis on PulseDB (Divide-and-Conquer)

## Description of Project
This system clusters 10-second PulseDB segments (ECG/PPG/ABP) using **divide-and-conquer** partitioning with either correlation or DTW distances.  
Within each cluster it finds the **closest pair**, and for each segment it uses **Kadane’s algorithm** on absolute first differences to locate the most active sub-interval.  
The emphasis is on **algorithmic design**, not black-box ML.

## Installation and Usage
- Install: `pip install -r requirements.txt`
- Prepare data as CSV files (one column of values) in `data/`
- Run: `python examples/run_pipeline.py --data_dir data --out_dir reports --metric correlation`
- Outputs: `clusters.json`, `closest_pairs.json`, `kadane.json`, and plots in `reports/plots/`

## Structure of Code
- `io.py`: loading & z-scoring; optional length-harmonization via linear interpolation
- `metrics.py`: correlation distance; DTW with optional Sakoe–Chiba window
- `divide_conquer.py`: recursive top-down split by median distance to a pivot
- `closest_pair.py`: in-cluster closest pair (brute force)
- `kadane.py`: maximum subarray; most active interval on |Δx|
- `report.py`: JSON/MD writers; per-series plots with interval annotation
- `examples/run_pipeline.py`: CLI entry

## Description of Algorithms
- **Divide-and-Conquer Clustering**: pick a pivot in a set S, compute distances d(·,pivot), split at median into L/R, recurse until stop rules (min size / max depth / dispersion threshold).  
- **Closest Pair**: exhaustive pairwise distance in each cluster; reports argmin.  
- **Kadane (Max Subarray)**: linear-time scan on transformed sequence y = |Δx| (or (Δx)²) to obtain the most active interval per segment.

## Verification with Toy Examples
- Unit tests (`pytest`) verify Kadane on a known array, DTW identity on identical series, correlation distance bounds, and the clustering partition size invariants.

## Execution Results with 1000 Time Series
- After running on your PulseDB subset, include:
  - Number of clusters & size distribution (`clusters.json`)
  - Closest pair distances per cluster (`closest_pairs.json`)
  - Histogram/stats of interval lengths from Kadane (`kadane.json`)
  - Sample plots under `reports/plots/`

## Discussion of Results
- Interpret whether clusters align with known physiology (e.g., ABP vs PPG morphologies, arrhythmia signatures).
- Use closest-pair distances as a cohesion proxy; lower is tighter.
- Analyze whether Kadane intervals co-occur within clusters (shared peak activity).

## Conclusions
- Divide-and-conquer provides interpretable, parameter-light structure for PulseDB segments.
- Closest-pair and Kadane enrich cluster reasoning and exemplar selection.
- Limitations: DTW O(n²) cost; brute-force closest-pair O(k²) per cluster; sensitivity to preprocessing.
- Future work: faster DTW (lower bounds + pruning), balanced pivoting, multi-resolution segmentation, multivariate fusion.
