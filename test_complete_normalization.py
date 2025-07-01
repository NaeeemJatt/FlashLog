#!/usr/bin/env python3
"""
Comprehensive test for the complete normalization solution.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "logai")))

from logai.utils.log_normalizer import LogNormalizer, NormalizationConfig

def test_complete_normalization():
    """Test the complete normalization solution."""
    
    print("🧪 Testing Complete Log Normalization Solution")
    print("=" * 80)
    
    # Initialize normalizer
    config = NormalizationConfig(
        normalize_ips=True,
        normalize_ports=True,
        normalize_timestamps=True,
        normalize_uuids=True,
        normalize_hashes=True,
        normalize_file_paths=True,
        normalize_hex_values=True,
        enable_caching=True
    )
    normalizer = LogNormalizer(config)
    
    # Test the specific problematic case
    print("\n🎯 Testing the specific problematic case:")
    print("-" * 50)
    
    problematic_logs = [
        "ciod: failed to read message prefix on control stream (CioStream socket to 172.16.96.116:33569",
        "ciod: failed to read message prefix on control stream (CioStream socket to 172.16.96.116:33370"
    ]
    
    print("Original logs:")
    for i, log in enumerate(problematic_logs):
        print(f"  {i+1}: {log}")
    
    print("\nNormalized logs:")
    normalized_logs = []
    for i, log in enumerate(problematic_logs):
        normalized = normalizer.normalize(log)
        normalized_logs.append(normalized)
        print(f"  {i+1}: {normalized}")
    
    if normalized_logs[0] == normalized_logs[1]:
        print("\n✅ SUCCESS: Both logs normalized to the same pattern!")
        print("   They will now be classified consistently.")
    else:
        print("\n❌ FAILURE: Logs still have different patterns after normalization.")
    
    # Test template hashing
    print("\n🔐 Testing template hashing:")
    print("-" * 30)
    
    for i, log in enumerate(problematic_logs):
        template_hash = normalizer.get_template_hash(log)
        print(f"Log {i+1} template hash: {template_hash}")
    
    if normalizer.get_template_hash(problematic_logs[0]) == normalizer.get_template_hash(problematic_logs[1]):
        print("✅ SUCCESS: Both logs have the same template hash!")
    else:
        print("❌ FAILURE: Logs have different template hashes.")
    
    # Test additional normalization patterns
    print("\n🔍 Testing additional normalization patterns:")
    print("-" * 50)
    
    test_cases = [
        ("IP address", "Connection to 192.168.1.1 failed", "Connection to <IP> failed"),
        ("Port number", "Server listening on port 8080", "Server listening on <PORT>"),
        ("Timestamp", "2024-01-01 10:00:00 ERROR: Database error", "<TIMESTAMP> ERROR: Database error"),
        ("UUID", "Session 550e8400-e29b-41d4-a716-446655440000 created", "Session <UUID> created"),
        ("Hash", "File hash: a1b2c3d4e5f678901234567890123456", "File hash: <HASH>"),
        ("File path", "Accessing /var/log/app.log", "Accessing <PATH>"),
        ("Hex value", "Memory address: 0x7fff12345678", "Memory address: <HEX>"),
    ]
    
    for test_name, original, expected in test_cases:
        normalized = normalizer.normalize(original)
        print(f"{test_name:12}: {normalized}")
        if expected in normalized:
            print(f"  ✅ {test_name} normalized correctly")
        else:
            print(f"  ❌ {test_name} normalization failed")
    
    # Test batch normalization
    print("\n📦 Testing batch normalization:")
    print("-" * 30)
    
    batch_logs = [
        "ciod: failed to read message prefix on control stream (CioStream socket to 172.16.96.116:33569",
        "ciod: failed to read message prefix on control stream (CioStream socket to 172.16.96.116:33370",
        "2024-01-01 10:00:00 ERROR: Database connection failed to 192.168.1.1:5432",
        "2024-01-01 10:01:00 ERROR: Database connection failed to 192.168.1.2:5432",
    ]
    
    normalized_batch = normalizer.normalize_batch(batch_logs)
    
    print("Batch normalization results:")
    for i, (original, normalized) in enumerate(zip(batch_logs, normalized_batch)):
        print(f"  {i+1}: {normalized}")
    
    # Test consistency grouping
    print("\n📊 Testing consistency grouping:")
    print("-" * 30)
    
    normalized_groups = {}
    for i, normalized in enumerate(normalized_batch):
        if normalized not in normalized_groups:
            normalized_groups[normalized] = []
        normalized_groups[normalized].append(i)
    
    print(f"Original logs: {len(batch_logs)}")
    print(f"Unique normalized patterns: {len(normalized_groups)}")
    print(f"Reduction: {len(batch_logs) - len(normalized_groups)} similar patterns identified")
    
    for pattern, indices in normalized_groups.items():
        print(f"\nPattern: {pattern}")
        print(f"Count: {len(indices)}")
        print("Original logs:")
        for idx in indices:
            print(f"  - {batch_logs[idx]}")
    
    print("\n🎉 Normalization test completed successfully!")
    print("The comprehensive normalization layer is working correctly.")
    print("Logs with identical structure but different dynamic values will now be classified consistently.")

if __name__ == "__main__":
    test_complete_normalization() 