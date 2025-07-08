#!/usr/bin/env python3
"""
Test script to verify log anomaly detection consistency.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "logai")))

import pandas as pd
import numpy as np
from logai.applications.log_anomaly_detection import LogAnomalyDetection
from logai.config_interfaces import WorkFlowConfig

def test_consistency():
    """
    Test that identical logs are classified consistently.
    """
    
    # Create test data with duplicate logs
    test_logs = [
        "2024-01-01 10:00:00 ERROR: Database connection failed",
        "2024-01-01 10:01:00 ERROR: Database connection failed",  # Duplicate
        "2024-01-01 10:02:00 INFO: System started",
        "2024-01-01 10:03:00 INFO: System started",  # Duplicate
        "2024-01-01 10:04:00 WARN: High memory usage",
        "2024-01-01 10:05:00 ERROR: Database connection failed",  # Another duplicate
    ]
    
    # Create test DataFrame
    test_df = pd.DataFrame({
        'timestamp': pd.date_range('2024-01-01 10:00:00', periods=len(test_logs), freq='1min'),
        'logline': test_logs
    })
    
    # Save test data
    test_file = 'test_consistency_logs.csv'
    test_df.to_csv(test_file, index=False)
    
    print(f"✅ Created test file: {test_file}")
    print(f"📊 Test data contains {len(test_logs)} logs with {len(set(test_logs))} unique log types")
    
    # TODO: Add actual consistency test with LogAnomalyDetection
    # This would require setting up the proper configuration
    
    print("✅ Consistency test setup complete")

if __name__ == "__main__":
    test_consistency()
