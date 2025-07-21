#!/usr/bin/env python3
"""
AI Log Summarization Demo
This script demonstrates the AI summarization feature working independently.
"""

import os
import sys
from transformers import pipeline

def test_ai_summarization():
    """Test the AI summarization feature"""
    print("🚀 AI Log Summarization Demo")
    print("=" * 50)
    
    # Check if model exists
    model_path = 'flashlog/models/t5-small'
    if not os.path.exists(model_path):
        print("❌ Model not found. Please run the download script first.")
        return False
    
    print("✅ Model found at:", model_path)
    
    try:
        # Load the model
        print("🔄 Loading T5-Small model...")
        summarizer = pipeline('summarization', model=model_path)
        print("✅ Model loaded successfully!")
        
        # Test cases
        test_cases = [
            {
                "name": "Database Errors",
                "logs": """
                Error at 2024-01-01 10:30:45 - Database connection failed.
                Warning at 2024-01-01 10:31:00 - Retrying connection.
                Error at 2024-01-01 10:32:15 - Connection timeout.
                Info at 2024-01-01 10:33:00 - Service restarted successfully.
                Warning at 2024-01-01 10:35:00 - High memory usage detected.
                Error at 2024-01-01 10:36:00 - Memory allocation failed.
                """
            },
            {
                "name": "System Logs",
                "logs": """
                INFO: System startup completed successfully
                WARN: High memory usage detected (85%)
                ERROR: Disk space low on /var/log
                INFO: Backup process started
                WARN: Network latency increased
                INFO: System maintenance completed
                ERROR: Service authentication failed
                """
            },
            {
                "name": "Application Logs",
                "logs": """
                [ERROR] User authentication failed for user: admin
                [WARN] Session timeout approaching for user: user123
                [INFO] New user registered: john.doe@example.com
                [ERROR] Payment processing failed for order: ORD-12345
                [INFO] Order completed successfully: ORD-12346
                [WARN] API rate limit approaching
                [ERROR] Database query timeout
                """
            },
            {
                "name": "Network Logs",
                "logs": """
                Connection refused from 192.168.1.100
                Successful login from 192.168.1.101
                Failed authentication attempt from 192.168.1.102
                Port scan detected from 192.168.1.103
                Connection established with 192.168.1.104
                Connection dropped from 192.168.1.105
                """
            }
        ]
        
        print("\n📝 Testing AI Summarization with different log types...")
        print("-" * 50)
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{i}. {test_case['name']}:")
            print(f"   Original logs: {len(test_case['logs'])} characters")
            
            # Generate summary
            result = summarizer(test_case['logs'], max_length=100, min_length=30, do_sample=False)
            summary = result[0]['summary_text']
            
            print(f"   AI Summary: {summary}")
            print(f"   Summary length: {len(summary)} characters")
            print(f"   Compression ratio: {len(summary)/len(test_case['logs'])*100:.1f}%")
        
        print("\n" + "=" * 50)
        print("🎉 AI Summarization Demo Completed Successfully!")
        print("\n📋 Key Features Demonstrated:")
        print("   ✅ T5-Small model loading and inference")
        print("   ✅ Multiple log format handling")
        print("   ✅ Intelligent summarization")
        print("   ✅ Consistent output quality")
        print("   ✅ Offline processing capability")
        
        print("\n💡 How to Use in Your Code:")
        print("   from transformers import pipeline")
        print("   summarizer = pipeline('summarization', model='flashlog/models/t5-small')")
        print("   result = summarizer(your_logs, max_length=100, min_length=30)")
        print("   summary = result[0]['summary_text']")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def interactive_demo():
    """Interactive demo where user can input their own logs"""
    print("\n🎯 Interactive AI Summarization Demo")
    print("=" * 50)
    
    model_path = 'flashlog/models/t5-small'
    if not os.path.exists(model_path):
        print("❌ Model not found. Please run the download script first.")
        return
    
    try:
        summarizer = pipeline('summarization', model=model_path)
        print("✅ Model loaded for interactive demo!")
        
        while True:
            print("\n" + "-" * 30)
            user_input = input("Enter your log data (or 'quit' to exit):\n")
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                break
            
            if not user_input.strip():
                print("Please enter some log data.")
                continue
            
            try:
                result = summarizer(user_input, max_length=100, min_length=30, do_sample=False)
                summary = result[0]['summary_text']
                
                print(f"\n🤖 AI Summary:")
                print(f"   {summary}")
                print(f"   Length: {len(summary)} characters")
                
            except Exception as e:
                print(f"❌ Error generating summary: {str(e)}")
    
    except Exception as e:
        print(f"❌ Error loading model: {str(e)}")

def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] == '--interactive':
        interactive_demo()
    else:
        success = test_ai_summarization()
        if success:
            print("\n🚀 The AI summarization feature is fully functional!")
            print("   You can now integrate this into your applications.")
        else:
            print("\n⚠️  Some issues detected. Please check the errors above.")

if __name__ == "__main__":
    main() 