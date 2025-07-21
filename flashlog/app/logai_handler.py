import pandas as pd
from datetime import datetime
import time
from logai.applications.log_anomaly_detection import LogAnomalyDetection
from logai.applications.application_interfaces import WorkFlowConfig
from elasticsearch import Elasticsearch
import os
import uuid
import logging

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
    
    # Check if file is actually a CSV or just a log file with .csv extension
    def is_actual_csv(filepath):
        try:
            # Try to read first few lines to see if it's properly formatted CSV
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                first_line = f.readline().strip()
                if not first_line:
                    return False
                
                # Check if it has comma separators (basic check)
                comma_count = first_line.count(',')
                if comma_count == 0:
                    return False
                
                # For files with Date and Time columns, treat as CSV regardless of comma consistency
                # since quoted fields can have varying comma counts
                if 'Date' in first_line and 'Time' in first_line:
                    return True
                
                # Read a few more lines to check consistency (only for non-Date/Time files)
                for i in range(min(5, 10)):
                    line = f.readline().strip()
                    if not line:
                        break
                    line_comma_count = line.count(',')
                    if line_comma_count != comma_count:
                        return False
                return True
        except Exception as e:
            return False

    # Handle different file types
    is_csv = is_actual_csv(filepath)
    if filename.endswith(".txt") or filename.endswith(".log") or (filename.endswith(".csv") and not is_csv):
        # Treat as unstructured log file
        try:
            with open(filepath, "r", encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            # Clean up lines and remove empty ones
            cleaned_lines = []
            for line in lines:
                line = line.strip()
                if line:  # Only add non-empty lines
                    cleaned_lines.append(line)
            
            if not cleaned_lines:
                raise ValueError("❌ File appears to be empty or contains no valid log entries.")
            
            df = pd.DataFrame({"logline": cleaned_lines})
            df["timestamp"] = pd.Timestamp.now()
            
        except Exception as e:
            logging.error(f"Error reading log file {filepath}: {str(e)}", exc_info=True)
            raise ValueError("Error reading log file. Please check the file format and try again.")
            
    else:
        # Handle as proper CSV file
        try:
            chunks = pd.read_csv(filepath, encoding='utf-8', on_bad_lines='skip', chunksize=10000)
            df_list = []
            for chunk in chunks:
                # Apply normalizations and append to df_list
                chunk.columns = [col.strip().lower() for col in chunk.columns]
                
                # Auto-detect log column
                for candidate in ["logline", "message", "log", "content"]:
                    if candidate in chunk.columns:
                        chunk.rename(columns={candidate: "logline"}, inplace=True)
                        break

                if "logline" not in chunk.columns:
                    raise KeyError("❌ Could not find a log column (e.g., 'logline', 'message') in uploaded file.")

                # Auto-detect timestamp column (handle different case variations, now all lowercased)
                timestamp_found = False
                # If both Date and Time columns exist, merge them into a timestamp
                if 'date' in chunk.columns and 'time' in chunk.columns:
                    print("🔧 Merging Date and Time columns into timestamp...")
                    # Clean the Time column - remove quotes and handle comma in milliseconds
                    chunk['time'] = chunk['time'].astype(str).str.replace('"', '').str.replace(',', '.')
                    chunk['timestamp'] = chunk['date'].astype(str) + ' ' + chunk['time'].astype(str)
                    timestamp_found = True
                    print("✅ Created timestamp column from Date and Time")
                    # Parse using the correct format - be more lenient
                    try:
                        chunk['timestamp'] = pd.to_datetime(chunk['timestamp'], format='%Y-%m-%d %H:%M:%S.%f', errors='coerce')
                        failed = chunk['timestamp'].isna().sum()
                        if failed > 0:
                            print(f"⚠️  {failed} timestamp conversions failed, but keeping rows with current timestamp.")
                            # Instead of dropping, fill failed conversions with current time
                            chunk['timestamp'] = chunk['timestamp'].fillna(pd.Timestamp.now())
                        print(f"✅ Timestamp column converted to datetime format with custom format")
                    except Exception as e:
                        logging.error(f"Timestamp conversion failed for file {filepath}: {e}", exc_info=True)
                        print("🔧 Using current timestamp for all rows")
                        chunk['timestamp'] = pd.Timestamp.now()
                else:
                    for timestamp_candidate in ["timestamp", "time", "date", "datetime"]:
                        if timestamp_candidate in chunk.columns:
                            chunk.rename(columns={timestamp_candidate: "timestamp"}, inplace=True)
                            timestamp_found = True
                            print(f"✅ Found timestamp column: {timestamp_candidate} -> timestamp")
                            break
    
                if not timestamp_found:
                    print("⚠️  No timestamp column found, proceeding without timestamps.")
                else:
                    # Robustly convert timestamp column to datetime - be more lenient
                    try:
                        chunk["timestamp"] = pd.to_datetime(chunk["timestamp"], errors='coerce')
                        # Instead of dropping failed conversions, fill with current time
                        failed = chunk["timestamp"].isna().sum()
                        if failed > 0:
                            print(f"⚠️  {failed} timestamp conversions failed, filling with current timestamp.")
                            chunk["timestamp"] = chunk["timestamp"].fillna(pd.Timestamp.now())
                        print(f"✅ Timestamp column converted to datetime format")
                    except Exception as e:
                        logging.error(f"Timestamp conversion failed for file {filepath}: {e}", exc_info=True)
                        print("🔧 Using current timestamp for all rows")
                        chunk["timestamp"] = pd.Timestamp.now()

                # Clean up loglines - be very lenient with cleaning
                chunk.dropna(subset=["logline"], inplace=True)
                chunk = chunk[chunk["logline"].astype(str).str.strip() != ""]  # Remove empty strings
    
                # For Android logs, be very lenient - only remove completely empty lines
                chunk = chunk[chunk["logline"].astype(str).str.strip().str.len() > 0]  # Keep any non-empty lines
    
                # For Android logs, also check if we have meaningful content
                if len(chunk) > 0:
                    # Check if we have any lines with typical log patterns
                    log_patterns = ['error', 'warning', 'info', 'debug', 'exception', 'failed', 'success', 'android', 'system', 'app', 'service', 'log', 'event', 'activity']
                    has_log_patterns = chunk["logline"].astype(str).str.lower().str.contains('|'.join(log_patterns)).any()
        
                    if not has_log_patterns:
                        # If no typical log patterns, just keep all non-empty content
                        non_empty_content = chunk[chunk["logline"].astype(str).str.strip().str.len() > 0]
                        if len(non_empty_content) == 0:
                            raise ValueError("❌ No valid log entries found after cleaning.")
                        else:
                            chunk = non_empty_content
                            print(f"⚠️  No typical log patterns found, but keeping {len(chunk)} non-empty entries")
                else:
                    raise ValueError("❌ No valid log entries found after cleaning.")
                df_list.append(chunk)
            df = pd.concat(df_list) if df_list else pd.DataFrame()
        except Exception as e2:
            logging.error(f"Error reading file {filepath}: {str(e2)}", exc_info=True)
            raise ValueError("Error reading file. Please check the file format and try again.")

    cleaned_path = filepath.replace(".csv", "_cleaned.csv").replace(".txt", "_cleaned.csv").replace(".log", "_cleaned.csv")
    df.to_csv(cleaned_path, index=False)
    # Check for timestamp column after normalization
    return cleaned_path, "timestamp" in df.columns

def process_log_file(filepath, parser_algo, model_type, index_name):
    start_time = time.time()
    
    cleaned_path, has_timestamp = preprocess_log(filepath)

    # Load the cleaned data and ensure timestamp is in datetime format
    df = pd.read_csv(cleaned_path)
    if has_timestamp and 'timestamp' in df.columns:
        print(f"🔧 Converting timestamp column to datetime format...")
        try:
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            # Fill any failed conversions with current time
            if df['timestamp'].isna().any():
                print("⚠️  Some timestamp conversions failed, filling with current time")
                df['timestamp'] = df['timestamp'].fillna(pd.Timestamp.now())
            print(f"✅ Timestamp column converted to datetime format")
        except Exception as e:
            logging.error(f"Timestamp conversion failed for file {filepath}: {e}", exc_info=True)
            print("🔧 Using current time as fallback")
            df['timestamp'] = pd.Timestamp.now()
        # Save the updated DataFrame with proper datetime format
        df.to_csv(cleaned_path, index=False)

    dimensions = {
        "body": ["logline"]
    }
    if has_timestamp:
        dimensions["timestamp"] = ["timestamp"]

    config = WorkFlowConfig.from_dict({
        "data_loader_config": {
            "filepath": cleaned_path,
            "dimensions": dimensions,
            "infer_datetime": True,
            "datetime_format": None  # Let pandas auto-detect the format
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
            "max_feature_len": 100
        },
        "anomaly_detection_config": {
            "algo_name": model_type,
            "algo_params": {
                "nu": 0.05 if model_type == "one_class_svm" else 0.1  # More conservative for One-Class SVM
            }
        }
    })

    detector = LogAnomalyDetection(config)
    
    # All algorithms now work with the enhanced timestamp handling
    if has_timestamp:
        print(f"✅ Timestamp column detected and will be used for analysis")
    else:
        print(f"⚠️  No timestamp column found, using log sequence for analysis")
    
    detector.execute()
    results = detector.results
    
    # Debug: Check anomaly distribution
    print(f"Debug: Total logs processed: {len(results)}")
    if 'is_anomaly' in results.columns:
        anomaly_count = results['is_anomaly'].sum()
        normal_count = len(results) - anomaly_count
        print(f"Debug: Anomalies detected: {anomaly_count}")
        print(f"Debug: Normal logs: {normal_count}")
        print(f"Debug: Anomaly percentage: {(anomaly_count/len(results)*100):.2f}%")
        
        # If all logs are marked as anomalies, this might indicate an issue
        if anomaly_count == len(results):
            print("⚠️  Warning: ALL logs marked as anomalies. This indicates a model issue.")
            print("🔍 This could be due to model parameters or data characteristics")
            print("🔍 Consider trying different algorithms or adjusting parameters")
            print("🔍 Current results will be preserved as-is")
        
        # If too many anomalies detected (but not all), just warn
        elif anomaly_count > len(results) * 0.8:  # More than 80% anomalies
            print(f"⚠️  Warning: High anomaly rate detected ({anomaly_count/len(results)*100:.1f}%).")
            print("🔍 This might be normal for your dataset, but consider trying different algorithms.")
    
    # Calculate processing time
    processing_time = time.time() - start_time
    print(f"⏱️  Processing completed in {processing_time:.2f} seconds")
    
    # Send to Elasticsearch if available
    try:
        send_to_elasticsearch(index_name, results)
    except Exception as e:
        print(f"⚠️  Elasticsearch upload failed: {str(e)}")
    
    return results, processing_time


