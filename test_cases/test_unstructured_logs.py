#!/usr/bin/env python3
"""
Test script to verify unstructured log file handling
"""

import os
import tempfile
import pandas as pd

def create_test_log_file():
    """Create a test unstructured log file"""
    log_content = """2024-01-01 10:00:01 User john.doe logged in from 192.168.1.100
2024-01-01 10:00:02 Error: Connection timeout for user jane.smith
2024-01-01 10:00:03 System: Database backup completed successfully
2024-01-01 10:00:04 Warning: High memory usage detected
2024-01-01 10:00:05 User admin logged in from 192.168.1.101
2024-01-01 10:00:06 Error: Disk space low on /dev/sda1
2024-01-01 10:00:07 System: Service restart completed
2024-01-01 10:00:08 User guest logged in from 192.168.1.102
2024-01-01 10:00:09 Error: Network connection lost
2024-01-01 10:00:10 System: Log rotation completed"""
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(log_content)
        return f.name

def test_unstructured_log_processing():
    """Test the unstructured log processing"""
    print("Testing Unstructured Log Processing...")
    
    try:
        # Import the function
        import sys
        sys.path.insert(0, 'FYP_GUI')
        from app.logai_handler import preprocess_log
        
        # Create test file
        test_file = create_test_log_file()
        print(f"✅ Created test log file: {test_file}")
        
        # Test processing
        cleaned_path, has_timestamp = preprocess_log(test_file)
        print(f"✅ Successfully processed log file")
        print(f"   Cleaned file: {cleaned_path}")
        print(f"   Has timestamp: {has_timestamp}")
        
        # Check the output
        df = pd.read_csv(cleaned_path)
        print(f"✅ Output DataFrame shape: {df.shape}")
        print(f"   Columns: {list(df.columns)}")
        print(f"   Sample log entries:")
        for i, row in df.head(3).iterrows():
            print(f"   {i+1}. {row['logline']}")
        
        # Cleanup
        os.unlink(test_file)
        os.unlink(cleaned_path)
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_csv_with_inconsistent_columns():
    """Test handling of CSV files with inconsistent columns"""
    print("\nTesting CSV with Inconsistent Columns...")
    
    try:
        import sys
        sys.path.insert(0, 'FYP_GUI')
        from app.logai_handler import preprocess_log
        
        # Create a problematic CSV file
        csv_content = """timestamp,message
2024-01-01 10:00:01,User login
2024-01-01 10:00:02,Error message
2024-01-01 10:00:03,Warning,high memory
2024-01-01 10:00:04,System status,ok,normal
2024-01-01 10:00:05,User logout"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(csv_content)
            test_file = f.name
        
        print(f"✅ Created problematic CSV file: {test_file}")
        
        # Test processing
        cleaned_path, has_timestamp = preprocess_log(test_file)
        print(f"✅ Successfully processed problematic CSV file")
        
        # Check the output
        df = pd.read_csv(cleaned_path)
        print(f"✅ Output DataFrame shape: {df.shape}")
        
        # Cleanup
        os.unlink(test_file)
        os.unlink(cleaned_path)
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("UNSTRUCTURED LOG PROCESSING TEST")
    print("=" * 60)
    
    results = []
    
    # Test 1: Unstructured log file
    results.append(test_unstructured_log_processing())
    
    # Test 2: CSV with inconsistent columns
    results.append(test_csv_with_inconsistent_columns())
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    tests = ["Unstructured Log Processing", "CSV with Inconsistent Columns"]
    for test, result in zip(tests, results):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test:35} {status}")
    
    all_passed = all(results)
    print(f"\nOverall Status: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    if all_passed:
        print("\n🎉 Your application can now handle unstructured log files properly!")
        print("✅ Fixed the ParserError issue")
        print("✅ Supports various file formats")
        print("✅ Handles inconsistent data gracefully")
    else:
        print("\n⚠️  Some issues remain that need attention.")
    
    return all_passed

if __name__ == "__main__":
    main() 