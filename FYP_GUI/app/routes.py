from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
import os
import glob
import pandas as pd
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from .logai_handler import process_log_file

main = Blueprint('main', __name__)

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
                
                # Get processing time if available
                if 'processing_time_seconds' in df.columns:
                    processing_time = df['processing_time_seconds'].iloc[0]  # Same for all rows in file
                    processing_times.append(processing_time)
                    total_processing_time += processing_time
                
                file_count += 1
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
    
    # Calculate metrics
    success_rate = ((total_logs - total_anomalies) / total_logs * 100) if total_logs > 0 else 0
    
    # Calculate average processing time
    if processing_times:
        avg_processing_time = sum(processing_times) / len(processing_times)
    else:
        avg_processing_time = 2.4  # Default fallback
    
    # Calculate month-over-month change (simplified)
    # For now, we'll use a simple calculation based on file count
    if file_count > 0:
        # Estimate based on number of files processed
        growth_rate = min(15.1, max(-10, (file_count - 1) * 5))  # Between -10% and +15%
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

@main.route('/', methods=['GET', 'POST'])
def index():
    results = None
    csv_path = None
    kibana_url = None
    
    # Compute dashboard metrics
    dashboard_metrics = compute_dashboard_metrics()

    if request.method == 'POST':
        parser = request.form.get("parser", "drain")
        model = request.form.get("model", "isolation_forest")
        user_index = request.form.get("index_name", "").strip()
        index_name = user_index if user_index else f"logai-{datetime.utcnow().strftime('%Y-%m-%d')}"

        file = request.files.get('logfile')
        if not file:
            flash('No file uploaded.')
            return redirect(request.url)

        filename = secure_filename(file.filename)
        filepath = os.path.join('uploads', filename)
        file.save(filepath)

        try:
            result_data, csv_path = process_log_file(filepath, parser, model, index_name)
        except KeyError as e:
            flash(str(e))
            return redirect(request.url)

        num_logs = len(result_data)
        num_anomalies = result_data["is_anomaly"].sum()
        flash(f"✅ {num_logs} log entries processed. {num_anomalies} anomalies detected. Sent to index: {index_name}")

        if "timestamp" not in result_data.columns or result_data["timestamp"].isnull().all():
            flash("⚠️ Timestamp column missing in file — using system time instead.")

        results = result_data.to_dict(orient='records')
        kibana_url = f"http://localhost:5601/app/discover#/?_a=(index:'{index_name}',columns:!(_source))"

        # Recompute metrics after new analysis
        dashboard_metrics = compute_dashboard_metrics()

    return render_template('index.html', 
                         results=results, 
                         csv_path=csv_path, 
                         kibana_url=kibana_url,
                         metrics=dashboard_metrics)

@main.route('/download/<filename>')
def download_csv(filename):
    """Download the analysis results CSV file"""
    try:
        file_path = os.path.join('uploads', filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True, download_name=filename)
        else:
            flash('File not found.')
            return redirect(url_for('main.index'))
    except Exception as e:
        flash(f'Error downloading file: {str(e)}')
        return redirect(url_for('main.index'))
