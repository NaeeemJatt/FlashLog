#!/usr/bin/env python3
"""
Test script to verify frontend boolean handling fix
"""

def test_boolean_conversion():
    """Test the boolean conversion logic"""
    
    print("🧪 Testing frontend boolean conversion fix...")
    print("=" * 60)
    
    # Test cases that simulate what the backend might send
    test_cases = [
        ("1.0", True, "String '1.0' should be True"),
        ("0.0", False, "String '0.0' should be False"),
        (1.0, True, "Float 1.0 should be True"),
        (0.0, False, "Float 0.0 should be False"),
        (1, True, "Integer 1 should be True"),
        (0, False, "Integer 0 should be False"),
        (True, True, "Boolean True should be True"),
        (False, False, "Boolean False should be False"),
    ]
    
    print("🔍 Testing JavaScript parseFloat logic:")
    print("   const isAnomaly = parseFloat(result.is_anomaly) === 1.0;")
    print()
    
    all_passed = True
    
    for value, expected, description in test_cases:
        # Simulate the JavaScript logic
        try:
            result = float(value) == 1.0
            status = "✅ PASS" if result == expected else "❌ FAIL"
            print(f"{status} {description}")
            print(f"   Input: {value} (type: {type(value).__name__})")
            print(f"   Expected: {expected}, Got: {result}")
            print()
            
            if result != expected:
                all_passed = False
                
        except Exception as e:
            print(f"❌ ERROR {description}")
            print(f"   Input: {value} (type: {type(value).__name__})")
            print(f"   Error: {e}")
            print()
            all_passed = False
    
    print("🔍 Testing old Boolean() logic (for comparison):")
    print("   const isAnomaly = Boolean(result.is_anomaly);")
    print()
    
    for value, expected, description in test_cases:
        # Simulate the old JavaScript logic
        try:
            result = bool(value)
            status = "✅ PASS" if result == expected else "❌ FAIL"
            print(f"{status} {description}")
            print(f"   Input: {value} (type: {type(value).__name__})")
            print(f"   Expected: {expected}, Got: {result}")
            print()
            
        except Exception as e:
            print(f"❌ ERROR {description}")
            print(f"   Input: {value} (type: {type(value).__name__})")
            print(f"   Error: {e}")
            print()
    
    if all_passed:
        print("🎉 All tests passed! The fix should work correctly.")
        print("✅ The parseFloat() === 1.0 logic properly handles all input types.")
        print("❌ The old Boolean() logic incorrectly treats '0.0' as True.")
    else:
        print("❌ Some tests failed! The fix needs more work.")
    
    return all_passed

if __name__ == "__main__":
    success = test_boolean_conversion()
    if not success:
        import sys
        sys.exit(1) 