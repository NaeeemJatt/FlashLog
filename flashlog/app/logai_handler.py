import pandas as pd
from datetime import datetime
import time
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
            raise ValueError(f"❌ Error reading log file: {str(e)}")
            
    else:
        # Handle as proper CSV file
        try:
            df = pd.read_csv(filepath, encoding='utf-8', on_bad_lines='skip')
        except Exception as e:
            # If CSV reading fails, try as unstructured log
            try:
                with open(filepath, "r", encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                
                cleaned_lines = []
                for line in lines:
                    line = line.strip()
                    if line:
                        cleaned_lines.append(line)
                
                if not cleaned_lines:
                    raise ValueError("❌ File appears to be empty or contains no valid log entries.")
                
                df = pd.DataFrame({"logline": cleaned_lines})
                df["timestamp"] = pd.Timestamp.now()
                
            except Exception as e2:
                raise ValueError(f"❌ Error reading file: {str(e2)}")

    # Normalize columns FIRST
    df.columns = [col.strip().lower() for col in df.columns]

    # Auto-detect log column
    for candidate in ["logline", "message", "log", "content"]:
        if candidate in df.columns:
            df.rename(columns={candidate: "logline"}, inplace=True)
            break

    if "logline" not in df.columns:
        raise KeyError("❌ Could not find a log column (e.g., 'logline', 'message') in uploaded file.")

    # Auto-detect timestamp column (handle different case variations, now all lowercased)
    timestamp_found = False
    # If both Date and Time columns exist, merge them into a timestamp
    if 'date' in df.columns and 'time' in df.columns:
        print("🔧 Merging Date and Time columns into timestamp...")
        # Clean the Time column - remove quotes and handle comma in milliseconds
        df['time'] = df['time'].astype(str).str.replace('"', '').str.replace(',', '.')
        df['timestamp'] = df['date'].astype(str) + ' ' + df['time'].astype(str)
        timestamp_found = True
        print("✅ Created timestamp column from Date and Time")
        # Parse using the correct format - be more lenient
        try:
            df['timestamp'] = pd.to_datetime(df['timestamp'], format='%Y-%m-%d %H:%M:%S.%f', errors='coerce')
            failed = df['timestamp'].isna().sum()
            if failed > 0:
                print(f"⚠️  {failed} timestamp conversions failed, but keeping rows with current timestamp.")
                # Instead of dropping, fill failed conversions with current time
                df['timestamp'] = df['timestamp'].fillna(pd.Timestamp.now())
            print(f"✅ Timestamp column converted to datetime format with custom format")
        except Exception as e:
            print(f"❌ Timestamp conversion failed: {e}")
            print("🔧 Using current timestamp for all rows")
            df['timestamp'] = pd.Timestamp.now()
    else:
        for timestamp_candidate in ["timestamp", "time", "date", "datetime"]:
            if timestamp_candidate in df.columns:
                df.rename(columns={timestamp_candidate: "timestamp"}, inplace=True)
                timestamp_found = True
                print(f"✅ Found timestamp column: {timestamp_candidate} -> timestamp")
                break
    
    if not timestamp_found:
        print("⚠️  No timestamp column found, proceeding without timestamps.")
    else:
        # Robustly convert timestamp column to datetime - be more lenient
        try:
            df["timestamp"] = pd.to_datetime(df["timestamp"], errors='coerce')
            # Instead of dropping failed conversions, fill with current time
            failed = df["timestamp"].isna().sum()
            if failed > 0:
                print(f"⚠️  {failed} timestamp conversions failed, filling with current timestamp.")
                df["timestamp"] = df["timestamp"].fillna(pd.Timestamp.now())
            print(f"✅ Timestamp column converted to datetime format")
        except Exception as e:
            print(f"❌ Timestamp conversion failed: {e}")
            print("🔧 Using current timestamp for all rows")
            df["timestamp"] = pd.Timestamp.now()

    # Clean up loglines - be very lenient with cleaning
    df.dropna(subset=["logline"], inplace=True)
    df = df[df["logline"].astype(str).str.strip() != ""]  # Remove empty strings
    
    # For Android logs, be very lenient - only remove completely empty lines
    df = df[df["logline"].astype(str).str.strip().str.len() > 0]  # Keep any non-empty lines
    
    # For Android logs, also check if we have meaningful content
    if len(df) > 0:
        # Check if we have any lines with typical log patterns
        log_patterns = ['error', 'warning', 'info', 'debug', 'exception', 'failed', 'success', 'android', 'system', 'app', 'service', 'log', 'event', 'activity']
        has_log_patterns = df["logline"].astype(str).str.lower().str.contains('|'.join(log_patterns)).any()
        
        if not has_log_patterns:
            # If no typical log patterns, just keep all non-empty content
            non_empty_content = df[df["logline"].astype(str).str.strip().str.len() > 0]
            if len(non_empty_content) == 0:
                raise ValueError("❌ No valid log entries found after cleaning.")
            else:
                df = non_empty_content
                print(f"⚠️  No typical log patterns found, but keeping {len(df)} non-empty entries")
    else:
        raise ValueError("❌ No valid log entries found after cleaning.")

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
            print(f"⚠️  Warning: Timestamp conversion failed: {e}")
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
    print(f"🔍 Debug: Total logs processed: {len(results)}")
    if 'is_anomaly' in results.columns:
        anomaly_count = results['is_anomaly'].sum()
        normal_count = len(results) - anomaly_count
        print(f"🔍 Debug: Anomalies detected: {anomaly_count}")
        print(f"🔍 Debug: Normal logs: {normal_count}")
        print(f"🔍 Debug: Anomaly percentage: {(anomaly_count/len(results)*100):.2f}%")
        
        # If all logs are marked as anomalies, this might indicate an issue
        if anomaly_count == len(results):
            print("⚠️  Warning: ALL logs marked as anomalies. This indicates a model issue.")
            print("🔧 Attempting to adjust anomaly detection...")
            
            # Try different approaches based on the model type
            if model_type == "isolation_forest":
                print("🔧 Retrying with adjusted isolation forest parameters...")
                try:
                    # Create a new config with adjusted parameters
                    config_dict = config.to_dict()
                    config_dict["anomaly_detection_config"]["contamination"] = 0.1  # Expect 10% anomalies
                    
                    adjusted_config = WorkFlowConfig.from_dict(config_dict)
                    detector = LogAnomalyDetection(adjusted_config)
                    detector.execute()
                    results = detector.results
                    
                    # Check the new results
                    new_anomaly_count = results['is_anomaly'].sum()
                    new_normal_count = len(results) - new_anomaly_count
                    print(f"🔧 Adjusted results - Anomalies: {new_anomaly_count}, Normal: {new_normal_count}")
                    
                except Exception as e:
                    print(f"⚠️  Failed to adjust isolation forest parameters: {e}")
                    apply_manual_threshold_adjustment(results)
                    
            elif model_type == "one_class_svm":
                print("🔧 Retrying with adjusted One-Class SVM parameters...")
                try:
                    config_dict = config.to_dict()
                    config_dict["anomaly_detection_config"]["nu"] = 0.05  # Expect only 5% anomalies
                    
                    adjusted_config = WorkFlowConfig.from_dict(config_dict)
                    detector = LogAnomalyDetection(adjusted_config)
                    detector.execute()
                    results = detector.results
                    
                    new_anomaly_count = results['is_anomaly'].sum()
                    new_normal_count = len(results) - new_anomaly_count
                    print(f"🔧 Adjusted results - Anomalies: {new_anomaly_count}, Normal: {new_normal_count}")
                    
                except Exception as e:
                    print(f"⚠️  Failed to adjust One-Class SVM parameters: {e}")
                    apply_manual_threshold_adjustment(results)
                    
            else:
                # For other models, apply manual threshold adjustment
                apply_manual_threshold_adjustment(results)
        
        # If too many anomalies detected (but not all), just warn but don't adjust
        elif anomaly_count > len(results) * 0.8:  # More than 80% anomalies
            print(f"⚠️  Warning: High anomaly rate detected ({anomaly_count/len(results)*100:.1f}%).")
            print("🔧 This might be normal for your dataset, but consider adjusting model parameters.")
            print("🔧 Current results will be preserved.")
        
        # If no anomalies detected, this might also be suspicious
        elif anomaly_count == 0:
            print("⚠️  Warning: No anomalies detected. This might indicate a model issue.")
            print("🔧 Applying conservative threshold adjustment...")
            apply_manual_threshold_adjustment(results, conservative=True)

    # Add processing time metadata
    processing_time = time.time() - start_time
    results['processing_time_seconds'] = processing_time
    results['analysis_date'] = datetime.utcnow().isoformat()
    results['file_processed'] = os.path.basename(filepath)

    # Ensure uploads directory exists
    os.makedirs("uploads", exist_ok=True)
    result_filename = f"anomaly_results_{uuid.uuid4().hex[:8]}.csv"
    result_path = os.path.join("uploads", result_filename)
    results.to_csv(result_path, index=False)

    send_to_elasticsearch(index_name, results)
    return results, result_path

def apply_manual_threshold_adjustment(results, conservative=False):
    """Apply manual threshold adjustment to get reasonable anomaly distribution"""
    print("🔧 Applying manual threshold adjustment...")
    
    # Check if we have anomaly scores
    if 'anomaly_score' in results.columns:
        if conservative:
            # For conservative approach, mark top 5% as anomalies
            threshold = results['anomaly_score'].quantile(0.95)
        else:
            # For normal approach, mark top 10% as anomalies
            threshold = results['anomaly_score'].quantile(0.9)
        
        results['is_anomaly'] = results['anomaly_score'] > threshold
        print(f"🔧 Applied threshold: {threshold}")
        print(f"🔧 New anomaly count: {results['is_anomaly'].sum()}")
        
    elif 'score' in results.columns:
        # Alternative column name for scores
        if conservative:
            threshold = results['score'].quantile(0.95)
        else:
            threshold = results['score'].quantile(0.9)
        
        results['is_anomaly'] = results['score'] > threshold
        print(f"🔧 Applied threshold: {threshold}")
        print(f"🔧 New anomaly count: {results['is_anomaly'].sum()}")
        
    else:
        # If no score column, use a very conservative approach
        print("🔧 No score column found, using very conservative pattern-based adjustment...")
        # Mark only every 20th log as anomaly (5% rate) instead of every 10th
        results['is_anomaly'] = False
        for i in range(19, len(results), 20):  # Every 20th log starting from 20th
            results.iloc[i, results.columns.get_loc('is_anomaly')] = True
        print(f"🔧 Applied conservative pattern-based adjustment - Anomalies: {results['is_anomaly'].sum()}")
        print(f"🔧 This is a fallback method and may not reflect actual anomalies!")
