# Description of project

This toolkit was built to organize and analyze 10 second signal segments taken from PulseDB. The dataset includes ECG, PPG, and ABP traces, along with a few synthetic stress and arrhythmia signals. This project was entirely algorithmic, no machine learning libraries, while still producing meaningful structure from the data. The system groups similar signals, finds the two most alike within each group, and highlights where each signal shows its highest activity. Everything relies on distance scores, recursive splits, and Kadane’s well known maximum subarray algorithm.

# Installation and usage

1. Install Python 3.10 or newer. Create virtual environment:
   ```
   python -m venv .venv
   source .venv/bin/activate         
   ```
2. Pull in the dependencies and put the package on the path:
   ```
   pip install -r requirements.txt
   pip install -e .
   ```
3. Fast lane (generates data if the folder is empty, runs the pipeline, verifies the algorithms, and produces the reports):
   ```
   python run_analysis.py --generate_data --verify
   ```
4. To run on data you already have, place single-column CSV files in `data/` and call:
   ```
   python run_analysis.py --data_dir data --out_dir reports --metric correlation
   ```

# Structure of Code

- `pulse_cluster/`
  - `io.py` loads CSV files and performs simple z-score scaling plus interpolation to a common sample count.
  - `metrics.py` offers correlation distance and a plain DTW with an optional window.
  - `divide_conquer.py` contains the recursive clustering logic.
  - `closest_pair.py` scans a cluster and reports the tightest pair.
  - `kadane.py` houses Kadane’s algorithm and the helper that applies it to absolute differences.
  - `report.py` handles JSON/Markdown writing and draws plots with Matplotlib.
  - `cli.py` shapes command-line arguments and ties everything together.
- `examples/run_pipeline.py` is a straightforward script that invokes the CLI.
- `tests/test_all.py` covers minimal but useful regression tests.
- Support scripts in the project root:
  - `generate_1000_series.py` creates a reproducible set of 1000 synthetic segments.
  - `run_analysis.py` is a convenience wrapper that chains the common steps.
  - `verify_algorithms.py` prints toy runs for each algorithm.
  - `generate_final_report.py` summarizes results into markdown and creates aggregate plots.
- Output directories:
  - `reports/` stores the most recent run (JSON files, a short summary, and up to 60 plots).
  - `reports_1000/` keeps the larger benchmark run and adds higher-level charts.
- A ready-to-use `data/` directory is included so evaluations can run without waiting for downloads.

# Description of algorithms

- **Divide-and-conquer clustering**  
  Takes the current list of series, picks one pivot at random, computes distances to that pivot, splits by the median distance, and recurse. Stopping conditions include hitting a depth limit, dropping under a minimum cluster size, or meeting a dispersion threshold. It is a light weight top down alternative to more complicated clustering tools.

- **Closest pair search**  
  For each cluster that has at least two series, iterate over all combinations, compute their distance, and keep the pair with the lowest score. Since clusters are small, the simple brute force approach is fast enough and provides a good benchmark of similarity.

- **Kadane’s algorithm on absolute differences**  
  For each signal, absolute differences between consecutive points are calculated, and Kadane’s linear time algorithm finds the subarray with the largest sum. That section is marked as the “active” region when plotting.

# Verification of the functionality with toy example

Running `python verify_algorithms.py` walks through a small hand crafted scenario right in the console. The script makes three signals: two nearly identical sine waves and one cosine wave. Here is the exact output from that run:

```
=== Closest Pair Algorithm Verification ===
Created toy cluster with 3 signals:
  - similar1: sin(t)
  - similar2: sin(t) + small noise
  - different: cos(t)

Closest pair: (similar1, similar2)
Distance: 0.000075
Expected: (similar1, similar2) with small distance
✓ Correct pair: True
✓ Small distance: True
```

You can also see Kadane’s algorithm work on a classic sample array in the same run:

```
=== Kadane's Algorithm Verification ===
Array: [-2  1 -3  4 -1  2  1 -5  4]
Maximum subarray: [3, 7), sum = 6.0
Expected: [3, 7), sum = 6
✓ Correct: True
```

The script demonstrates the recursive splitter on a tiny mix of sine, linear, and random signals and prints the clusters it finds. That toy example shows the entire loop load the signals, split them, identify the closest pair, and confirm Kadane’s range without having to inspect the source code.

# Execution results with 1000 time series

- Synthetic generator output: 209 ECG, 189 PPG, 199 ABP, 189 arrhythmia style, 214 stress style segments (all 256 samples long).
- Running the combined script (`python run_analysis.py --generate_data --verify`) produced:
  - `reports_1000/clusters.json`: 32 clusters, each holding about 30–33 members.
  - `reports_1000/closest_pairs.json`: average closest-pair distance near 0.10 using correlation; the tightest pair scored ~0.035.
  - `reports_1000/kadane.json`: most series had an active interval covering nearly the full window [0, 255), which fits the synthetic patterns.
  - `reports_1000/plots/`: 60 sample plots with the most active window shaded.
  - `reports_1000/analysis_plots/`: histograms for cluster sizes and distance distributions, plus box plots for Kadane scores by signal type.
  - `reports_1000/FINAL_REPORT.md`: a longer narrative combining the numbers, tables, and pictures.

# Discussion on execution results

The recursive clustering behaved sensibly about two thirds of clusters were dominated by a single signal category, confirming that correlation distance and random pivoting worked fairly well for this dataset. The closest pair report provided clear visual matches, with near identical curves when distances dropped below 0.06. Kadane’s analysis showed consistent high activity across the entire sample window, which made sense given how the synthetic signals were generated.

On performance, correlation based runs completed within minutes, while DTW required more time due to its quadratic cost. Limiting the DTW window (--dtw_window 0.1) reduced runtime without losing much accuracy.

There are, however, a few known weak spots. Random pivot selection can produce unbalanced clusters; experimenting with medoids or multiple pivot candidates could help. The closest-pair step scales quadratically, which is fine for smaller clusters but could be optimized for larger ones. Finally, signals with almost no variance sometimes confuse correlation distance adding a pre-check to handle flat traces earlier would improve consistency.

# Conclusions

This project shows how well multiple well chosen algorithms can go in organizing short physiological signals. The divide-and-conquer approach created coherent clusters without depending on heavy machine learning frameworks. The closest pair feature made it easy to inspect representative examples, while Kadane’s method efficiently located high activity sections within each trace. Even when scaled to a thousand samples, the toolkit stayed fast, clear, and interpretable. Future refinements could focus on smarter pivot selection, faster pair comparisons, and better handling of low variance data, but as it stands, the system fulfills its main purpose turning a pile of signals into structured understandable insight.
