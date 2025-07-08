#!/usr/bin/env python3
"""
Test script to simulate .log file upload and processing
"""

import os
import sys
sys.path.append('FYP_GUI')

from app.logai_handler import preprocess_log, process_log_file

def create_test_log_file():
    """Create a test .log file"""
    test_log_content = """2024-01-15 10:30:15 INFO [MainThread] Application started successfully
2024-01-15 10:30:16 DEBUG [WorkerThread-1] Processing request ID: 12345
2024-01-15 10:30:17 ERROR [WorkerThread-1] Database connection failed
2024-01-15 10:30:18 WARN [MainThread] High memory usage detected
2024-01-15 10:30:19 INFO [WorkerThread-2] Request completed successfully
2024-01-15 10:30:20 ERROR [WorkerThread-1] Invalid user credentials
2024-01-15 10:30:21 DEBUG [WorkerThread-2] Cache miss for key: user_profile_123
2024-01-15 10:30:22 INFO [MainThread] System health check passed
2024-01-15 10:30:23 ERROR [WorkerThread-1] Network timeout occurred
2024-01-15 10:30:24 WARN [MainThread] Disk space running low"""
    
    test_file = "test_upload.log"
    with open(test_file, 'w') as f:
        f.write(test_log_content)
    
    return test_file

def test_log_processing():
    """Test the log processing pipeline"""
    print("🧪 Testing .log file processing...")
    
    # Create test log file
    test_file = create_test_log_file()
    print(f"✅ Created test file: {test_file}")
    
    try:
        # Test preprocessing
        print("\n📝 Testing preprocessing...")
        cleaned_path, has_timestamp = preprocess_log(test_file)
        print(f"✅ Preprocessing successful")
        print(f"   - Cleaned file: {cleaned_path}")
        print(f"   - Has timestamp: {has_timestamp}")
        
        # Check the cleaned file
        import pandas as pd
        df = pd.read_csv(cleaned_path)
        print(f"   - Rows processed: {len(df)}")
        print(f"   - Columns: {list(df.columns)}")
        print(f"   - Sample logline: {df['logline'].iloc[0][:50]}...")
        
        # Test full processing
        print("\n🔍 Testing full anomaly detection...")
        results, csv_path = process_log_file(test_file, "drain", "isolation_forest", "test-index")
        print(f"✅ Full processing successful")
        print(f"   - Results file: {csv_path}")
        print(f"   - Total entries: {len(results)}")
        print(f"   - Anomalies detected: {results['is_anomaly'].sum()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during processing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup
        if os.path.exists(test_file):
            os.remove(test_file)
        if 'cleaned_path' in locals() and os.path.exists(cleaned_path):
            os.remove(cleaned_path)
        if 'csv_path' in locals() and os.path.exists(csv_path):
            os.remove(csv_path)

if __name__ == "__main__":
    success = test_log_processing()
    if success:
        print("\n🎉 All tests passed! .log file processing is working correctly.")
    else:
        print("\n💥 Tests failed! There's an issue with .log file processing.") 