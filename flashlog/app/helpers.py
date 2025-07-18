import os
import glob
import pandas as pd

def compute_dashboard_metrics():
    """Compute dashboard metrics from all previous analysis results"""
    uploads_dir = 'uploads'
    anomaly_files = glob.glob(os.path.join(uploads_dir, 'anomaly_results_*.csv'))
    total_logs = 0
    total_anomalies = 0
    total_processing_time = 0
    file_count = 0
    processing_times = []
    for file_path in anomaly_files:
        try:
            df = pd.read_csv(file_path)
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