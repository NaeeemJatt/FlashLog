#!/usr/bin/env python3
"""
Test script to verify GUI anomaly detection fix
"""

import sys
import os
import pandas as pd
import numpy as np

# Add the logai directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'logai'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'FYP_GUI'))

from FYP_GUI.app.logai_handler import process_log_file

def test_gui_anomaly_detection():
    """Test the GUI anomaly detection with the fix"""
    
    print("🧪 Testing GUI anomaly detection fix...")
    print("=" * 60)
    
    try:
        # Test with a sample log file
        test_file = "logs/BGL_2k.log_structured.csv"
        
        if not os.path.exists(test_file):
            print(f"❌ Test file not found: {test_file}")
            return False
        
        print(f"✅ Using test file: {test_file}")
        
        # Test One-Class SVM with AEL parser
        print("\n🔍 Testing One-Class SVM with AEL parser...")
        results, result_path = process_log_file(
            filepath=test_file,
            parser_algo="ael",
            model_type="one_class_svm",
            index_name="test_index"
        )
        
        print(f"✅ Processing completed successfully")
        print(f"✅ Results saved to: {result_path}")
        
        # Analyze results
        total_logs = len(results)
        anomaly_count = results['is_anomaly'].sum()
        normal_count = total_logs - anomaly_count
        anomaly_percentage = (anomaly_count / total_logs) * 100
        
        print(f"\n📊 RESULTS SUMMARY:")
        print(f"   Total logs: {total_logs}")
        print(f"   Anomalies detected: {anomaly_count}")
        print(f"   Normal logs: {normal_count}")
        print(f"   Anomaly percentage: {anomaly_percentage:.2f}%")
        
        # Check if results are reasonable
        if anomaly_count == 0:
            print("⚠️  WARNING: No anomalies detected - this might be too conservative")
        elif anomaly_count == total_logs:
            print("❌ ERROR: All logs marked as anomalies - this indicates the fix didn't work!")
            return False
        elif anomaly_percentage > 50:
            print("⚠️  WARNING: More than 50% anomalies detected - this seems too high")
        elif anomaly_percentage < 1:
            print("⚠️  WARNING: Less than 1% anomalies detected - this might be too conservative")
        else:
            print("✅ Anomaly detection results look reasonable!")
        
        # Check if the results file was created and contains the right data
        if os.path.exists(result_path):
            saved_results = pd.read_csv(result_path)
            saved_anomaly_count = saved_results['is_anomaly'].sum()
            print(f"✅ Results file created successfully")
            print(f"✅ Saved file anomaly count: {saved_anomaly_count}")
            
            if saved_anomaly_count == anomaly_count:
                print("✅ Results consistency check passed!")
            else:
                print("❌ Results consistency check failed!")
                return False
        else:
            print("❌ Results file was not created!")
            return False
        
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
    success = test_gui_anomaly_detection()
    if success:
        print("\n✅ Test completed successfully!")
        print("🎉 The GUI fix should now work correctly!")
    else:
        print("\n❌ Test failed!")
        sys.exit(1) 