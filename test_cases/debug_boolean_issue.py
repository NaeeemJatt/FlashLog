#!/usr/bin/env python3
"""
Debug script to check the actual data format being sent from backend
"""

import sys
import os
import pandas as pd
import numpy as np

# Add the logai directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'logai'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'FYP_GUI'))

from FYP_GUI.app.logai_handler import process_log_file

def debug_data_format():
    """Debug the actual data format being sent"""
    
    print("🔍 Debugging data format issue...")
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
        
        # Check the raw results DataFrame
        print(f"\n📊 RAW RESULTS ANALYSIS:")
        print(f"   Total logs: {len(results)}")
        print(f"   Columns: {list(results.columns)}")
        
        if 'is_anomaly' in results.columns:
            print(f"   is_anomaly column type: {results['is_anomaly'].dtype}")
            print(f"   is_anomaly unique values: {results['is_anomaly'].unique()}")
            print(f"   is_anomaly value counts:")
            print(results['is_anomaly'].value_counts())
            
            # Check first 10 values
            print(f"\n🔍 First 10 is_anomaly values:")
            for i, value in enumerate(results['is_anomaly'].head(10)):
                print(f"   {i+1}: {value} (type: {type(value).__name__})")
            
            # Check if there are any anomalies
            anomaly_count = results['is_anomaly'].sum()
            print(f"\n🔍 Anomaly count: {anomaly_count}")
            
            if anomaly_count > 0:
                print(f"✅ Anomalies detected: {anomaly_count}")
                
                # Show some anomaly examples
                anomaly_examples = results[results['is_anomaly'] == 1.0].head(3)
                print(f"\n🔍 Example anomalies:")
                for idx, row in anomaly_examples.iterrows():
                    print(f"   Anomaly {idx}: {row['logline'][:100]}...")
            else:
                print(f"❌ No anomalies detected - this might be the issue!")
                
        else:
            print(f"❌ 'is_anomaly' column not found!")
            print(f"   Available columns: {list(results.columns)}")
        
        # Check the saved CSV file
        if os.path.exists(result_path):
            print(f"\n📄 SAVED CSV ANALYSIS:")
            saved_results = pd.read_csv(result_path)
            print(f"   CSV file: {result_path}")
            print(f"   CSV columns: {list(saved_results.columns)}")
            
            if 'is_anomaly' in saved_results.columns:
                print(f"   CSV is_anomaly column type: {saved_results['is_anomaly'].dtype}")
                print(f"   CSV is_anomaly unique values: {saved_results['is_anomaly'].unique()}")
                print(f"   CSV is_anomaly value counts:")
                print(saved_results['is_anomaly'].value_counts())
                
                # Check first 10 values in CSV
                print(f"\n🔍 First 10 CSV is_anomaly values:")
                for i, value in enumerate(saved_results['is_anomaly'].head(10)):
                    print(f"   {i+1}: {value} (type: {type(value).__name__})")
                
                csv_anomaly_count = saved_results['is_anomaly'].sum()
                print(f"\n🔍 CSV Anomaly count: {csv_anomaly_count}")
                
                if csv_anomaly_count != anomaly_count:
                    print(f"❌ MISMATCH: DataFrame has {anomaly_count} anomalies, CSV has {csv_anomaly_count}")
                else:
                    print(f"✅ CSV matches DataFrame: {csv_anomaly_count} anomalies")
            else:
                print(f"❌ 'is_anomaly' column not found in CSV!")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = debug_data_format()
    if not success:
        import sys
        sys.exit(1) 