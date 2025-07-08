#!/usr/bin/env python3
"""
Final test to verify the complete normalization solution works with actual anomaly detection.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "logai")))

import pandas as pd
from logai.applications.log_anomaly_detection import LogAnomalyDetection
from logai.config_interfaces import WorkFlowConfig
from logai.dataloader.data_model import LogRecordObject
from logai.utils import constants

def test_final_solution():
    """Test the complete solution with actual anomaly detection."""
    
    print("🧪 Testing Complete Solution with Actual Anomaly Detection")
    print("=" * 80)
    
    # Create test logs with the problematic case
    test_logs = [
        "ciod: failed to read message prefix on control stream (CioStream socket to 172.16.96.116:33569",
        "ciod: failed to read message prefix on control stream (CioStream socket to 172.16.96.116:33370",
        "ciod: failed to read message prefix on control stream (CioStream socket to 192.168.1.1:8080",
        "ciod: failed to read message prefix on control stream (CioStream socket to 10.0.0.1:443",
        "2024-01-01 10:00:00 ERROR: Database connection failed to 192.168.1.1:5432",
        "2024-01-01 10:01:00 ERROR: Database connection failed to 192.168.1.2:5432",
        "2024-01-01 10:02:00 ERROR: Database connection failed to 192.168.1.3:5432",
        "Process 12345 crashed with error code 404",
        "Process 67890 crashed with error code 500",
        "Process 11111 crashed with error code 404",
    ]
    
    # Create timestamps
    timestamps = pd.date_range('2024-01-01', periods=len(test_logs), freq='1min')
    
    # Create LogRecordObject
    logrecord = LogRecordObject(
        body=pd.DataFrame({
            constants.LOGLINE_NAME: test_logs,
            constants.LOG_TIMESTAMPS: timestamps
        }),
        timestamp=pd.DataFrame({
            constants.LOG_TIMESTAMPS: timestamps
        }),
        attributes=pd.DataFrame({
            'attribute1': ['value1'] * len(test_logs),
            'attribute2': ['value2'] * len(test_logs)
        })
    )
    
    # Create configuration
    config = WorkFlowConfig(
        data_loader_config=None,  # We'll use the logrecord directly
        open_set_data_loader_config=None,
        preprocessor_config=None,
        log_parser_config={
            "algo_name": "ael",
            "algo_params": {
                "max_dist": 0.1,
                "delimeter": " ",
                "min_len": 2,
                "max_len": 200,
            }
        },
        log_vectorizer_config={
            "algo_name": "tfidf",
            "algo_params": {
                "max_features": 100,
                "min_df": 1,
                "max_df": 1.0,
            }
        },
        feature_extractor_config={
            "algo_name": "counter",
            "algo_params": {
                "window_size": 60,
                "step_size": 60,
            }
        },
        anomaly_detection_config={
            "algo_name": "one_class_svm",
            "algo_params": {
                "nu": 0.1,
                "kernel": "rbf",
                "gamma": "scale",
            }
        }
    )
    
    # Create anomaly detection instance
    anomaly_detector = LogAnomalyDetection(config)
    
    # Manually set the logrecord
    anomaly_detector._logrecord = logrecord
    
    print(f"📊 Test setup:")
    print(f"  Total logs: {len(test_logs)}")
    print(f"  Unique log patterns expected: 4 (3 different types)")
    print()
    
    # Execute anomaly detection
    print("🔍 Executing anomaly detection...")
    anomaly_detector.execute()
    
    # Get results
    results = anomaly_detector.anomaly_results
    
    print(f"\n📈 Results:")
    print(f"  Total logs processed: {len(results)}")
    print(f"  Anomalies detected: {results['is_anomaly'].sum()}")
    print(f"  Safe logs: {(results['is_anomaly'] == 0).sum()}")
    
    # Check consistency for identical patterns
    print(f"\n🔍 Consistency Analysis:")
    
    # Group by normalized content
    from logai.utils.log_normalizer import LogNormalizer, NormalizationConfig
    
    normalizer = LogNormalizer(NormalizationConfig())
    normalized_groups = {}
    
    for i, log in enumerate(test_logs):
        normalized = normalizer.normalize(log)
        if normalized not in normalized_groups:
            normalized_groups[normalized] = []
        normalized_groups[normalized].append(i)
    
    inconsistencies = 0
    
    for pattern, indices in normalized_groups.items():
        if len(indices) > 1:  # Only check groups with multiple logs
            classifications = [results.iloc[idx]['is_anomaly'] for idx in indices]
            unique_classifications = set(classifications)
            
            print(f"\nPattern: {pattern[:80]}...")
            print(f"  Log indices: {indices}")
            print(f"  Classifications: {classifications}")
            
            if len(unique_classifications) > 1:
                inconsistencies += 1
                print(f"  ❌ INCONSISTENT: Multiple classifications found!")
            else:
                print(f"  ✅ CONSISTENT: All logs classified as {classifications[0]}")
    
    print(f"\n📊 Summary:")
    print(f"  Unique normalized patterns: {len(normalized_groups)}")
    print(f"  Pattern groups with multiple logs: {sum(1 for indices in normalized_groups.values() if len(indices) > 1)}")
    print(f"  Inconsistencies found: {inconsistencies}")
    
    if inconsistencies == 0:
        print("\n🎉 SUCCESS: All identical logs classified consistently!")
        print("The comprehensive normalization solution is working correctly.")
    else:
        print(f"\n⚠️  WARNING: Found {inconsistencies} inconsistencies!")
        print("The normalization solution needs further refinement.")
    
    # Show detailed results
    print(f"\n📋 Detailed Results:")
    for i, (log, result) in enumerate(zip(test_logs, results['is_anomaly'])):
        normalized = normalizer.normalize(log)
        status = "ANOMALY" if result == 1.0 else "SAFE"
        print(f"  {i+1:2d}. [{status:8s}] {log[:60]}...")
        print(f"       Normalized: {normalized[:60]}...")

if __name__ == "__main__":
    test_final_solution() 