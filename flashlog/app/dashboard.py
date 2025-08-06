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

def sanitize_for_json(obj):
    """Convert NumPy types to JSON-serializable Python types"""
    if isinstance(obj, (np.integer, np.int64, np.int32, np.int16, np.int8)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32, np.float16)):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_for_json(item) for item in obj]
    else:
        return obj

# Create a blueprint for dashboard-related routes

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def root():
    """Default route - redirect to auth if not authenticated, otherwise to appropriate dashboard"""
    if 'user_id' not in session:
        return redirect(url_for('auth.auth_page'))
    if session.get('role') == 'admin':
                    return redirect(url_for('admin.admin_dashboard'))
    return redirect(url_for('dashboard.index'))

@dashboard_bp.route('/dashboard', methods=['GET'])
def index():
    # Authentication is now handled in before_request (should be moved to a decorator or middleware)
    if session.get('role') == 'admin':
                    return redirect(url_for('admin.admin_dashboard'))
    dashboard_metrics = compute_dashboard_metrics()
    return render_template('index.html', metrics=dashboard_metrics)

@dashboard_bp.route('/analyze', methods=['POST'])
def analyze():
    print("[DEBUG] /analyze route called")
    if session.get('role') == 'admin':
                    return redirect(url_for('admin.admin_dashboard'))
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
            # Store original loglines for learning engine
            original_loglines = []
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        line = line.strip()
                        if line:  # Only non-empty lines
                            original_loglines.append(line)
                session['current_loglines'] = sanitize_for_json(original_loglines[:1000])  # Limit to 1000 lines for memory
                session.modified = True
                print(f"[DEBUG] Stored {len(session['current_loglines'])} original loglines for learning")
            except Exception as e:
                print(f"[DEBUG] Error reading original loglines: {e}")
                session['current_loglines'] = []
            
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
                elif isinstance(obj, (np.integer, np.int64, np.int32)):
                    return int(obj)  # Convert NumPy integers to Python int
                elif isinstance(obj, (np.floating, np.float64, np.float32)):
                    return float(obj)  # Convert NumPy floats to Python float
                return obj
            results = convert_timestamps(results)
            run_id = str(uuid.uuid4())
            results_json = json.dumps(results.to_dict(orient='records') if hasattr(results, 'to_dict') else list(results))
            conn = get_db_connection()
            conn.execute('INSERT INTO analysis_runs (run_id, user_id, results_json) VALUES (?, ?, ?)', (run_id, session['user_id'], results_json))
            conn.commit()
            conn.close()
            session['run_id'] = run_id
            session.modified = True  # Ensure run_id is saved immediately
            print(f"[DEBUG] Stored run_id in session: {run_id}")
            print(f"[DEBUG] Session keys after storing run_id: {list(session.keys())}")
            print(f"[DEBUG] Session run_id value: {session.get('run_id')}")
            total_logs = len(results)
            anomaly_count = results['is_anomaly'].sum() if hasattr(results, 'is_anomaly') else 0
            success_rate = round((total_logs - anomaly_count) / total_logs * 100, 2) if total_logs > 0 else 0
            
            # Convert NumPy types to Python native types for JSON serialization
            analysis_summary = {
                'total_logs': total_logs,
                'total_anomalies': anomaly_count,
                'success_rate': success_rate,
                'index_name': index_name,
                'parser': parser,
                'model': model,
                'created_at': datetime.now().isoformat()
            }
            session['analysis_summary'] = sanitize_for_json(analysis_summary)
            session.modified = True  # Ensure analysis_summary is saved
            print(f"[DEBUG] Analysis summary: {session['analysis_summary']}")
            print(f"[DEBUG] Session keys after storing analysis_summary: {list(session.keys())}")
            print(f"[DEBUG] Session run_id after analysis_summary: {session.get('run_id')}")
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
            # Save anomaly_types to temp file AND database
            tmp_dir = 'uploads/tmp'
            os.makedirs(tmp_dir, exist_ok=True)
            anomaly_types_path = os.path.join(tmp_dir, f'anomaly_types_{run_id}.json')
            print(f"[DEBUG] Saving anomaly types to temp file for run_id: {run_id}")
            with open(anomaly_types_path, 'w') as f:
                json.dump(anomaly_types, f)
            print(f"[DEBUG] anomaly_types saved to temp file: {anomaly_types}")
            session['anomaly_types_path'] = anomaly_types_path
            
            # ALSO save to database for persistence (if column exists)
            try:
                conn = get_db_connection()
                # First check if the column exists by trying to query it
                try:
                    conn.execute('SELECT anomaly_types_json FROM analysis_runs LIMIT 1')
                    # Column exists, safe to update
                    conn.execute(
                        'UPDATE analysis_runs SET anomaly_types_json = ? WHERE run_id = ?',
                        (json.dumps(anomaly_types), run_id)
                    )
                    conn.commit()
                    print(f"[DEBUG] anomaly_types also saved to database for run_id: {run_id}")
                except:
                    # Column doesn't exist, skip database storage
                    print(f"[DEBUG] anomaly_types_json column doesn't exist in database, skipping database storage")
                conn.close()
            except Exception as e:
                print(f"[DEBUG] Error saving anomaly_types to database: {e}")
                # Continue anyway, temp file is still available
            session.modified = True
            # Save severity counts for dashboard (sum from anomaly_types)
            severity_counts = {'Critical': 0, 'High': 0, 'Medium': 0, 'Low': 0}
            print(f"[DEBUG] Processing {len(anomaly_types)} anomaly types for severity counts")
            for item in anomaly_types:
                sev = item.get('severity')
                cnt = item.get('count', 0)
                print(f"[DEBUG] Processing anomaly type: severity='{sev}', count={cnt}, type='{item.get('type', 'N/A')}'")
                # Handle case sensitivity issues and clean up extra quotes
                if sev:
                    # Clean up extra quotes and normalize
                    sev_cleaned = sev.strip().strip('\'"').strip()  # Remove extra quotes
                    sev_normalized = sev_cleaned.title()  # Normalize to Title Case
                    if sev_normalized in severity_counts:
                        severity_counts[sev_normalized] += cnt
                        print(f"[DEBUG] Updated {sev_normalized} count to {severity_counts[sev_normalized]}")
                    else:
                        print(f"[DEBUG] Unknown severity '{sev}' (normalized: '{sev_normalized}') - not adding to counts")
                else:
                    print(f"[DEBUG] Empty or None severity - not adding to counts")
            print(f"[DEBUG] Final severity_counts: {severity_counts}")
            session['severity_counts'] = sanitize_for_json(severity_counts)
            
            # NEW: Trigger continuous learning engine
            try:
                print("[DEBUG] Triggering continuous learning engine...")
                import sys
                
                # Try multiple paths to find learning_engine
                current_dir = os.getcwd()
                print(f"[DEBUG] Current working directory: {current_dir}")
                
                possible_paths = [
                    current_dir,  # Current working directory
                    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),  # Project root
                    os.path.dirname(__file__),  # Same directory as this file
                ]
                
                learning_engine_found = False
                for path in possible_paths:
                    learning_engine_path = os.path.join(path, 'learning_engine.py')
                    if os.path.exists(learning_engine_path):
                        if path not in sys.path:
                            sys.path.insert(0, path)
                        print(f"[DEBUG] Found learning_engine at: {learning_engine_path}")
                        learning_engine_found = True
                        break
                
                if not learning_engine_found:
                    raise ImportError("learning_engine.py not found in any expected location")
                
                from learning_engine import ContinuousLearningEngine
                
                # Use the original loglines we stored earlier (session-independent)
                learning_logs = session.get('current_loglines', [])
                learning_results = results.to_dict(orient='records') if hasattr(results, 'to_dict') else list(results)
                
                if learning_logs and learning_results:
                    engine = ContinuousLearningEngine()
                    learning_session = engine.analyze_and_learn(
                        logs=learning_logs,  # These logs are now stored in database
                        results=learning_results,
                        session_id=run_id,
                        user_id=session.get('user_id', 1)
                    )
                    
                    # NEW: Track learning impact
                    impact_result = engine.track_learning_impact(run_id, learning_logs, learning_results)
                    
                    # Store only minimal info in session (for immediate feedback)
                    # Ensure JSON serializable data
                    session['learning_session_id'] = str(learning_session['session_id'])
                    session['learning_count'] = int(learning_session['learning_count'])
                    session.modified = True
                    
                    # Flash message to inform user
                    if learning_session['learning_count'] > 0:
                        flash(f'Analysis complete! 🧠 Generated {learning_session["learning_count"]} algorithm learnings for admin review.', 'info')
                        print(f"[DEBUG] ✅ Learnings stored permanently in database - session-independent!")
                    else:
                        flash('Analysis complete! No new learnings generated this time.', 'info')
                    
                    # Show learning impact if detected
                    if impact_result.get('impact_detected'):
                        improvements = impact_result['improvements']
                        impact_message = "🎯 Learning Impact Detected: "
                        if improvements.get('detection_improvement', 0) > 0:
                            impact_message += f"Detection improved by {improvements['detection_improvement']:.1f}%. "
                        if improvements.get('confidence_improvement', 0) > 0:
                            impact_message += f"Confidence improved by {improvements['confidence_improvement']:.1f}%. "
                        if improvements.get('accuracy_improvement', 0) > 0:
                            impact_message += f"Accuracy improved by {improvements['accuracy_improvement']:.1f}%. "
                        
                        flash(impact_message, 'success')
                        print(f"[DEBUG] ✅ Learning impact tracked and displayed to user")
                    else:
                        print(f"[DEBUG] No learning impact detected: {impact_result.get('message', 'Unknown')}")
                else:
                    print("[DEBUG] No data available for learning engine")
                    flash('Analysis complete!', 'success')
                    
            except Exception as learning_error:
                print(f"[DEBUG] Learning engine error: {learning_error}")
                flash('Analysis complete! (Learning engine temporarily unavailable)', 'warning')
            
            # BYPASS SESSION ISSUES: Store run_id in URL parameter instead
            print(f"[DEBUG] Session persistence failing - using URL parameter instead")
            print(f"[DEBUG] run_id to pass: {run_id}")
            print("[DEBUG] Redirecting to analyzed logs page with run_id parameter...")
            return redirect(url_for('upload.analyzed_logs', run_id=run_id))
        except Exception as e:
            print(f"[ERROR] Exception in analysis route: {str(e)}")
            print(f"[ERROR] Exception type: {type(e)}")
            import traceback
            print(f"[ERROR] Full traceback: {traceback.format_exc()}")
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
                print(f"[DEBUG] Error path - run_id: {session.get('run_id')}")
                return redirect(url_for('upload.analyzed_logs', run_id=run_id))
            except Exception as e2:
                flash(f'Critical error: {str(e2)}', 'error')
                return redirect(url_for('dashboard.index'))
    except Exception as e:
        print(f"[ERROR] Outer exception caught in analyze route: {str(e)}")
        print(f"[ERROR] Outer exception type: {type(e)}")
        import traceback
        print(f"[ERROR] Outer exception traceback: {traceback.format_exc()}")
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