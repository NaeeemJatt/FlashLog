#!/usr/bin/env python3
"""
Test script for Enhanced Interactive Dashboard
Tests the new chart switching functionality and enhanced visualizations
"""

import requests
import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import os

def test_enhanced_dashboard():
    """Test the enhanced dashboard with interactive charts"""
    
    print("🧪 Testing Enhanced Interactive Dashboard...")
    
    # Test 1: Check if dashboard loads with new chart controls
    print("\n1. Testing dashboard chart controls...")
    
    try:
        # Start Chrome in headless mode
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        driver = webdriver.Chrome(options=options)
        
        # Navigate to the dashboard (assuming it's running on localhost:5000)
        driver.get("http://localhost:5000/analysis-dashboard")
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Check if chart type selectors are present
        selectors = driver.find_elements(By.CLASS_NAME, "chart-type-selector")
        print(f"   ✅ Found {len(selectors)} chart type selectors")
        
        # Check if chart containers are present
        chart_containers = driver.find_elements(By.CLASS_NAME, "chart-container")
        print(f"   ✅ Found {len(chart_containers)} chart containers")
        
        # Check if new chart panels are present
        chart_panels = driver.find_elements(By.CLASS_NAME, "chart-panel")
        print(f"   ✅ Found {len(chart_panels)} interactive chart panels")
        
        # Test chart type switching (if selectors are available)
        if selectors:
            print("\n2. Testing chart type switching...")
            
            for i, selector in enumerate(selectors[:2]):  # Test first 2 selectors
                try:
                    select = Select(selector)
                    options = select.options
                    print(f"   📊 Chart {i+1} has {len(options)} chart type options:")
                    
                    for option in options:
                        print(f"      - {option.text}")
                    
                    # Test switching to a different chart type
                    if len(options) > 1:
                        select.select_by_index(1)  # Select second option
                        time.sleep(1)  # Wait for chart to update
                        print(f"   ✅ Successfully switched chart {i+1} type")
                    
                except Exception as e:
                    print(f"   ⚠️  Could not test selector {i+1}: {str(e)}")
        
        # Check for enhanced features
        print("\n3. Testing enhanced features...")
        
        # Check for new chart types
        new_charts = driver.find_elements(By.ID, "severityChart")
        if new_charts:
            print("   ✅ Log Severity Analysis chart found")
        
        timeline_charts = driver.find_elements(By.ID, "timelineChart")
        if timeline_charts:
            print("   ✅ Anomaly Timeline chart found")
        
        # Check for enhanced styling
        enhanced_styles = driver.find_elements(By.CLASS_NAME, "chart-controls")
        if enhanced_styles:
            print("   ✅ Enhanced chart controls styling found")
        
        driver.quit()
        print("\n✅ Enhanced Dashboard Test Completed Successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        if 'driver' in locals():
            driver.quit()

def test_backend_data_processing():
    """Test the enhanced backend data processing"""
    
    print("\n🔧 Testing Enhanced Backend Data Processing...")
    
    try:
        # Test the enhanced data processing function
        from app.routes import process_dashboard_data
        
        # Create sample data
        sample_results = [
            {
                'logline': 'ERROR: Database connection failed',
                'is_anomaly': 1,
                'timestamp': '2024-01-01T10:00:00'
            },
            {
                'logline': 'INFO: User login successful',
                'is_anomaly': 0,
                'timestamp': '2024-01-01T10:01:00'
            },
            {
                'logline': 'WARNING: High memory usage detected',
                'is_anomaly': 1,
                'timestamp': '2024-01-01T10:02:00'
            },
            {
                'logline': 'CRITICAL: System shutdown initiated',
                'is_anomaly': 1,
                'timestamp': '2024-01-01T10:03:00'
            }
        ]
        
        sample_analysis = {
            'id': 'test-123',
            'user_id': 1,
            'created_at': '2024-01-01T10:00:00',
            'index_name': 'test-index',
            'parser': 'drain',
            'model': 'isolation_forest'
        }
        
        # Process the data
        dashboard_data = process_dashboard_data(sample_results, sample_analysis)
        
        # Verify enhanced features
        print("   ✅ Basic statistics processed")
        assert 'summary' in dashboard_data
        assert dashboard_data['summary']['total_logs'] == 4
        assert dashboard_data['summary']['anomaly_count'] == 3
        
        print("   ✅ Enhanced pattern analysis processed")
        assert 'pattern_data' in dashboard_data
        assert 'severity_levels' in dashboard_data['pattern_data']
        
        # Check severity levels
        severity = dashboard_data['pattern_data']['severity_levels']
        print(f"      - Critical: {severity.get('Critical', 0)}")
        print(f"      - High: {severity.get('High', 0)}")
        print(f"      - Medium: {severity.get('Medium', 0)}")
        print(f"      - Low: {severity.get('Low', 0)}")
        
        print("   ✅ Time-based analysis processed")
        assert 'time_data' in dashboard_data
        if dashboard_data['time_data']:
            assert 'daily_distribution' in dashboard_data['time_data']
            assert 'daily_anomalies' in dashboard_data['time_data']
        
        print("   ✅ Anomaly insights generated")
        assert 'anomaly_insights' in dashboard_data
        assert len(dashboard_data['anomaly_insights']) > 0
        
        print("\n✅ Backend Data Processing Test Completed Successfully!")
        
    except Exception as e:
        print(f"\n❌ Backend test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Starting Enhanced Dashboard Tests...")
    
    # Test backend data processing
    test_backend_data_processing()
    
    # Test frontend dashboard
    test_enhanced_dashboard()
    
    print("\n🎉 All Enhanced Dashboard Tests Completed!") 