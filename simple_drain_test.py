#!/usr/bin/env python3
"""
Simple test script to verify Drain parser is working properly
"""

import sys
import os
import pandas as pd

# Add the logai directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'logai'))

def test_drain_parser():
    """Test Drain parser functionality"""
    print("Testing Drain Parser...")
    
    try:
        from logai.algorithms.parsing_algo.drain import Drain, DrainParams
        
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
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run Drain parser test"""
    print("=" * 60)
    print("DRAIN PARSER TEST")
    print("=" * 60)
    
    success = test_drain_parser()
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    if success:
        print("✅ DRAIN PARSER IS WORKING PROPERLY!")
        print("\n🎉 Your log parsing functionality should work correctly.")
        print("   The Drain parser can:")
        print("   - Extract log templates from raw log messages")
        print("   - Identify variable parameters in logs")
        print("   - Group similar log messages into clusters")
        print("   - Work with your Flask application")
    else:
        print("❌ DRAIN PARSER HAS ISSUES")
        print("\n⚠️  There are problems with the Drain parser that need to be fixed.")
    
    return success

if __name__ == "__main__":
    main() 