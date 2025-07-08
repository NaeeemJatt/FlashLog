#!/usr/bin/env python3
"""
Test the exact JavaScript logic that should be used in the frontend
"""

def test_js_logic():
    """Test the exact JavaScript logic"""
    
    print("🧪 Testing exact JavaScript logic...")
    print("=" * 60)
    
    # Test cases based on the actual data format (float64)
    test_cases = [
        (0.0, False, "Float 0.0 should be False"),
        (1.0, True, "Float 1.0 should be True"),
        ("0.0", False, "String '0.0' should be False"),
        ("1.0", True, "String '1.0' should be True"),
        (0, False, "Integer 0 should be False"),
        (1, True, "Integer 1 should be True"),
    ]
    
    print("🔍 Testing JavaScript parseFloat logic:")
    print("   const isAnomaly = parseFloat(result.is_anomaly) === 1.0;")
    print()
    
    all_passed = True
    
    for value, expected, description in test_cases:
        # Simulate the exact JavaScript logic
        try:
            result = float(value) == 1.0
            status = "✅ PASS" if result == expected else "❌ FAIL"
            print(f"{status} {description}")
            print(f"   Input: {value} (type: {type(value).__name__})")
            print(f"   parseFloat({value}) === 1.0: {result}")
            print(f"   Expected: {expected}")
            print()
            
            if result != expected:
                all_passed = False
                
        except Exception as e:
            print(f"❌ ERROR {description}")
            print(f"   Input: {value} (type: {type(value).__name__})")
            print(f"   Error: {e}")
            print()
            all_passed = False
    
    print("🔍 Testing alternative JavaScript logic:")
    print("   const isAnomaly = result.is_anomaly === 1.0;")
    print()
    
    for value, expected, description in test_cases:
        # Simulate direct comparison (no parseFloat)
        try:
            result = value == 1.0
            status = "✅ PASS" if result == expected else "❌ FAIL"
            print(f"{status} {description}")
            print(f"   Input: {value} (type: {type(value).__name__})")
            print(f"   {value} === 1.0: {result}")
            print(f"   Expected: {expected}")
            print()
            
        except Exception as e:
            print(f"❌ ERROR {description}")
            print(f"   Input: {value} (type: {type(value).__name__})")
            print(f"   Error: {e}")
            print()
    
    print("🔍 Testing strict equality:")
    print("   const isAnomaly = result.is_anomaly === 1;")
    print()
    
    for value, expected, description in test_cases:
        # Simulate strict equality with integer
        try:
            result = value == 1
            status = "✅ PASS" if result == expected else "❌ FAIL"
            print(f"{status} {description}")
            print(f"   Input: {value} (type: {type(value).__name__})")
            print(f"   {value} === 1: {result}")
            print(f"   Expected: {expected}")
            print()
            
        except Exception as e:
            print(f"❌ ERROR {description}")
            print(f"   Input: {value} (type: {type(value).__name__})")
            print(f"   Error: {e}")
            print()
    
    if all_passed:
        print("🎉 All parseFloat tests passed!")
        print("✅ The parseFloat() === 1.0 logic should work correctly.")
    else:
        print("❌ Some parseFloat tests failed!")
    
    return all_passed

if __name__ == "__main__":
    success = test_js_logic()
    if not success:
        import sys
        sys.exit(1) 