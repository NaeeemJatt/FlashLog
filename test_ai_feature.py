#!/usr/bin/env python3
"""
Test script for AI Summarization Feature
"""

import os
import sys
from transformers import pipeline

def test_t5_model():
    """Test the T5 model directly"""
    print("🧪 Testing T5-Small Model...")
    
    try:
        # Check if model exists
        model_path = 'flashlog/models/t5-small'
        if not os.path.exists(model_path):
            print("❌ Model not found at:", model_path)
            return False
            
        print("✅ Model directory found")
        
        # Load the model
        summarizer = pipeline('summarization', model=model_path)
        print("✅ Model loaded successfully")
        
        # Test with sample log data
        test_logs = """
        Error at 2024-01-01 10:30:45 - Database connection failed.
        Warning at 2024-01-01 10:31:00 - Retrying connection.
        Error at 2024-01-01 10:32:15 - Connection timeout.
        Info at 2024-01-01 10:33:00 - Service restarted successfully.
        Warning at 2024-01-01 10:35:00 - High memory usage detected.
        Error at 2024-01-01 10:36:00 - Memory allocation failed.
        """
        
        print("📝 Testing with sample log data...")
        result = summarizer(test_logs, max_length=150, min_length=50, do_sample=False)
        summary = result[0]['summary_text']
        
        print("✅ Summary generated successfully!")
        print("📋 Generated Summary:")
        print("   " + summary)
        print(f"📊 Summary length: {len(summary)} characters")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing model: {str(e)}")
        return False

def test_flask_integration():
    """Test Flask integration"""
    print("\n🌐 Testing Flask Integration...")
    
    try:
        # Change to flashlog directory
        os.chdir('flashlog')
        
        # Import Flask app
        from app import create_app
        app = create_app()
        
        print("✅ Flask app created successfully")
        
        # Check if routes exist
        routes = [rule.rule for rule in app.url_map.iter_rules() if 'summarize' in rule.rule]
        if routes:
            print("✅ Summarization routes found:")
            for route in routes:
                print(f"   - {route}")
        else:
            print("❌ No summarization routes found")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Error testing Flask integration: {str(e)}")
        return False

def main():
    """Main test function"""
    print("🚀 AI Summarization Feature Test")
    print("=" * 50)
    
    # Test 1: T5 Model
    model_works = test_t5_model()
    
    # Test 2: Flask Integration
    flask_works = test_flask_integration()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"   T5 Model: {'✅ PASS' if model_works else '❌ FAIL'}")
    print(f"   Flask Integration: {'✅ PASS' if flask_works else '❌ FAIL'}")
    
    if model_works and flask_works:
        print("\n🎉 AI Feature is FULLY FUNCTIONAL!")
        print("   You can now:")
        print("   1. Start the Flask app: cd flashlog && python run.py")
        print("   2. Visit: http://localhost:5000/summarize-ui")
        print("   3. Use the AI summarization feature")
    else:
        print("\n⚠️  Some issues detected. Please check the errors above.")
    
    return model_works and flask_works

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 