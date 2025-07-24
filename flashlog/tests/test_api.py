import os
import json
import requests
import unittest

# Load config
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'api_config.json')
with open(CONFIG_PATH, 'r') as f:
    api_config = json.load(f)
API_KEYS = api_config["API_KEYS"]
API_URL = api_config["API_URL"]

class TestAPIConfiguration(unittest.TestCase):

    def test_api_keys_count(self):
        """Test if there are API keys loaded."""
        self.assertGreater(len(API_KEYS), 0, "No API keys found in config")

    def test_api_endpoint(self):
        """Test if API_URL is correctly set."""
        self.assertTrue(API_URL.startswith('https://api.groq.com/openai/v1/'), "Invalid API_URL")

    def test_api_calls(self):
        """Test each API key with a simple request."""
        test_prompt = "Hello, this is a test."
        for key in API_KEYS:
            headers = {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": "llama3-70b-8192",
                "messages": [{"role": "user", "content": test_prompt}]
            }
            response = requests.post(API_URL, headers=headers, json=data)
            self.assertEqual(response.status_code, 200, f"API call failed for key: {key[:10]}...")
            self.assertIn('choices', response.json(), "Invalid response structure")

if __name__ == '__main__':
    unittest.main() 