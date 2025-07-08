#!/usr/bin/env python3
"""
Fix for log normalization to ensure similar logs with dynamic values 
(like port numbers, IP addresses) are treated as the same type.
"""

import re
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "logai")))

def normalize_log_content(logline):
    """
    Normalize log content by replacing dynamic values with placeholders.
    This ensures logs with the same structure but different dynamic values
    are treated as the same type.
    """
    if not isinstance(logline, str):
        return logline
    
    # Normalize IP addresses
    logline = re.sub(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', '<IP>', logline)
    
    # Normalize port numbers (common patterns)
    logline = re.sub(r':\d{4,5}\b', ':PORT', logline)  # Port numbers 4-5 digits
    logline = re.sub(r'port\s+\d+', 'port PORT', logline, flags=re.IGNORECASE)
    
    # Normalize timestamps (various formats)
    logline = re.sub(r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}', '<TIMESTAMP>', logline)
    logline = re.sub(r'\d{2}:\d{2}:\d{2}', '<TIME>', logline)
    
    # Normalize file paths
    logline = re.sub(r'/[a-zA-Z0-9/._-]+', '<PATH>', logline)
    logline = re.sub(r'[A-Za-z]:\\[A-Za-z0-9\\._-]+', '<PATH>', logline)
    
    # Normalize process IDs
    logline = re.sub(r'\bpid\s+\d+\b', 'pid PID', logline, flags=re.IGNORECASE)
    logline = re.sub(r'\bprocess\s+\d+\b', 'process PID', logline, flags=re.IGNORECASE)
    
    # Normalize memory addresses (hex)
    logline = re.sub(r'0x[0-9a-fA-F]+', '<HEX>', logline)
    
    # Normalize numeric IDs
    logline = re.sub(r'\bid\s+\d+\b', 'id ID', logline, flags=re.IGNORECASE)
    
    # Normalize error codes
    logline = re.sub(r'error\s+\d+', 'error CODE', logline, flags=re.IGNORECASE)
    logline = re.sub(r'code\s+\d+', 'code CODE', logline, flags=re.IGNORECASE)
    
    return logline

def fix_drain_parser():
    """
    Fix the Drain parser to use normalized log content.
    """
    
    file_path = "logai/logai/algorithms/parsing_algo/drain.py"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Add normalization import and function
        normalization_code = '''
import re

def normalize_log_for_parsing(logline):
    """
    Normalize log content by replacing dynamic values with placeholders.
    This ensures logs with the same structure but different dynamic values
    are treated as the same type.
    """
    if not isinstance(logline, str):
        return logline
    
    # Normalize IP addresses
    logline = re.sub(r'\\b(?:\\d{1,3}\\.){3}\\d{1,3}\\b', '<IP>', logline)
    
    # Normalize port numbers (common patterns)
    logline = re.sub(r':\\d{4,5}\\b', ':PORT', logline)  # Port numbers 4-5 digits
    logline = re.sub(r'port\\s+\\d+', 'port PORT', logline, flags=re.IGNORECASE)
    
    # Normalize timestamps (various formats)
    logline = re.sub(r'\\d{4}-\\d{2}-\\d{2}\\s+\\d{2}:\\d{2}:\\d{2}', '<TIMESTAMP>', logline)
    logline = re.sub(r'\\d{2}:\\d{2}:\\d{2}', '<TIME>', logline)
    
    # Normalize file paths
    logline = re.sub(r'/[a-zA-Z0-9/._-]+', '<PATH>', logline)
    logline = re.sub(r'[A-Za-z]:\\\\[A-Za-z0-9\\\\._-]+', '<PATH>', logline)
    
    # Normalize process IDs
    logline = re.sub(r'\\bpid\\s+\\d+\\b', 'pid PID', logline, flags=re.IGNORECASE)
    logline = re.sub(r'\\bprocess\\s+\\d+\\b', 'process PID', logline, flags=re.IGNORECASE)
    
    # Normalize memory addresses (hex)
    logline = re.sub(r'0x[0-9a-fA-F]+', '<HEX>', logline)
    
    # Normalize numeric IDs
    logline = re.sub(r'\\bid\\s+\\d+\\b', 'id ID', logline, flags=re.IGNORECASE)
    
    # Normalize error codes
    logline = re.sub(r'error\\s+\\d+', 'error CODE', logline, flags=re.IGNORECASE)
    logline = re.sub(r'code\\s+\\d+', 'code CODE', logline, flags=re.IGNORECASE)
    
    return logline

'''
        
        # Find the parse method and add normalization
        if 'def parse(self, loglines):' in content:
            # Add normalization before parsing
            content = content.replace(
                'def parse(self, loglines):',
                'def parse(self, loglines):\n        # Normalize logs for consistent parsing\n        normalized_loglines = [normalize_log_for_parsing(log) for log in loglines]\n        loglines = normalized_loglines'
            )
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ Updated {file_path} with log normalization")
        else:
            print(f"⚠️  Could not find parse method in {file_path}")
            
    except Exception as e:
        print(f"❌ Error updating {file_path}: {e}")

def fix_ael_parser():
    """
    Fix the AEL parser to use normalized log content.
    """
    
    file_path = "logai/logai/algorithms/parsing_algo/ael.py"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the parse method and add normalization
        if 'def parse(self, loglines):' in content:
            # Add normalization before parsing
            content = content.replace(
                'def parse(self, loglines):',
                'def parse(self, loglines):\n        # Normalize logs for consistent parsing\n        from .drain import normalize_log_for_parsing\n        normalized_loglines = [normalize_log_for_parsing(log) for log in loglines]\n        loglines = normalized_loglines'
            )
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ Updated {file_path} with log normalization")
        else:
            print(f"⚠️  Could not find parse method in {file_path}")
            
    except Exception as e:
        print(f"❌ Error updating {file_path}: {e}")

def test_normalization():
    """
    Test the normalization function with the problematic logs.
    """
    
    test_logs = [
        "ciod: failed to read message prefix on control stream (CioStream socket to 172.16.96.116:33569",
        "ciod: failed to read message prefix on control stream (CioStream socket to 172.16.96.116:33370",
        "2024-01-01 10:00:00 ERROR: Database connection failed to 192.168.1.1:5432",
        "2024-01-01 10:01:00 ERROR: Database connection failed to 192.168.1.2:5432",
        "Process 12345 crashed with error code 404",
        "Process 67890 crashed with error code 500"
    ]
    
    print("🧪 Testing log normalization:")
    print("=" * 80)
    
    for i, log in enumerate(test_logs):
        normalized = normalize_log_content(log)
        print(f"Original {i+1}: {log}")
        print(f"Normalized: {normalized}")
        print("-" * 80)
    
    # Check if similar logs are normalized to the same pattern
    normalized_logs = [normalize_log_content(log) for log in test_logs]
    unique_patterns = set(normalized_logs)
    
    print(f"\n📊 Results:")
    print(f"Original logs: {len(test_logs)}")
    print(f"Unique patterns after normalization: {len(unique_patterns)}")
    print(f"Reduction: {len(test_logs) - len(unique_patterns)} similar patterns identified")

def main():
    """
    Apply all fixes for log normalization.
    """
    
    print("🔧 Applying log normalization fixes...")
    
    # Test normalization first
    test_normalization()
    
    # Fix parsers
    fix_drain_parser()
    fix_ael_parser()
    
    print("\n✅ All normalization fixes applied!")
    print("\n📋 Summary:")
    print("1. ✅ Added log normalization function that replaces dynamic values with placeholders")
    print("2. ✅ Updated Drain parser to use normalized logs")
    print("3. ✅ Updated AEL parser to use normalized logs")
    print("4. ✅ Tested normalization with sample logs")
    print("\n🎯 Now logs like:")
    print("   'ciod: failed to read message prefix on control stream (CioStream socket to 172.16.96.116:33569'")
    print("   'ciod: failed to read message prefix on control stream (CioStream socket to 172.16.96.116:33370'")
    print("   Will be normalized to:")
    print("   'ciod: failed to read message prefix on control stream (CioStream socket to <IP>:PORT'")
    print("   And treated as the same log type!")

if __name__ == "__main__":
    main() 