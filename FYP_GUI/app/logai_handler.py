import pandas as pd
from datetime import datetime
from logai.applications.log_anomaly_detection import LogAnomalyDetection
from logai.applications.application_interfaces import WorkFlowConfig
from elasticsearch import Elasticsearch
import os
import uuid

def send_to_elasticsearch(index_name, result_list):
    try:
        es = Elasticsearch("http://localhost:9200")
        # Test connection
        if not es.ping():
            print("⚠️  Elasticsearch is not running. Skipping Elasticsearch upload.")
            return
            
        for _, result in result_list.iterrows():
            doc = {
                "log_line": result.get("logline", ""),
                "anomaly": result.get("is_anomaly", False),
                "score": float(result.get("is_anomaly", False)),
                "timestamp": result.get("timestamp", datetime.utcnow().isoformat())
            }
            es.index(index=index_name, document=doc)
        print("✅ Data successfully sent to Elasticsearch")
    except Exception as e:
        print(f"⚠️  Elasticsearch connection failed: {str(e)}")
        print("📝 Continuing without Elasticsearch upload...")

def preprocess_log(filepath):
    filename = os.path.basename(filepath).lower()

    # Convert TXT to CSV if needed
    if filename.endswith(".txt"):
        with open(filepath, "r") as f:
            lines = f.readlines()
        df = pd.DataFrame(lines, columns=["logline"])
        df["timestamp"] = datetime.utcnow().isoformat()
        filepath = filepath.replace(".txt", ".csv")
        df.to_csv(filepath, index=False)
    else:
        df = pd.read_csv(filepath)

    # Normalize columns
    df.columns = [col.strip().lower() for col in df.columns]

    # Auto-detect log column
    for candidate in ["logline", "message", "log", "content"]:
        if candidate in df.columns:
            df.rename(columns={candidate: "logline"}, inplace=True)
            break

    if "logline" not in df.columns:
        raise KeyError("❌ Could not find a log column (e.g., 'logline', 'message') in uploaded file.")

    if "timestamp" not in df.columns:
        df["timestamp"] = datetime.utcnow().isoformat()

    df.dropna(subset=["logline"], inplace=True)

    cleaned_path = filepath.replace(".csv", "_cleaned.csv")
    df.to_csv(cleaned_path, index=False)
    return cleaned_path, "timestamp" in df.columns

def process_log_file(filepath, parser_algo, model_type, index_name):
    cleaned_path, has_timestamp = preprocess_log(filepath)

    dimensions = {
        "body": ["logline"]
    }
    if has_timestamp:
        dimensions["timestamp"] = ["timestamp"]

    config = WorkFlowConfig.from_dict({
        "data_loader_config": {
            "filepath": cleaned_path,
            "dimensions": dimensions
        },
        "preprocessor_config": {
            "custom_delimiters_regex": []
        },
        "log_parser_config": {
            "parsing_algorithm": parser_algo
        },
        "log_vectorizer_config": {
            "algo_name": "tfidf"
        },
        "categorical_encoder_config": {
            "encoding_type": "onehot"
        },
        "feature_extractor_config": {
            "feature_type": "log_vector",
            "window_size": 5,
            "embedding_method": "tfidf"
        },
        "anomaly_detection_config": {
            "model_type": model_type
        }
    })

    detector = LogAnomalyDetection(config)
    detector.execute()
    results = detector.results

    # Save results as CSV
    result_filename = f"anomaly_results_{uuid.uuid4().hex[:8]}.csv"
    result_path = os.path.join("uploads", result_filename)
    results.to_csv(result_path, index=False)

    send_to_elasticsearch(index_name, results)
    return results, result_path
