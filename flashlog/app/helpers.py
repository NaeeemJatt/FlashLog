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
    Build a detailed prompt for the LLM to classify anomaly types, severity, and count.
    """
    if not anomalies:
        return "No anomalies provided."
    if isinstance(anomalies[0], dict):
        anomaly_text = "\n".join([str(a) for a in anomalies])
    else:
        anomaly_text = "\n".join(anomalies)
    prompt = (
        "You are a cybersecurity expert. Analyze the following log anomalies and provide a structured summary.\n\n"
        "For each unique anomaly type, return:\n"
        "- The anomaly type (as a short label)\n"
        "- The severity (Critical, High, Medium, Low)\n"
        "- The count of occurrences\n\n"
        "Format your response as a JSON array, where each item has 'type', 'severity', and 'count'.\n\n"
        "Anomalies:\n"
        f"{anomaly_text}\n\n"
        "Example response:\n"
        '[{"type": "SQL Injection", "severity": "Critical", "count": 3}, {"type": "Brute Force", "severity": "High", "count": 2}]'
    )
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
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    prompt = build_anomaly_prompt(list(anomaly_chunk))
    data = {
        "model": "llama-3.3-70b-versatile",
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
                print(f"[WARN] Rate limit hit for key {api_key}. Throttling...")
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
            response.raise_for_status()
            print(f"[INFO] API key {api_key} used. Response time: {elapsed:.2f}s")
            reply = response.json()["choices"][0]["message"]["content"]
            try:
                result = json.loads(reply)
            except Exception:
                result = reply
            return result
        except Exception as e:
            print(f"[ERROR] API key {api_key} attempt {attempt+1} failed: {e}")
            time.sleep(2 ** attempt)
    return []  # Return empty if all retries fail


def classify_all_anomalies(anomalies):
    """
    Classify all anomalies in parallel using 6 API keys and merge the results.
    """
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