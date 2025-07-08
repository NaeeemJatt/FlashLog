#!/usr/bin/env python3
"""
Test script to verify logai functionality
"""

import sys
import os
import tempfile

# Add the parent directory to the path to import logai
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def test_logai_import():
    """Test if logai can be imported"""
    try:
        from logai.applications.log_anomaly_detection import LogAnomalyDetection
        from logai.applications.application_interfaces import WorkFlowConfig
        print("✅ LogAI imports successful")
        return True
    except ImportError as e:
        print(f"❌ LogAI import failed: {e}")
        return False

def test_simple_log_processing():
    """Test simple log processing"""
    try:
        # Create a simple test log file
        test_log_content = """2024-01-01 10:00:00 INFO Application started
2024-01-01 10:00:01 INFO User login successful
2024-01-01 10:00:02 ERROR Database connection failed
2024-01-01 10:00:03 INFO Application started
2024-01-01 10:00:04 INFO User login successful"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_log_content)
            temp_file = f.name
        
        print(f"📝 Created test log file: {temp_file}")
        
        # Test the logai_handler
        from app.logai_handler import process_log_file
        
        print("🔍 Testing log processing...")
        results, csv_path = process_log_file(temp_file, "drain", "isolation_forest", "test-index")
        
        print(f"✅ Log processing successful!")
        print(f"   - Results shape: {results.shape}")
        print(f"   - CSV saved to: {csv_path}")
        print(f"   - Anomalies found: {results['is_anomaly'].sum()}")
        
        # Clean up
        os.unlink(temp_file)
        if os.path.exists(csv_path):
            os.unlink(csv_path)
        
        return True
        
    except Exception as e:
        print(f"❌ Log processing test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Testing LogAI functionality...")
    
    if test_logai_import():
        test_simple_log_processing()
    else:
        print("❌ Cannot proceed without LogAI imports") 