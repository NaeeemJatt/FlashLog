import sys
import os
import json

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))

from helpers import classify_all_anomalies, API_URL, API_KEYS

# Sample anomalies for testing
sample_anomalies = [
    "Critical error: SQL injection attempt detected in login form",
    "Warning: Unauthorized access to /admin endpoint from IP 192.168.1.100",
    "Error: Failed login attempt with invalid credentials",
    "High severity: Potential brute force attack on user account",
    "Medium: Suspicious file upload detected"
]

# Run classification
results = classify_all_anomalies(sample_anomalies)

# Print raw results
print('Raw Classification Results:')
print(results)

# Process results to extract JSON if possible
processed_results = []
for result in results:
    if isinstance(result, list):
        processed_results.extend(result)
    elif isinstance(result, dict):
        processed_results.append(result)
    elif isinstance(result, str):
        # Attempt to extract JSON from string response
        try:
            start_idx = result.find('[')
            end_idx = result.rfind(']') + 1
            if start_idx >= 0 and end_idx > start_idx:
                json_str = result[start_idx:end_idx]
                parsed = json.loads(json_str)
                if isinstance(parsed, list):
                    processed_results.extend(parsed)
                else:
                    print(f'WARNING: Parsed JSON is not a list: {parsed}')
            else:
                print(f'WARNING: No JSON array found in string response: {result[:100]}...')
        except json.JSONDecodeError as e:
            print(f'ERROR: Failed to parse JSON from response: {e}')
            print(f'Response snippet: {result[:100]}...')
    else:
        print(f'WARNING: Unexpected result type: {type(result)}')

# Print processed results
print('Processed Classification Results:')
print(json.dumps(processed_results, indent=2))

# Basic validation
if not isinstance(processed_results, list):
    print('ERROR: Processed results should be a list')
    sys.exit(1)

if not processed_results:
    print('ERROR: No results after processing')
    sys.exit(1)

for item in processed_results:
    if not all(key in item for key in ['type', 'severity', 'count']):
        print(f'ERROR: Missing keys in result item: {item}')
        sys.exit(1)
print('SUCCESS: All processed results have expected structure') 