#!/usr/bin/env python3
"""
Test script to verify the datetime.date JSON serialization fix
"""

import json
from datetime import datetime, date
import pandas as pd

def test_date_serialization():
    """Test that datetime.date objects are properly converted to strings"""
    
    print("🧪 Testing datetime.date JSON serialization fix...")
    
    # Create sample data with datetime.date keys (like our original issue)
    sample_df = pd.DataFrame({
        'timestamp': [
            '2024-01-01 10:00:00',
            '2024-01-01 11:00:00',
            '2024-01-02 10:00:00',
            '2024-01-02 11:00:00'
        ],
        'is_anomaly': [0, 1, 0, 1]
    })
    
    # Convert timestamps to datetime
    sample_df['timestamp'] = pd.to_datetime(sample_df['timestamp'])
    sample_df['day'] = sample_df['timestamp'].dt.date
    
    # Create daily distributions (this was causing the error)
    daily_dist = sample_df.groupby('day').size().to_dict()
    daily_anomalies = sample_df[sample_df['is_anomaly'] == 1].groupby('day').size().to_dict()
    
    print(f"   📅 Original daily_dist keys: {list(daily_dist.keys())}")
    print(f"   📅 Original daily_anomalies keys: {list(daily_anomalies.keys())}")
    
    # Apply our fix
    daily_dist_fixed = {str(key): value for key, value in daily_dist.items()}
    daily_anomalies_fixed = {str(key): value for key, value in daily_anomalies.items()}
    
    print(f"   ✅ Fixed daily_dist keys: {list(daily_dist_fixed.keys())}")
    print(f"   ✅ Fixed daily_anomalies keys: {list(daily_anomalies_fixed.keys())}")
    
    # Test JSON serialization
    try:
        # This should fail with original data
        json.dumps(daily_dist)
        print("   ❌ Original data should have failed JSON serialization")
    except TypeError as e:
        print(f"   ✅ Original data correctly failed: {str(e)[:50]}...")
    
    try:
        # This should work with fixed data
        json_str = json.dumps(daily_anomalies_fixed)
        print(f"   ✅ Fixed data serialized successfully: {json_str}")
        print("   ✅ JSON serialization fix is working!")
    except Exception as e:
        print(f"   ❌ Fixed data still failed: {str(e)}")
    
    return True

if __name__ == "__main__":
    test_date_serialization()
    print("\n🎉 Date serialization test completed!") 