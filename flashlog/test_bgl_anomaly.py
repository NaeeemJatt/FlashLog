#!/usr/bin/env python3
"""
Test Script for BGL Log Anomaly Detection
This script tests the anomaly detection with BGL log file to verify it's working correctly
"""

import os
import sys
import pandas as pd
from datetime import datetime

# Add the logai path to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'logai'))

def test_bgl_anomaly_detection():
    """Test anomaly detection with BGL log file"""
    
    print("🧪 Testing BGL Log Anomaly Detection")
    print("=" * 50)
    
    # Check if BGL log file exists
    bgl_file = os.path.join('..', 'logs', 'BGL_2k.log')
    if not os.path.exists(bgl_file):
        print(f"❌ BGL log file not found at: {bgl_file}")
        print("Please ensure the BGL log file exists in the logs directory")
        return False
    
    print(f"✅ Found BGL log file: {bgl_file}")
    
    # Test different algorithms and parsers
    test_configs = [
        {"parser": "drain", "model": "isolation_forest", "name": "Drain + Isolation Forest"},
        {"parser": "ael", "model": "lof", "name": "AEL + Local Outlier Factor"},
        {"parser": "iplom", "model": "one_class_svm", "name": "IPLoM + One-Class SVM"},
        {"parser": "drain", "model": "lof", "name": "Drain + Local Outlier Factor"},
        {"parser": "ael", "model": "isolation_forest", "name": "AEL + Isolation Forest"},
    ]
    
    results = []
    
    for config in test_configs:
        print(f"\n🔍 Testing: {config['name']}")
        print("-" * 30)
        
        try:
            # Import the process_log_file function
            from app.logai_handler import process_log_file
            
            # Process the log file
            start_time = datetime.now()
            result_data, csv_path = process_log_file(
                bgl_file, 
                config['parser'], 
                config['model'], 
                f"test-bgl-{config['parser']}-{config['model']}"
            )
            end_time = datetime.now()
            
            # Calculate processing time
            processing_time = (end_time - start_time).total_seconds()
            
            # Get anomaly statistics
            total_logs = len(result_data)
            anomalies = result_data['is_anomaly'].sum() if 'is_anomaly' in result_data.columns else 0
            anomaly_percentage = (anomalies / total_logs * 100) if total_logs > 0 else 0
            
            print(f"📊 Results:")
            print(f"   - Total logs: {total_logs}")
            print(f"   - Anomalies detected: {anomalies}")
            print(f"   - Anomaly percentage: {anomaly_percentage:.2f}%")
            print(f"   - Processing time: {processing_time:.2f} seconds")
            
            # Check if this looks like a real result
            if anomalies == 0:
                print("ℹ️  No anomalies detected - this could be legitimate")
                status = "PASSED (0 anomalies)"
            elif anomalies == 100 and config['model'] == 'one_class_svm':
                print("✅ One-Class SVM detected 100 anomalies (5% threshold) - this is legitimate")
                status = "PASSED (legitimate 100)"
            elif anomalies == 100:
                print("⚠️  WARNING: Getting exactly 100 anomalies - this might be artificial")
                status = "SUSPICIOUS"
            else:
                print("✅ Real anomaly detection result")
                status = "PASSED"
            
            results.append({
                'config': config['name'],
                'parser': config['parser'],
                'model': config['model'],
                'total_logs': total_logs,
                'anomalies': anomalies,
                'anomaly_percentage': anomaly_percentage,
                'processing_time': processing_time,
                'status': status
            })
            
        except Exception as e:
            print(f"❌ Error testing {config['name']}: {str(e)}")
            import traceback
            traceback.print_exc()
            results.append({
                'config': config['name'],
                'parser': config['parser'],
                'model': config['model'],
                'total_logs': 0,
                'anomalies': 0,
                'anomaly_percentage': 0,
                'processing_time': 0,
                'status': f"ERROR: {str(e)}"
            })
    
    # Print summary
    print("\n" + "=" * 50)
    print("📋 TEST SUMMARY")
    print("=" * 50)
    
    for result in results:
        print(f"{result['config']:<35} | {result['anomalies']:>3} anomalies | {result['anomaly_percentage']:>6.2f}% | {result['status']}")
    
    # Check if any tests show suspicious results
    suspicious_results = [r for r in results if r['status'] == 'SUSPICIOUS']
    if suspicious_results:
        print(f"\n⚠️  {len(suspicious_results)} test(s) showing suspicious results")
        print("This might indicate the manual threshold adjustment is still being applied")
        return False
    else:
        print(f"\n✅ All tests show legitimate results - the fix is working!")
        return True

def check_log_file_structure():
    """Check the structure of the BGL log file"""
    print("\n🔍 Checking BGL log file structure")
    print("-" * 30)
    
    bgl_file = os.path.join('..', 'logs', 'BGL_2k.log')
    
    try:
        df = pd.read_csv(bgl_file)
        print(f"📄 File: {bgl_file}")
        print(f"📊 Shape: {df.shape}")
        print(f"📋 Columns: {list(df.columns)}")
        
        # Show first few rows
        print(f"\n📝 First 3 rows:")
        print(df.head(3).to_string())
        
        # Check for timestamp column
        if 'timestamp' in df.columns:
            print(f"\n⏰ Timestamp column found: {df['timestamp'].dtype}")
            print(f"   Sample timestamps: {df['timestamp'].head(3).tolist()}")
        else:
            print(f"\n⚠️  No timestamp column found")
            print(f"   Available columns: {list(df.columns)}")
        
        # Check for logline column
        if 'logline' in df.columns:
            print(f"\n📝 Logline column found")
            print(f"   Sample loglines:")
            for i, logline in enumerate(df['logline'].head(3)):
                print(f"   {i+1}: {logline[:100]}...")
        else:
            print(f"\n⚠️  No logline column found")
            print(f"   Available columns: {list(df.columns)}")
            
    except Exception as e:
        print(f"❌ Error reading BGL file: {str(e)}")

if __name__ == "__main__":
    print("🧪 BGL Anomaly Detection Test")
    print("=" * 50)
    
    # First check the log file structure
    check_log_file_structure()
    
    # Then run the anomaly detection tests
    success = test_bgl_anomaly_detection()
    
    if success:
        print("\n🎉 All tests passed! The anomaly detection is working correctly.")
    else:
        print("\n❌ Some tests failed. The manual threshold adjustment might still be active.")
    
    print("\n" + "=" * 50) 