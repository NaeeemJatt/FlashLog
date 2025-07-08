#!/usr/bin/env python3
"""
Simple test script to verify Flask app functionality
"""

import requests
import os
import tempfile

def test_flask_app():
    """Test the Flask application"""
    base_url = "http://localhost:5000"
    
    print("🧪 Testing Flask Application...")
    
    # Test 1: Check if server is running
    try:
        response = requests.get(base_url)
        print(f"✅ Server is running (Status: {response.status_code})")
    except requests.exceptions.ConnectionError:
        print("❌ Server is not running. Please start the Flask app first.")
        return False
    
    # Test 2: Test session functionality
    try:
        response = requests.get(f"{base_url}/test-session")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Session test passed: {data}")
        else:
            print(f"❌ Session test failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Session test error: {e}")
    
    # Test 3: Test debug session
    try:
        response = requests.get(f"{base_url}/debug-session")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Debug session: {data}")
        else:
            print(f"❌ Debug session failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Debug session error: {e}")
    
    # Test 4: Test analyzed-logs page
    try:
        response = requests.get(f"{base_url}/analyzed-logs")
        if response.status_code == 200:
            print("✅ Analyzed logs page accessible")
        elif response.status_code == 302:
            print("✅ Analyzed logs page redirecting (expected when no data)")
        else:
            print(f"❌ Analyzed logs page error: {response.status_code}")
    except Exception as e:
        print(f"❌ Analyzed logs page error: {e}")
    
    print("\n🎯 To test file upload:")
    print("1. Open http://localhost:5000 in your browser")
    print("2. Upload a log file")
    print("3. Check if it redirects to /analyzed-logs")
    print("4. If issues persist, check browser console for errors")
    
    return True

if __name__ == "__main__":
    test_flask_app() 