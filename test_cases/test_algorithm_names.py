#!/usr/bin/env python3
"""
Test script to verify algorithm names are correct
"""

import sys
import os

# Add the logai directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'logai'))

from logai.algorithms.factory import factory

def test_algorithm_names():
    """Test that all algorithm names are valid"""
    
    print("🧪 Testing algorithm names...")
    print("=" * 60)
    
    # Get available algorithms
    available_algorithms = factory._algorithms.get('detection', {})
    print(f"✅ Available detection algorithms: {list(available_algorithms.keys())}")
    
    # Test each algorithm name
    test_algorithms = [
        'isolation_forest',
        'one_class_svm', 
        'lof',  # Fixed from local_outlier_factor
        'distribution_divergence'
    ]
    
    print(f"\n🔍 Testing algorithm names:")
    all_valid = True
    
    for algo_name in test_algorithms:
        try:
            # Try to get the algorithm config class
            config_class = factory.get_config('detection', algo_name, {})
            print(f"✅ {algo_name}: Valid")
        except Exception as e:
            print(f"❌ {algo_name}: Invalid - {e}")
            all_valid = False
    
    print(f"\n📋 Summary:")
    if all_valid:
        print("🎉 All algorithm names are valid!")
        print("✅ The frontend should work correctly now.")
    else:
        print("❌ Some algorithm names are invalid!")
        print("🔧 Please fix the invalid algorithm names.")
    
    return all_valid

if __name__ == "__main__":
    success = test_algorithm_names()
    if not success:
        import sys
        sys.exit(1) 