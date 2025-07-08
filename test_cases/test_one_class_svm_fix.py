#!/usr/bin/env python3
"""
Test script to verify One-Class SVM anomaly detection fix
"""

import sys
import os
import pandas as pd
import numpy as np

# Add the logai directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'logai'))

from logai.applications.application_interfaces import WorkFlowConfig
from logai.applications.log_anomaly_detection import LogAnomalyDetection
from logai.config_interfaces import Config

def create_test_config():
    """Create a test configuration for One-Class SVM with AEL parser"""
    
    # Create the workflow configuration
    config_dict = {
        "data_loader_config": {
            "filepath": "logs/BGL_2k.log_structured.csv",
            "log_format": "csv",
            "datetime_format": "%Y-%m-%d %H:%M:%S",
            "logline_name": "logline",
            "timestamp_name": "timestamp"
        },
        "preprocessor_config": {
            "custom_delimiters_regex": None,
            "custom_replacement": None
        },
        "log_parser_config": {
            "algo_name": "ael",
            "algo_params": {
                "max_child_id": 100,
                "merge_threshold": 0.3,
                "sim_threshold": 0.6
            }
        },
        "log_vectorizer_config": {
            "algo_name": "tfidf",
            "algo_params": {
                "max_features": 100,
                "ngram_range": [1, 1]
            }
        },
        "feature_extractor_config": {
            "algo_name": "basic",
            "algo_params": {}
        },
        "anomaly_detection_config": {
            "algo_name": "one_class_svm",
            "algo_params": {
                "kernel": "rbf",
                "nu": 0.05,  # Expect only 5% anomalies (much more conservative than default 0.5)
                "gamma": "auto"
            }
        }
    }
    
    return WorkFlowConfig.from_dict(config_dict)

def test_one_class_svm():
    """Test One-Class SVM anomaly detection with the fix"""
    
    print("🧪 Testing One-Class SVM anomaly detection fix...")
    print("=" * 60)
    
    try:
        # Create configuration
        config = create_test_config()
        print("✅ Configuration created successfully")
        
        # Create and run anomaly detector
        detector = LogAnomalyDetection(config)
        print("✅ Anomaly detector created successfully")
        
        # Execute anomaly detection
        detector.execute()
        print("✅ Anomaly detection executed successfully")
        
        # Get results
        results = detector.results
        print(f"✅ Results obtained: {len(results)} total logs")
        
        # Analyze results
        anomaly_count = results['is_anomaly'].sum()
        normal_count = len(results) - anomaly_count
        anomaly_percentage = (anomaly_count / len(results)) * 100
        
        print(f"\n📊 RESULTS SUMMARY:")
        print(f"   Total logs: {len(results)}")
        print(f"   Anomalies detected: {anomaly_count}")
        print(f"   Normal logs: {normal_count}")
        print(f"   Anomaly percentage: {anomaly_percentage:.2f}%")
        
        # Check if results are reasonable
        if anomaly_count == 0:
            print("⚠️  WARNING: No anomalies detected - this might be too conservative")
        elif anomaly_count == len(results):
            print("❌ ERROR: All logs marked as anomalies - this indicates a bug!")
            return False
        elif anomaly_percentage > 50:
            print("⚠️  WARNING: More than 50% anomalies detected - this seems too high")
        elif anomaly_percentage < 1:
            print("⚠️  WARNING: Less than 1% anomalies detected - this might be too conservative")
        else:
            print("✅ Anomaly detection results look reasonable!")
        
        # Show some example anomalies
        if anomaly_count > 0:
            print(f"\n🔍 EXAMPLE ANOMALIES:")
            anomaly_examples = results[results['is_anomaly'] == 1.0].head(3)
            for idx, row in anomaly_examples.iterrows():
                print(f"   Anomaly {idx}: {row['logline'][:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_one_class_svm()
    if success:
        print("\n✅ Test completed successfully!")
    else:
        print("\n❌ Test failed!")
        sys.exit(1) 