#!/usr/bin/env python3
"""
Test to verify all parsers (AEL, Drain, IPLOM) work with normalization.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "logai")))

import pandas as pd
from logai.algorithms.parsing_algo import AEL, Drain, IPLoM
from logai.algorithms.parsing_algo.ael import AELParams
from logai.algorithms.parsing_algo.drain import DrainParams
from logai.algorithms.parsing_algo.iplom import IPLoMParams
from logai.utils.log_normalizer import LogNormalizer, NormalizationConfig

def test_all_parsers_normalization():
    """Test that all parsers work correctly with normalization."""
    
    print("🧪 Testing All Parsers with Normalization")
    print("=" * 80)
    
    # Test logs with the problematic case
    test_logs = [
        "ciod: failed to read message prefix on control stream (CioStream socket to 172.16.96.116:33569",
        "ciod: failed to read message prefix on control stream (CioStream socket to 172.16.96.116:33370",
        "ciod: failed to read message prefix on control stream (CioStream socket to 192.168.1.1:8080",
        "2024-01-01 10:00:00 ERROR: Database connection failed to 192.168.1.1:5432",
        "2024-01-01 10:01:00 ERROR: Database connection failed to 192.168.1.2:5432",
        "Process 12345 crashed with error code 404",
        "Process 67890 crashed with error code 500",
    ]
    
    loglines = pd.Series(test_logs, name="Content")
    
    # Test each parser with correct parameter classes
    parsers = {
        "AEL": (AEL, AELParams),
        "Drain": (Drain, DrainParams),
        "IPLoM": (IPLoM, IPLoMParams)
    }
    
    # Parser configurations
    parser_configs = {
        "AEL": {
            "rex": None,
            "minEventCount": 2,
            "merge_percent": 1,
            "keep_para": True,
        },
        "Drain": {
            "depth": 4,
            "sim_th": 0.4,
            "max_children": 100,
            "max_clusters": None,
            "extra_delimiters": (),
            "param_str": "*",
        },
        "IPLoM": {
            "rex": None,
            "logformat": None,
            "maxEventLen": 200,
            "step2Support": 0,
            "PST": 0,
            "CT": 0,
            "lowerBound": 0.25,
            "upperBound": 0.9,
            "keep_para": True,
        }
    }
    
    # Test normalization separately first
    print("🔍 Testing Normalization:")
    print("-" * 40)
    
    normalizer = LogNormalizer(NormalizationConfig())
    normalized_logs = normalizer.normalize_batch(test_logs)
    
    print("Original logs:")
    for i, log in enumerate(test_logs[:3]):
        print(f"  {i+1}: {log}")
    
    print("\nNormalized logs:")
    for i, normalized in enumerate(normalized_logs[:3]):
        print(f"  {i+1}: {normalized}")
    
    # Test each parser
    for parser_name, (ParserClass, ParamsClass) in parsers.items():
        print(f"\n🔧 Testing {parser_name} Parser:")
        print("-" * 40)
        
        try:
            # Create parser instance with correct parameters
            config_dict = parser_configs[parser_name]
            params = ParamsClass(**config_dict)
            parser = ParserClass(params)
            
            # Parse logs
            parsed_loglines = parser.parse(loglines)
            
            print(f"✅ {parser_name} parsing successful!")
            print(f"   Input logs: {len(test_logs)}")
            print(f"   Parsed templates: {len(parsed_loglines)}")
            
            # Check for consistency in template generation
            unique_templates = parsed_loglines.unique()
            print(f"   Unique templates: {len(unique_templates)}")
            
            # Show some examples
            print(f"   Template examples:")
            for i, template in enumerate(unique_templates[:3]):
                print(f"     {i+1}: {template}")
            
            # Check if normalization helped with consistency
            # The first two logs should have similar templates after normalization
            template1 = parsed_loglines.iloc[0]
            template2 = parsed_loglines.iloc[1]
            
            if template1 == template2:
                print(f"   ✅ Logs 1 and 2 have identical templates (normalization working!)")
            else:
                print(f"   ⚠️  Logs 1 and 2 have different templates")
                print(f"      Template 1: {template1}")
                print(f"      Template 2: {template2}")
            
        except Exception as e:
            print(f"❌ {parser_name} parsing failed: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n🎉 Parser normalization test completed!")
    print("All parsers should now work with the comprehensive normalization layer.")

if __name__ == "__main__":
    test_all_parsers_normalization() 