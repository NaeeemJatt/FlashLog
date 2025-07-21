from flask import Blueprint, render_template, session, redirect, url_for, flash, request, current_app
from .helpers import compute_dashboard_metrics
from werkzeug.utils import secure_filename
from .logai_handler import process_log_file
from .routes import log_user_activity
from datetime import datetime
import os
from .auth import get_db_connection
import uuid
import json
import pandas as pd
import numpy as np

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

@dashboard_bp.route('/dashboard', methods=['GET', 'POST'])
def index():
    # Authentication is now handled in before_request (should be moved to a decorator or middleware)
    if session.get('role') == 'admin':
        return redirect(url_for('admin.dashboard'))
    dashboard_metrics = compute_dashboard_metrics()
    if request.method == 'POST':
        # Get form data
        parser = request.form.get('parser')
        model = request.form.get('model')
        index_name = request.form.get('index_name', f'analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
        
        if 'logfile' not in request.files:
            flash('No file part', 'error')
            return redirect(request.url)
        file = request.files['logfile']
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(request.url)
        if not allowed_file(file.filename):
            flash('Invalid file type. Allowed: csv, txt, log', 'error')
            return redirect(request.url)
        
        filename = secure_filename(file.filename)
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Check file size after save (or check before)
        if os.path.getsize(filepath) > 10 * 1024 * 1024:
            os.remove(filepath)
            flash('File too large (max 10MB)', 'error')
            return redirect(request.url)
        
        # Process
        try:
            try:
                results, _ = process_log_file(filepath, parser, model, index_name)
                print(f"[DEBUG] Results type: {type(results)}, length: {len(results)}")
                # Convert all timestamps to strings for JSON serialization
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
                # Save to DB
                run_id = str(uuid.uuid4())
                results_json = json.dumps(results.to_dict(orient='records') if hasattr(results, 'to_dict') else list(results))
                conn = get_db_connection()
                conn.execute('INSERT INTO analysis_runs (run_id, user_id, results_json) VALUES (?, ?, ?)', (run_id, session['user_id'], results_json))
                conn.commit()
                conn.close()
                print(f"[DEBUG] Saved results to DB with run_id: {run_id}")
                session['current_run'] = run_id
                session['analysis_summary'] = {
                    'total_logs': len(results),
                    'total_anomalies': results['is_anomaly'].sum() if hasattr(results, 'is_anomaly') else 0,
                    'index_name': index_name,
                    'parser': parser,
                    'model': model,
                    'created_at': datetime.now().isoformat()
                }
                print(f"[DEBUG] session['current_run'] set to {run_id}")
                print(f"[DEBUG] session['analysis_summary'] set")
                session.modified = True  # Force session to save changes
                print("[DEBUG] Redirecting to /analyzed-logs (DB save path)")
                return redirect(url_for('upload.analyzed_logs'))
            except Exception as e:
                print(f"[DEBUG] Error during DB save/session set: {str(e)}")
                flash(f'Error saving analysis results: {str(e)}', 'error')
                # Fallback: store a small sample in session for debugging
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
                    print("[DEBUG] Fallback: stored sample in session, redirecting to /analyzed-logs")
                    return redirect(url_for('upload.analyzed_logs'))
                except Exception as e2:
                    print(f"[DEBUG] Fallback error: {str(e2)}")
                    flash(f'Critical error: {str(e2)}', 'error')
                    print("[DEBUG] Redirecting to /dashboard (critical error path)")
                    return redirect(url_for('dashboard.index'))
        except Exception as e:
            print(f"[DEBUG] Outer error: {str(e)}")
            flash(f'Unexpected error: {str(e)}', 'error')
            print("[DEBUG] Redirecting to /dashboard (outer error path)")
            return redirect(url_for('dashboard.index'))
    return render_template('index.html', metrics=dashboard_metrics)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'csv', 'txt', 'log'} 