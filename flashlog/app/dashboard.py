from flask import Blueprint, render_template, session, redirect, url_for, flash, request, current_app
from .helpers import compute_dashboard_metrics
from werkzeug.utils import secure_filename
from .logai_handler import process_log_file
from .routes import log_user_activity
from datetime import datetime
import os
import json
import pandas as pd
import numpy as np
from flask_login import login_required
import uuid
from .auth import get_db_connection

# Create a blueprint for dashboard-related routes

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def root():
    """Default route - redirect to auth if not authenticated, otherwise to appropriate dashboard"""
    if 'user_id' not in session:
        return redirect(url_for('auth.auth_page'))
    if session.get('role') == 'admin':
        return redirect(url_for('admin.dashboard'))
    return redirect(url_for('dashboard.index'))

@dashboard_bp.route('/dashboard', methods=['GET'])
def index():
    # Authentication is now handled in before_request (should be moved to a decorator or middleware)
    if session.get('role') == 'admin':
        return redirect(url_for('admin.dashboard'))
    dashboard_metrics = compute_dashboard_metrics()
    return render_template('index.html', metrics=dashboard_metrics)

@dashboard_bp.route('/analyze', methods=['POST'])
def analyze():
    print("[DEBUG] /analyze route called")
    if session.get('role') == 'admin':
        return redirect(url_for('admin.dashboard'))
    parser = request.form.get('parser')
    model = request.form.get('model')
    index_name = request.form.get('index_name', f'analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
    if 'logfile' not in request.files:
        flash('No file part', 'error')
        return redirect(url_for('dashboard.index'))
    file = request.files['logfile']
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(url_for('dashboard.index'))
    if not allowed_file(file.filename):
        flash('Invalid file type. Allowed: csv, txt, log', 'error')
        return redirect(url_for('dashboard.index'))
    filename = secure_filename(file.filename)
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    print(f"[DEBUG] File saved to {filepath}, starting analysis...")
    if os.path.getsize(filepath) > 10 * 1024 * 1024:
        os.remove(filepath)
        flash('File too large (max 10MB)', 'error')
        return redirect(url_for('dashboard.index'))
    try:
        try:
            results, _ = process_log_file(filepath, parser, model, index_name)
            print(f"[DEBUG] Analysis complete. Results type: {type(results)}, length: {len(results)}")
            def convert_timestamps(obj):
                if isinstance(obj, pd.DataFrame):
                    for col in obj.columns:
                        if np.issubdtype(obj[col].dtype, np.datetime64):
                            obj[col] = obj[col].astype(str)
                        elif obj[col].dtype == 'object':
                            obj[col] = obj[col].apply(lambda x: str(x) if isinstance(x, (pd.Timestamp, np.datetime64)) else x)
                    return obj
                elif isinstance(obj, list):
                    return [convert_timestamps(x) for x in obj]
                elif isinstance(obj, dict):
                    return {k: convert_timestamps(v) for k, v in obj.items()}
                elif isinstance(obj, (pd.Timestamp, np.datetime64)):
                    return str(obj)
                return obj
            results = convert_timestamps(results)
            run_id = str(uuid.uuid4())
            results_json = json.dumps(results.to_dict(orient='records') if hasattr(results, 'to_dict') else list(results))
            conn = get_db_connection()
            conn.execute('INSERT INTO analysis_runs (run_id, user_id, results_json) VALUES (?, ?, ?)', (run_id, session['user_id'], results_json))
            conn.commit()
            conn.close()
            session['current_run'] = run_id
            total_logs = len(results)
            anomaly_count = results['is_anomaly'].sum() if hasattr(results, 'is_anomaly') else 0
            success_rate = round((total_logs - anomaly_count) / total_logs * 100, 2) if total_logs > 0 else 0
            session['analysis_summary'] = {
                'total_logs': total_logs,
                'total_anomalies': anomaly_count,
                'success_rate': success_rate,
                'index_name': index_name,
                'parser': parser,
                'model': model,
                'created_at': datetime.now().isoformat()
            }
            print(f"[DEBUG] Analysis summary: {session['analysis_summary']}")
            # Immediately classify anomalies and store in temp file
            anomalies = []
            if hasattr(results, 'to_dict'):
                anomalies = [row for row in results.to_dict(orient='records') if row.get('is_anomaly')]
            elif isinstance(results, list):
                anomalies = [row for row in results if row.get('is_anomaly')]
            anomaly_types = []
            if anomalies:
                print(f"[DEBUG] {len(anomalies)} anomalies detected, calling external API...")
                from .helpers import classify_all_anomalies
                anomaly_types = classify_all_anomalies(anomalies)
                print(f"[DEBUG] API returned {len(anomaly_types)} anomaly types.")
            else:
                print("[DEBUG] No anomalies to classify.")
            # Save anomaly_types to temp file
            tmp_dir = 'uploads/tmp'
            os.makedirs(tmp_dir, exist_ok=True)
            anomaly_types_path = os.path.join(tmp_dir, f'anomaly_types_{run_id}.json')
            print(f"[DEBUG] Saving anomaly types to temp file for run_id: {run_id}")
            with open(anomaly_types_path, 'w') as f:
                json.dump(anomaly_types, f)
            print(f"[DEBUG] anomaly_types saved to temp file: {anomaly_types}")
            session['anomaly_types_path'] = anomaly_types_path
            session.modified = True
            # Save severity counts for dashboard (sum from anomaly_types)
            severity_counts = {'Critical': 0, 'High': 0, 'Medium': 0, 'Low': 0}
            for item in anomaly_types:
                sev = item.get('severity')
                cnt = item.get('count', 0)
                if sev in severity_counts:
                    severity_counts[sev] += cnt
            session['severity_counts'] = severity_counts
            print("[DEBUG] Redirecting to analyzed logs page...")
            return redirect(url_for('upload.analyzed_logs'))
        except Exception as e:
            flash(f'Error saving analysis results: {str(e)}', 'error')
            try:
                sample = results.head(5).to_dict(orient='records') if hasattr(results, 'head') else list(results)[:5]
                session['analysis_results'] = sample
                session['analysis_summary'] = {
                    'total_logs': len(sample),
                    'total_anomalies': sample[0].get('is_anomaly', 0) if sample else 0,
                    'index_name': index_name,
                    'parser': parser,
                    'model': model,
                    'created_at': datetime.now().isoformat()
                }
                session.modified = True
                return redirect(url_for('upload.analyzed_logs'))
            except Exception as e2:
                flash(f'Critical error: {str(e2)}', 'error')
                return redirect(url_for('dashboard.index'))
    except Exception as e:
        flash(f'Unexpected error: {str(e)}', 'error')
        return redirect(url_for('dashboard.index'))

# Update dashboard route to /admin/dashboard for admin dashboard
@dashboard_bp.route('/admin/dashboard', methods=['GET', 'POST'])
@login_required
def admin_dashboard():
    # ... existing admin dashboard logic ...
    pass

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'csv', 'txt', 'log'} 