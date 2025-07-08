#!/usr/bin/env python3
"""
Test script to verify log parsers are working properly
"""

import sys
import os
import pandas as pd

# Add the logai directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'logai'))

from logai.algorithms.parsing_algo.drain import Drain, DrainParams
from logai.algorithms.parsing_algo.ael import AEL, AELParams
from logai.algorithms.parsing_algo.iplom import IPLoM, IPLoMParams

def test_drain_parser():
    """Test Drain parser functionality"""
    print("Testing Drain Parser...")
    
    # Sample log data
    log_data = [
        "2025-01-01 10:00:01 User john.doe logged in from 192.168.1.100",
        "2025-01-01 10:00:02 User jane.smith logged in from 192.168.1.101", 
        "2025-01-01 10:00:03 User admin logged in from 192.168.1.102",
        "2025-01-01 10:00:04 Error: Connection timeout for user john.doe",
        "2025-01-01 10:00:05 Error: Connection timeout for user jane.smith",
        "2025-01-01 10:00:06 System: Database backup completed successfully",
        "2025-01-01 10:00:07 System: Database backup completed successfully"
    ]
    
    log_series = pd.Series(log_data, name='logline')
    
    # Test Drain parser
    try:
        drain_params = DrainParams(sim_th=0.4, depth=3)
        drain_parser = Drain(drain_params)
        
        # Parse the logs
        parsed_logs = drain_parser.parse(log_series)
        
        print(f"✅ Drain parser working - Parsed {len(parsed_logs)} log entries")
        print(f"   Created {drain_parser.clusters_counter} clusters")
        print(f"   Sample parsed templates:")
        for i, template in enumerate(parsed_logs.head(3)):
            print(f"   {i+1}. {template}")
        
        return True
        
    except Exception as e:
        print(f"❌ Drain parser failed: {str(e)}")
        return False

def test_ael_parser():
    """Test AEL parser functionality"""
    print("\nTesting AEL Parser...")
    
    # Sample log data
    log_data = [
        "User john.doe logged in from 192.168.1.100",
        "User jane.smith logged in from 192.168.1.101", 
        "User admin logged in from 192.168.1.102",
        "Error: Connection timeout for user john.doe",
        "Error: Connection timeout for user jane.smith",
        "System: Database backup completed successfully",
        "System: Database backup completed successfully"
    ]
    
    log_series = pd.Series(log_data, name='logline')
    
    # Test AEL parser
    try:
        ael_params = AELParams(minEventCount=2, merge_percent=0.5)
        ael_parser = AEL(ael_params)
        
        # Parse the logs
        parsed_logs = ael_parser.parse(log_series)
        
        print(f"✅ AEL parser working - Parsed {len(parsed_logs)} log entries")
        print(f"   Sample parsed templates:")
        for i, template in enumerate(parsed_logs.head(3)):
            print(f"   {i+1}. {template}")
        
        return True
        
    except Exception as e:
        print(f"❌ AEL parser failed: {str(e)}")
        return False

def test_iplom_parser():
    """Test IPLoM parser functionality"""
    print("\nTesting IPLoM Parser...")
    
    # Sample log data
    log_data = [
        "User john.doe logged in from 192.168.1.100",
        "User jane.smith logged in from 192.168.1.101", 
        "User admin logged in from 192.168.1.102",
        "Error: Connection timeout for user john.doe",
        "Error: Connection timeout for user jane.smith",
        "System: Database backup completed successfully",
        "System: Database backup completed successfully"
    ]
    
    log_series = pd.Series(log_data, name='logline')
    
    # Test IPLoM parser
    try:
        iplom_params = IPLoMParams()
        iplom_parser = IPLoM(iplom_params)
        
        # Parse the logs
        parsed_logs = iplom_parser.parse(log_series)
        
        print(f"✅ IPLoM parser working - Parsed {len(parsed_logs)} log entries")
        print(f"   Sample parsed templates:")
        for i, template in enumerate(parsed_logs.head(3)):
            print(f"   {i+1}. {template}")
        
        return True
        
    except Exception as e:
        print(f"❌ IPLoM parser failed: {str(e)}")
        return False

def test_parser_integration():
    """Test parser integration with your application workflow"""
    print("\nTesting Parser Integration...")
    
    try:
        from logai.applications.log_anomaly_detection import LogAnomalyDetection
        from logai.applications.application_interfaces import WorkFlowConfig
        
        # Create a simple test configuration
        config = WorkFlowConfig.from_dict({
            "data_loader_config": {
                "filepath": "test_logs.csv",
                "dimensions": {
                    "body": ["logline"]
                }
            },
            "preprocessor_config": {
                "custom_delimiters_regex": []
            },
            "log_parser_config": {
                "parsing_algorithm": "drain"
            },
            "log_vectorizer_config": {
                "algo_name": "tfidf"
            },
            "categorical_encoder_config": {
                "encoding_type": "onehot"
            },
            "feature_extractor_config": {
                "feature_type": "log_vector",
                "window_size": 5,
                "embedding_method": "tfidf"
            },
            "anomaly_detection_config": {
                "model_type": "isolation_forest"
            }
        })
        
        print("✅ Parser integration configuration created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Parser integration failed: {str(e)}")
        return False

def main():
    """Run all parser tests"""
    print("=" * 60)
    print("LOG PARSER COMPREHENSIVE TEST")
    print("=" * 60)
    
    results = []
    
    # Test individual parsers
    results.append(test_drain_parser())
    results.append(test_ael_parser())
    results.append(test_iplom_parser())
    
    # Test integration
    results.append(test_parser_integration())
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    tests = ["Drain Parser", "AEL Parser", "IPLoM Parser", "Integration"]
    for test, result in zip(tests, results):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test:20} {status}")
    
    all_passed = all(results)
    print(f"\nOverall Status: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    if all_passed:
        print("\n🎉 All log parsers are working properly!")
    else:
        print("\n⚠️  Some parsers have issues that need attention.")
    
    return all_passed

if __name__ == "__main__":
    main() 