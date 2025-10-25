#!/usr/bin/env python3
"""
Easy-to-use script for running the PulseDB analysis pipeline.
This script handles the PYTHONPATH setup automatically.
"""

import sys
import os
import subprocess
from pathlib import Path

def main():
    """Run the PulseDB analysis with proper environment setup"""
    
    # Add current directory to Python path
    current_dir = Path(__file__).parent.absolute()
    python_path = os.environ.get('PYTHONPATH', '')
    if python_path:
        os.environ['PYTHONPATH'] = f"{current_dir}:{python_path}"
    else:
        os.environ['PYTHONPATH'] = str(current_dir)
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Run PulseDB Time-Series Clustering Analysis')
    parser.add_argument('--data_dir', type=str, default='data', 
                       help='Directory containing CSV files (default: data)')
    parser.add_argument('--out_dir', type=str, default='reports', 
                       help='Output directory for results (default: reports)')
    parser.add_argument('--metric', type=str, choices=['correlation', 'dtw'], 
                       default='correlation', help='Distance metric to use')
    parser.add_argument('--max_depth', type=int, default=6, 
                       help='Maximum clustering depth (default: 6)')
    parser.add_argument('--min_cluster_size', type=int, default=20, 
                       help='Minimum cluster size (default: 20)')
    parser.add_argument('--target_len', type=int, default=256, 
                       help='Target series length (default: 256)')
    parser.add_argument('--dtw_window', type=float, default=0.1, 
                       help='DTW window fraction (default: 0.1)')
    parser.add_argument('--generate_data', action='store_true', 
                       help='Generate 1000 synthetic time series first')
    parser.add_argument('--verify', action='store_true', 
                       help='Run algorithm verification tests')
    
    args = parser.parse_args()
    
    print("PulseDB Time-Series Clustering Analysis")
    print("=" * 50)
    
    # Generate data if requested
    if args.generate_data:
        print("Generating 1000 synthetic time series...")
        subprocess.run([sys.executable, 'generate_1000_series.py'], cwd=current_dir)
        print("Data generation complete!")
        print()
    
    # Run verification if requested
    if args.verify:
        print("Running algorithm verification...")
        subprocess.run([sys.executable, 'verify_algorithms.py'], cwd=current_dir)
        print("Verification complete!")
        print()
    
    # Run the main analysis
    print(f"Running analysis with parameters:")
    print(f"  - Data directory: {args.data_dir}")
    print(f"  - Output directory: {args.out_dir}")
    print(f"  - Distance metric: {args.metric}")
    print(f"  - Max depth: {args.max_depth}")
    print(f"  - Min cluster size: {args.min_cluster_size}")
    print()
    
    cmd = [
        sys.executable, 'examples/run_pipeline.py',
        '--data_dir', args.data_dir,
        '--out_dir', args.out_dir,
        '--metric', args.metric,
        '--max_depth', str(args.max_depth),
        '--min_cluster_size', str(args.min_cluster_size),
        '--target_len', str(args.target_len)
    ]
    
    if args.metric == 'dtw':
        cmd.extend(['--dtw_window', str(args.dtw_window)])
    
    try:
        subprocess.run(cmd, cwd=current_dir, check=True)
        print("Analysis completed successfully!")
        print(f"Results saved to: {args.out_dir}/")
        print(f"Check {args.out_dir}/SUMMARY.md for a quick overview")
        
        # Generate comprehensive report if we have results
        if Path(args.out_dir).exists() and (Path(args.out_dir) / "clusters.json").exists():
            print("Generating comprehensive report...")
            subprocess.run([sys.executable, 'generate_final_report.py'], cwd=current_dir)
            print(f"Comprehensive report saved to: {args.out_dir}/FINAL_REPORT.md")
        
    except subprocess.CalledProcessError as e:
        print(f"Error running analysis: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("Error: Could not find the analysis script. Make sure you're in the project directory.")
        sys.exit(1)

if __name__ == "__main__":
    main()
