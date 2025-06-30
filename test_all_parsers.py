#!/usr/bin/env python3
"""
Test script to verify all three parsers work in your application
"""

import sys
import os
import pandas as pd

# Add the logai directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'logai'))

def test_all_parsers():
    """Test all three parsers functionality"""
    print("Testing All Parsers...")
    
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
    
    results = {}
    
    # Test Drain parser
    try:
        from logai.algorithms.parsing_algo.drain import Drain, DrainParams
        drain_params = DrainParams(sim_th=0.4, depth=3)
        drain_parser = Drain(drain_params)
        parsed_logs = drain_parser.parse(log_series)
        results['Drain'] = {
            'status': '✅ PASS',
            'clusters': drain_parser.clusters_counter,
            'sample': parsed_logs.iloc[0] if len(parsed_logs) > 0 else 'N/A'
        }
    except Exception as e:
        results['Drain'] = {
            'status': '❌ FAIL',
            'error': str(e)
        }
    
    # Test AEL parser
    try:
        from logai.algorithms.parsing_algo.ael import AEL, AELParams
        ael_params = AELParams(minEventCount=2, merge_percent=0.5)
        ael_parser = AEL(ael_params)
        parsed_logs = ael_parser.parse(log_series)
        results['AEL'] = {
            'status': '✅ PASS',
            'clusters': len(set(parsed_logs)),
            'sample': parsed_logs.iloc[0] if len(parsed_logs) > 0 else 'N/A'
        }
    except Exception as e:
        results['AEL'] = {
            'status': '❌ FAIL',
            'error': str(e)
        }
    
    # Test IPLoM parser
    try:
        from logai.algorithms.parsing_algo.iplom import IPLoM, IPLoMParams
        iplom_params = IPLoMParams()
        iplom_parser = IPLoM(iplom_params)
        parsed_logs = iplom_parser.parse(log_series)
        results['IPLoM'] = {
            'status': '✅ PASS',
            'clusters': len(set(parsed_logs)),
            'sample': parsed_logs.iloc[0] if len(parsed_logs) > 0 else 'N/A'
        }
    except Exception as e:
        results['IPLoM'] = {
            'status': '❌ FAIL',
            'error': str(e)
        }
    
    return results

def main():
    """Run all parser tests"""
    print("=" * 60)
    print("ALL PARSERS TEST")
    print("=" * 60)
    
    results = test_all_parsers()
    
    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    
    for parser_name, result in results.items():
        print(f"{parser_name:10} {result['status']}")
        if result['status'] == '✅ PASS':
            print(f"           Clusters: {result['clusters']}")
            print(f"           Sample: {result['sample']}")
        else:
            print(f"           Error: {result['error']}")
        print()
    
    # Summary
    passed = sum(1 for r in results.values() if r['status'] == '✅ PASS')
    total = len(results)
    
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Parsers Working: {passed}/{total}")
    
    if passed == total:
        print("🎉 ALL PARSERS ARE WORKING!")
        print("✅ Your GUI now supports all three parsers:")
        print("   - Drain Parser (Recommended)")
        print("   - AEL Parser")
        print("   - IPLoM Parser")
    else:
        print("⚠️  Some parsers have issues that need attention.")
    
    return passed == total

if __name__ == "__main__":
    main() 