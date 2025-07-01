#!/usr/bin/env python3
"""
Simple test to verify the anomaly detection fix.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "logai")))

import pandas as pd
from logai.applications.log_anomaly_detection import LogAnomalyDetection
from logai.config_interfaces import WorkFlowConfig
from logai.dataloader.data_model import LogRecordObject
from logai.utils import constants

def test_anomaly_detection_fix():
    """Test the anomaly detection fix."""
    
    print("🧪 Testing Anomaly Detection Fix")
    print("=" * 50)
    
    # Create simple test logs
    test_logs = [
        "ciod: failed to read message prefix on control stream (CioStream socket to 172.16.96.116:33569",
        "ciod: failed to read message prefix on control stream (CioStream socket to 172.16.96.116:33370",
        "ciod: failed to read message prefix on control stream (CioStream socket to 192.168.1.1:8080",
        "2024-01-01 10:00:00 ERROR: Database connection failed to 192.168.1.1:5432",
        "2024-01-01 10:01:00 ERROR: Database connection failed to 192.168.1.2:5432",
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
        data_loader_config=None,
        open_set_data_loader_config=None,
        preprocessor_config=None,
        log_parser_config={
            "algo_name": "drain",
            "algo_params": {
                "depth": 4,
                "sim_th": 0.4,
                "max_children": 100,
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
            "algo_name": "isolation_forest",
            "algo_params": {
                "n_estimators": 100,
                "contamination": 0.1,
                "random_state": 42,
            }
        }
    )
    
    # Create anomaly detection instance
    anomaly_detector = LogAnomalyDetection(config)
    
    # Manually set the logrecord
    anomaly_detector._logrecord = logrecord
    
    print(f"📊 Test setup:")
    print(f"  Total logs: {len(test_logs)}")
    print()
    
    # Execute anomaly detection
    print("🔍 Executing anomaly detection...")
    try:
        anomaly_detector.execute()
        print("✅ Anomaly detection executed successfully!")
        
        # Get results
        results = anomaly_detector.anomaly_results
        
        print(f"\n📈 Results:")
        print(f"  Total logs processed: {len(results)}")
        print(f"  Anomalies detected: {results['is_anomaly'].sum()}")
        print(f"  Safe logs: {(results['is_anomaly'] == 0).sum()}")
        
        # Check consistency
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
            if len(indices) > 1:
                classifications = [results.iloc[idx]['is_anomaly'] for idx in indices]
                unique_classifications = set(classifications)
                
                if len(unique_classifications) > 1:
                    inconsistencies += 1
                    print(f"  ❌ INCONSISTENT: Pattern '{pattern[:50]}...' has multiple classifications: {classifications}")
                else:
                    print(f"  ✅ CONSISTENT: Pattern '{pattern[:50]}...' all classified as {classifications[0]}")
        
        print(f"\n📊 Summary:")
        print(f"  Unique normalized patterns: {len(normalized_groups)}")
        print(f"  Inconsistencies found: {inconsistencies}")
        
        if inconsistencies == 0:
            print("\n🎉 SUCCESS: All identical logs classified consistently!")
        else:
            print(f"\n⚠️  WARNING: Found {inconsistencies} inconsistencies!")
            
    except Exception as e:
        print(f"❌ Anomaly detection failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_anomaly_detection_fix() 