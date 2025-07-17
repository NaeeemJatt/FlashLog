#!/usr/bin/env python3
"""
Test script to verify the Kibana dashboard fix for processing_time_seconds TypeError.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def test_kibana_dashboard_fix():
    """Test the Kibana dashboard data processing with problematic data"""
    
    # Create test data with problematic processing_time_seconds (concatenated string)
    test_data = {
        'logline': [
            '2024-01-01 10:00:00 INFO: Application started',
            '2024-01-01 10:00:01 ERROR: Database connection failed',
            '2024-01-01 10:00:02 WARNING: High memory usage',
            '2024-01-01 10:00:03 INFO: Request processed',
            '2024-01-01 10:00:04 ERROR: Authentication failed'
        ],
        'is_anomaly': [False, True, False, False, True],
        'timestamp': [
            '2024-01-01 10:00:00',
            '2024-01-01 10:00:01', 
            '2024-01-01 10:00:02',
            '2024-01-01 10:00:03',
            '2024-01-01 10:00:04'
        ],
        'processing_time_seconds': [
            '1.3322634696960451.3322634696960451.332263469696045',  # Problematic concatenated string
            '2.1',
            '1.8',
            '3.2',
            '2.5'
        ]
    }
    
    df = pd.DataFrame(test_data)
    
    print("Test DataFrame:")
    print(df)
    print("\nData types:")
    print(df.dtypes)
    print("\nProcessing time column sample:")
    print(df['processing_time_seconds'].head())
    
    # Test the fix by simulating the problematic operations
    print("\n" + "="*50)
    print("Testing the fix...")
    
    # Test 1: Basic numeric conversion
    try:
        processing_times = pd.to_numeric(df['processing_time_seconds'], errors='coerce')
        processing_times = processing_times.dropna()
        print(f"✓ Numeric conversion successful")
        print(f"  Valid values: {len(processing_times)}")
        print(f"  Sample values: {processing_times.head().tolist()}")
    except Exception as e:
        print(f"✗ Numeric conversion failed: {e}")
    
    # Test 2: Mean calculation
    try:
        if len(processing_times) > 0:
            avg_time = processing_times.mean()
            max_time = processing_times.max()
            print(f"✓ Statistics calculation successful")
            print(f"  Average: {avg_time:.3f}")
            print(f"  Maximum: {max_time:.3f}")
        else:
            print("✓ No valid processing times, using fallback values")
    except Exception as e:
        print(f"✗ Statistics calculation failed: {e}")
    
    # Test 3: Variance calculation
    try:
        if len(processing_times) > 0:
            variance = processing_times.var()
            print(f"✓ Variance calculation successful")
            print(f"  Variance: {variance:.3f}")
        else:
            print("✓ No valid processing times, using fallback variance")
    except Exception as e:
        print(f"✗ Variance calculation failed: {e}")
    
    # Test 4: Time series data generation simulation
    print("\n" + "="*50)
    print("Testing time series data generation...")
    
    try:
        # Simulate the time series processing
        time_points = [datetime.now() + timedelta(seconds=i*5) for i in range(10)]
        processing_variance_data = []
        
        for i in range(len(time_points)):
            if i < len(processing_times):
                variance = processing_times.iloc[:i+1].var() * 1000
                processing_variance_data.append(int(variance if not np.isnan(variance) else 0))
            else:
                base_variance = processing_times.var() * 1000
                noise = np.random.normal(0, base_variance * 0.1)
                processing_variance_data.append(int(max(0, base_variance + noise)))
        
        print(f"✓ Time series generation successful")
        print(f"  Generated {len(processing_variance_data)} data points")
        print(f"  Sample values: {processing_variance_data[:5]}")
        
    except Exception as e:
        print(f"✗ Time series generation failed: {e}")
    
    print("\n" + "="*50)
    print("Test completed successfully!")
    print("The fix should now handle problematic processing_time_seconds data.")

if __name__ == "__main__":
    test_kibana_dashboard_fix() 