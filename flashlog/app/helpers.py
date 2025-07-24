import os
import glob
import pandas as pd
import requests
import numpy as np
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

# Load API keys and endpoint from api_config.json
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'api_config.json')
with open(CONFIG_PATH, 'r') as f:
    api_config = json.load(f)
API_KEYS = api_config["API_KEYS"]
API_URL = api_config["API_URL"]

# print("Loaded API KEYS:", API_KEYS)
# print("Loaded API URL:", API_URL)


def compute_dashboard_metrics():
    """Compute dashboard metrics from all previous analysis results"""
    uploads_dir = 'uploads'
    anomaly_files = glob.glob(os.path.join(uploads_dir, 'anomaly_results_*.csv'))
    uploads_abs = os.path.abspath(uploads_dir)
    total_logs = 0
    total_anomalies = 0
    total_processing_time = 0
    file_count = 0
    processing_times = []
    for file_path in anomaly_files:
        abs_path = os.path.abspath(file_path)
        if not abs_path.startswith(uploads_abs):
            continue
        try:
            df = pd.read_csv(abs_path)
            if not df.empty:
                total_logs += len(df)
                if 'is_anomaly' in df.columns:
                    total_anomalies += df['is_anomaly'].sum()
                if 'processing_time_seconds' in df.columns:
                    try:
                        processing_times_col = pd.to_numeric(df['processing_time_seconds'], errors='coerce')
                        processing_times_col = processing_times_col.dropna()
                        if len(processing_times_col) > 0:
                            processing_time = processing_times_col.iloc[0]
                            processing_times.append(processing_time)
                            total_processing_time += processing_time
                    except Exception as e:
                        print(f"Error processing processing_time_seconds in compute_dashboard_metrics: {e}")
                        pass
                file_count += 1
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
    success_rate = ((total_logs - total_anomalies) / total_logs * 100) if total_logs > 0 else 0
    if processing_times:
        avg_processing_time = sum(processing_times) / len(processing_times)
    else:
        avg_processing_time = 2.4
    if file_count > 0:
        growth_rate = min(15.1, max(-10, (file_count - 1) * 5))
    else:
        growth_rate = 0
    return {
        'total_logs': total_logs,
        'total_anomalies': total_anomalies,
        'success_rate': round(success_rate, 1),
        'avg_processing_time': round(avg_processing_time, 1),
        'growth_rate': growth_rate,
        'files_processed': file_count
    }


def build_anomaly_prompt(anomalies):
    """
    Build a prompt for the external API to classify log anomalies.
    """
    total_anomalies = len(anomalies)
    prompt = (
        "You are an expert in log analysis and anomaly detection. "
        "I have a list of log anomalies from a system, and I need you to analyze them and classify each anomaly into distinct types. "
        "For each type of anomaly, provide a severity level (Critical, High, Medium, Low) and the count of how many times this type appears in the provided logs. "
        "Please respond ONLY with a JSON array of objects, where each object has the following structure: "
        "{'type': string, 'severity': string, 'count': integer}. "
        "Do not include any explanatory text or additional formatting outside the JSON array. "
        "Ensure that the sum of the 'count' values in your response equals the total number of anomalies provided (" + str(total_anomalies) + "), "
        "so that every anomaly is accounted for in one of the types. "
        "If some anomalies cannot be classified into a specific type, include them under a type labeled 'Unclassified' with an appropriate severity. "
        "If there are no anomalies to classify, return an empty JSON array []. "
        "Here are the log anomalies for analysis (total: " + str(total_anomalies) + "):\n\n"
    )
    for i, anomaly in enumerate(anomalies, 1):
        log_line = anomaly.get('logline', str(anomaly))
        prompt += f"Anomaly {i}: {log_line}\n"
    prompt += "\nPlease classify these anomalies and return the result as a JSON array, ensuring the sum of counts matches the total (" + str(total_anomalies) + ")."
    return prompt


def split_anomalies(anomalies, n_chunks):
    """
    Split anomalies into n roughly equal chunks for parallel processing.
    """
    return np.array_split(anomalies, n_chunks)


def classify_anomalies_worker(anomaly_chunk, api_key, api_url, max_retries=3):
    """
    Send a chunk of anomalies to the external API using the assigned API key.
    Handles retries, rate limits, and returns structured results.
    """
    if not anomaly_chunk or len(anomaly_chunk) == 0:
        print(f"[DEBUG] Empty chunk for key {api_key[:10]}..., returning empty results.")
        return []
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    prompt = build_anomaly_prompt(list(anomaly_chunk))
    data = {
        "model": "llama3-70b-8192",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }
    for attempt in range(max_retries):
        try:
            start = time.time()
            response = requests.post(api_url, headers=headers, json=data, timeout=30)
            elapsed = time.time() - start
            if response.status_code == 429:
                print(f"[WARN] Rate limit hit for key {api_key[:10]}.... Throttling...")
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
            response.raise_for_status()
            print(f"[INFO] API key {api_key[:10]}... used. Response time: {elapsed:.2f}s")
            # Get the raw response content
            reply = response.json()["choices"][0]["message"]["content"]
            # Log a snippet of the raw response for debugging
            print(f"[DEBUG] Raw response snippet for key {api_key[:10]}...: {reply[:100] if reply else 'Empty response'}...")
            # Check if the response looks like JSON (starts with { or [)
            reply = reply.strip()
            if reply and (reply[0] == '{' or reply[0] == '['):
                # Attempt to parse JSON
                try:
                    start_idx = reply.find('[')
                    end_idx = reply.rfind(']') + 1
                    if start_idx >= 0 and end_idx > start_idx:
                        json_str = reply[start_idx:end_idx]
                        result = json.loads(json_str)
                        if not isinstance(result, list):
                            print(f"[WARN] Parsed JSON is not a list for key {api_key[:10]}...")
                            result = []
                    else:
                        # Try parsing the entire reply as JSON if no array is found
                        result = json.loads(reply)
                        if not isinstance(result, list):
                            print(f"[WARN] Full JSON parse is not a list for key {api_key[:10]}...")
                            result = []
                except json.JSONDecodeError as e:
                    print(f"[ERROR] JSON parse failed for key {api_key[:10]}...: {e}")
                    # Fallback to text extraction if JSON parsing fails
                    result = extract_anomalies_from_text(reply)
            else:
                # Response is likely plain text, extract data directly
                print(f"[DEBUG] Response for key {api_key[:10]}... is plain text, attempting text extraction.")
                result = extract_anomalies_from_text(reply)
            return result
        except Exception as e:
            print(f"[ERROR] API key {api_key[:10]}... attempt {attempt+1} failed: {e}")
            time.sleep(2 ** attempt)
    return []  # Return empty if all retries fail


def extract_anomalies_from_text(text):
    """
    Fallback method to extract anomaly data from plain text responses if JSON parsing fails.
    Looks for patterns like 'type', 'severity', 'count' in the text.
    """
    import re
    result = []
    # Simple pattern to look for anomaly descriptions in text
    pattern = r'(type|anomaly)[^:]*:.*?(\w+[^,.;]*)(?:,|\.|\s|$)|severity[^:]*:.*?(\w+[^,.;]*)(?:,|\.|\s|$)|count[^:]*:.*?(\d+)(?:,|\.|\s|$)'
    matches = re.findall(pattern, text, re.IGNORECASE)
    if matches:
        current_type = None
        current_severity = None
        current_count = None
        for match in matches:
            if match[1].strip():
                current_type = match[1].strip()
            elif match[2].strip():
                current_severity = match[2].strip()
            elif match[3].strip():
                current_count = int(match[3].strip())
            if current_type and current_severity and current_count is not None:
                result.append({
                    'type': current_type,
                    'severity': current_severity,
                    'count': current_count
                })
                current_type = None
                current_severity = None
                current_count = None
    if not result:
        print("[DEBUG] No anomaly data extracted from plain text response.")
    else:
        print(f"[DEBUG] Extracted {len(result)} anomalies from plain text response.")
    return result


def classify_all_anomalies(anomalies):
    """
    Classify all anomalies in parallel using 6 API keys and merge the results.
    """
    if not anomalies or len(anomalies) == 0:
        print("[DEBUG] Empty anomalies list passed to classify_all_anomalies, returning empty results.")
        return []
    n_keys = len(API_KEYS)
    anomaly_chunks = split_anomalies(anomalies, n_keys)
    results = []
    with ThreadPoolExecutor(max_workers=n_keys) as executor:
        futures = [
            executor.submit(classify_anomalies_worker, list(chunk), API_KEYS[i], API_URL)
            for i, chunk in enumerate(anomaly_chunks)
        ]
        for future in as_completed(futures):
            result = future.result()
            if isinstance(result, list):
                results.extend(result)
            else:
                results.append(result)
    return results 