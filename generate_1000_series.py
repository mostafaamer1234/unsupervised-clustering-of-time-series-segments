#!/usr/bin/env python3
"""
Generate 1000 synthetic time series segments for testing the PulseDB clustering system.
Creates diverse physiological signal patterns including ECG, PPG, and ABP-like signals.
"""

import numpy as np
import pandas as pd
import os
from pathlib import Path
import random

def generate_ecg_like(t, heart_rate=72, noise_level=0.1):
    """Generate ECG-like signal with P, QRS, T waves"""
    # Heart rate in Hz
    hr_hz = heart_rate / 60.0
    
    # P wave (atrial depolarization)
    p_wave = 0.3 * np.exp(-((t % (1/hr_hz)) - 0.1)**2 / 0.01)
    
    # QRS complex (ventricular depolarization) 
    qrs = 1.0 * np.exp(-((t % (1/hr_hz)) - 0.2)**2 / 0.005)
    
    # T wave (ventricular repolarization)
    t_wave = 0.4 * np.exp(-((t % (1/hr_hz)) - 0.4)**2 / 0.02)
    
    signal = p_wave + qrs + t_wave
    signal += noise_level * np.random.randn(len(t))
    return signal

def generate_ppg_like(t, heart_rate=72, noise_level=0.1):
    """Generate PPG-like signal with systolic and diastolic phases"""
    hr_hz = heart_rate / 60.0
    
    # Systolic phase (sharp rise)
    systole = 0.8 * np.exp(-((t % (1/hr_hz)) - 0.1)**2 / 0.01)
    
    # Diastolic phase (gradual decline)
    diastole = 0.4 * np.exp(-((t % (1/hr_hz)) - 0.3)**2 / 0.05)
    
    # Dicrotic notch
    dicrotic = 0.2 * np.exp(-((t % (1/hr_hz)) - 0.4)**2 / 0.01)
    
    signal = systole + diastole + dicrotic
    signal += noise_level * np.random.randn(len(t))
    return signal

def generate_abp_like(t, heart_rate=72, noise_level=0.1):
    """Generate ABP-like signal with systolic and diastolic pressures"""
    hr_hz = heart_rate / 60.0
    
    # Systolic pressure (peak)
    systolic = 1.0 * np.exp(-((t % (1/hr_hz)) - 0.1)**2 / 0.008)
    
    # Diastolic pressure (baseline)
    diastolic = 0.3 * np.exp(-((t % (1/hr_hz)) - 0.5)**2 / 0.1)
    
    # Dicrotic notch
    dicrotic = 0.4 * np.exp(-((t % (1/hr_hz)) - 0.2)**2 / 0.005)
    
    signal = systolic + diastolic + dicrotic
    signal += noise_level * np.random.randn(len(t))
    return signal

def generate_arhythmia(t, heart_rate=72, noise_level=0.1):
    """Generate arrhythmic pattern with irregular intervals"""
    # Variable heart rate
    hr_variations = heart_rate + 20 * np.sin(0.1 * t) + 10 * np.random.randn(len(t))
    hr_hz = hr_variations / 60.0
    
    # Irregular intervals
    intervals = np.cumsum(1.0 / hr_hz)
    
    signal = np.zeros_like(t)
    for i, interval in enumerate(intervals):
        if i < len(intervals) - 1:
            # Create beat at this interval
            beat_time = interval
            if beat_time < len(t):
                # QRS-like complex
                qrs = 1.0 * np.exp(-((t - beat_time)**2) / 0.01)
                signal += qrs
    
    signal += noise_level * np.random.randn(len(t))
    return signal

def generate_stress_pattern(t, heart_rate=90, noise_level=0.15):
    """Generate stress-like pattern with elevated heart rate and variability"""
    # Elevated and variable heart rate
    hr_hz = (heart_rate + 15 * np.sin(0.2 * t) + 5 * np.random.randn(len(t))) / 60.0
    
    # More pronounced P wave (sympathetic activation)
    p_wave = 0.5 * np.exp(-((t % (1/hr_hz)) - 0.1)**2 / 0.008)
    
    # Taller QRS
    qrs = 1.2 * np.exp(-((t % (1/hr_hz)) - 0.2)**2 / 0.004)
    
    # Inverted T wave (stress indicator)
    t_wave = -0.3 * np.exp(-((t % (1/hr_hz)) - 0.4)**2 / 0.02)
    
    signal = p_wave + qrs + t_wave
    signal += noise_level * np.random.randn(len(t))
    return signal

def main():
    """Generate 1000 diverse time series segments"""
    # Set random seed for reproducibility
    random.seed(42)
    np.random.seed(42)
    
    # Create data directory
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # Time vector for 10-second segments at 256 Hz
    t = np.linspace(0, 10, 256)
    
    # Generate 1000 segments with different patterns
    patterns = [
        ("ECG", generate_ecg_like),
        ("PPG", generate_ppg_like), 
        ("ABP", generate_abp_like),
        ("ARR", generate_arhythmia),
        ("STR", generate_stress_pattern)
    ]
    
    print("Generating 1000 time series segments...")
    
    for i in range(1000):
        # Randomly select pattern type
        pattern_name, pattern_func = random.choice(patterns)
        
        # Random parameters
        heart_rate = random.uniform(60, 100)
        noise_level = random.uniform(0.05, 0.2)
        
        # Generate signal
        signal = pattern_func(t, heart_rate, noise_level)
        
        # Add some random variations
        if random.random() < 0.3:  # 30% chance of additional variation
            # Add baseline drift
            drift = 0.1 * np.sin(0.5 * t + random.uniform(0, 2*np.pi))
            signal += drift
            
        if random.random() < 0.2:  # 20% chance of artifacts
            # Add artifact spikes
            spike_times = random.sample(range(50, 200), random.randint(1, 3))
            for spike_time in spike_times:
                signal[spike_time] += random.uniform(0.5, 2.0)
        
        # Create filename
        filename = f"{pattern_name}_{i:04d}.csv"
        filepath = data_dir / filename
        
        # Save as CSV
        df = pd.DataFrame({"value": signal})
        df.to_csv(filepath, index=False)
        
        if (i + 1) % 100 == 0:
            print(f"Generated {i + 1}/1000 segments...")
    
    print(f"Successfully generated 1000 time series segments in {data_dir}/")
    print("Pattern distribution:")
    for pattern_name, _ in patterns:
        count = len(list(data_dir.glob(f"{pattern_name}_*.csv")))
        print(f"  {pattern_name}: {count} segments")

if __name__ == "__main__":
    main()
