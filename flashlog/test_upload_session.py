#!/usr/bin/env python3
"""
Test script to simulate file upload and check session persistence
"""

import requests
import tempfile
import os

def test_upload_and_session():
    """Test file upload and session persistence"""
    base_url = "http://localhost:5000"
    
    print("🧪 Testing file upload and session persistence...")
    
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
    
    # Create a session to maintain cookies
    session = requests.Session()
    
    # Step 1: Get the initial page to establish session
    print("1️⃣ Getting initial page...")
    response = session.get(base_url)
    print(f"   - Status: {response.status_code}")
    
    # Step 2: Upload the file
    print("2️⃣ Uploading file...")
    with open(temp_file, 'rb') as f:
        files = {'logfile': ('test.log', f, 'text/plain')}
        data = {
            'parser': 'drain',
            'model': 'isolation_forest',
            'index_name': 'test-session'
        }
        response = session.post(base_url, files=files, data=data, allow_redirects=False)
    
    print(f"   - Upload status: {response.status_code}")
    print(f"   - Location header: {response.headers.get('Location', 'None')}")
    
    # Step 3: Check if we got a redirect
    if response.status_code == 302:
        redirect_url = response.headers.get('Location')
        print(f"3️⃣ Following redirect to: {redirect_url}")
        
        # Follow the redirect
        response = session.get(f"{base_url}{redirect_url}")
        print(f"   - Redirect status: {response.status_code}")
        
        # Check if we're on the analyzed-logs page
        if 'analyzed-logs' in response.url:
            print("✅ Successfully redirected to analyzed-logs page!")
            
            # Check if the page contains results
            if 'Analysis Results' in response.text:
                print("✅ Page contains 'Analysis Results' - session data is working!")
            else:
                print("❌ Page doesn't contain 'Analysis Results' - session data may be missing")
        else:
            print(f"❌ Unexpected redirect to: {response.url}")
    else:
        print(f"❌ No redirect received, status: {response.status_code}")
        print(f"   - Response content: {response.text[:200]}...")
    
    # Step 4: Check session data via debug endpoint
    print("4️⃣ Checking session data...")
    response = session.get(f"{base_url}/debug-session")
    if response.status_code == 200:
        data = response.json()
        print(f"   - Session data: {data}")
        if data['analysis_results_count'] > 0:
            print("✅ Session contains analysis results!")
        else:
            print("❌ Session is empty - no analysis results found")
    else:
        print(f"❌ Failed to get session data: {response.status_code}")
    
    # Clean up
    os.unlink(temp_file)
    print("🧹 Cleaned up test file")

if __name__ == "__main__":
    test_upload_and_session() 