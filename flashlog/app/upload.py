from flask import Blueprint, render_template, session, redirect, url_for, flash, request, make_response
import os
import pandas as pd
from datetime import datetime
from .auth import get_db_connection
import json
import uuid

upload_bp = Blueprint('upload', __name__)

@upload_bp.route('/analyzed-logs')
@upload_bp.route('/analyzed-logs/<run_id>')
def analyzed_logs(run_id=None):
    if 'user_id' not in session:
        print("[DEBUG] No user_id in session - redirecting to auth")
        flash('Please log in to view analysis results.', 'error')
        return redirect(url_for('auth.auth_page'))
    
    # Debug session state at the start of the route
    print(f"[DEBUG] analyzed_logs route - Session keys: {list(session.keys())}")
    print(f"[DEBUG] analyzed_logs route - Session ID: {session.get('session_token', 'NO_TOKEN')}")
    print(f"[DEBUG] analyzed_logs route - User ID: {session.get('user_id', 'NO_USER')}")
    print(f"[DEBUG] analyzed_logs route - Request endpoint: {request.endpoint}")
    
    # Check if session token is valid (similar to routes.py logic)
    session_token = session.get('session_token')
    if session_token:
        conn = get_db_connection()
        valid_session = conn.execute(
            'SELECT * FROM user_sessions WHERE session_token = ? AND expires_at > CURRENT_TIMESTAMP',
            (session_token,)
        ).fetchone()
        conn.close()
        print(f"[DEBUG] analyzed_logs route - Session token validation: {'VALID' if valid_session else 'INVALID'}")
        
        if not valid_session:
            print("[DEBUG] analyzed_logs route - Session token expired, clearing session")
            session.clear()
            flash('Session expired. Please log in again.', 'error')
            return redirect(url_for('auth.auth_page'))
    else:
        print("[DEBUG] analyzed_logs route - No session token found")
    
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Show 10 results per page
    
    # Try to get run_id from URL parameter first, then fallback to session
    if not run_id:
        run_id = request.args.get('run_id')
    if not run_id:
        run_id = session.get('run_id')
    if not run_id:
        run_id = session.get('backup_run_id')
    
    print(f"[DEBUG] analyzed_logs route - Final run_id: {run_id}")
    print(f"[DEBUG] analyzed_logs route - run_id source: {'URL parameter' if request.args.get('run_id') else 'session'}")
    
    if not run_id:
        print("[DEBUG] No run_id in session - redirecting to dashboard")
        flash('No analysis run found. Please analyze a log file first.')
        return redirect('/user/dashboard')
    
    try:
        conn = get_db_connection()
        row = conn.execute('SELECT results_json FROM analysis_runs WHERE run_id = ?', (run_id,)).fetchone()
        conn.close()
        if not row:
            print("[DEBUG] No results found in DB for run_id - redirecting")
            flash('Analysis results expired or not found.')
            return redirect('/user/dashboard')
        analysis_results = json.loads(row['results_json'])
        
        # Get analysis summary from session or create a basic one
        analysis_summary = session.get('analysis_summary', {})
        if not analysis_summary:
            # Create basic summary from results if session data is missing
            total_logs = len(analysis_results)
            anomaly_count = sum(1 for r in analysis_results if r.get('is_anomaly', False))
            analysis_summary = {
                'total_logs': total_logs,
                'total_anomalies': anomaly_count,
                'success_rate': round((total_logs - anomaly_count) / total_logs * 100, 2) if total_logs > 0 else 0,
                'index_name': 'flashlog-analysis',
                'parser': 'drain',
                'model': 'isolation_forest',
                'created_at': 'Unknown'
            }
            print(f"[DEBUG] Created fallback analysis_summary: {analysis_summary}")
        else:
            print(f"[DEBUG] Using session analysis_summary: {analysis_summary}")
            
    except Exception as e:
        print(f"[DEBUG] Error loading from DB: {str(e)}")
        flash('Error loading analysis results from storage.', 'error')
        return redirect('/user/dashboard')
    
    if not analysis_results or not isinstance(analysis_results, list):
        print("[DEBUG] Loaded results invalid - redirecting")
        flash('Invalid analysis results.')
        return redirect('/user/dashboard')
    
    # Calculate pagination
    total_results = len(analysis_results)
    total_pages = (total_results + per_page - 1) // per_page  # Ceiling division
    
    # Calculate start and end indices for current page
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    
    # Get results for current page
    results = analysis_results[start_idx:end_idx]
    
    # Prepare pagination info
    pagination = {
        'page': page,
        'per_page': per_page,
        'total_results': total_results,
        'total_pages': total_pages,
        'total_count': total_results,
        'has_prev': page > 1,
        'has_next': page < total_pages,
        'prev_num': page - 1 if page > 1 else None,
        'next_num': page + 1 if page < total_pages else None
    }
    
    response = make_response(render_template('analyzed_logs.html',
                         results=results,
                         csv_path=None,
                         kibana_url=session.get('kibana_url'),
                         analysis_summary=analysis_summary,
                         pagination=pagination,
                         run_id=run_id))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@upload_bp.route('/analysis-dashboard')
@upload_bp.route('/analysis-dashboard/<analysis_id>')
def analysis_dashboard(analysis_id=None):
    if 'user_id' not in session:
        flash('Please log in to view dashboard.', 'error')
        return redirect(url_for('auth.auth_page'))
    analysis_file = session.get('analysis_file')
    analysis_summary = session.get('analysis_summary', {})
    if not analysis_file or not isinstance(analysis_file, str) or not os.path.exists(analysis_file):
        flash('No analysis results found. Please upload and analyze a log file first.', 'error')
        return redirect('/user/dashboard')
    try:
        results_df = pd.read_csv(analysis_file)
        results = results_df.to_dict(orient='records')
    except Exception as e:
        flash('Error loading analysis results. Please try again.', 'error')
        return redirect('/user/dashboard')
    analysis = {
        'id': analysis_id or analysis_summary.get('analysis_id', 'current'),
        'user_id': session['user_id'],
        'created_at': analysis_summary.get('created_at', datetime.now().isoformat()),
        'index_name': analysis_summary.get('index_name', 'Unknown'),
        'parser': analysis_summary.get('parser', 'Unknown'),
        'model': analysis_summary.get('model', 'Unknown')
    }
    # You may want to import and use process_dashboard_data here if needed
    return render_template('user_dashboard.html', analysis=analysis, results=results)

@upload_bp.route('/upload', methods=['POST'])
def upload_file():
    if 'user_id' not in session:
        flash('Please log in to upload files.', 'error')
        return redirect(url_for('auth.auth_page'))

    file = request.files.get('logfile')
    parser_algo = request.form.get('parser')
    model_type = request.form.get('model')
    index_name = request.form.get('index_name') or f"flashlog-{datetime.now().strftime('%Y-%m-%d')}"

    if not file or file.filename == '':
        flash('No file selected!', 'error')
        return redirect('/user/dashboard')

    # Save file to a temp location
    filepath = os.path.join('uploads', file.filename)
    file.save(filepath)

    # Call LogAI handler
    from .logai_handler import process_log_file
    results, processing_time = process_log_file(filepath, parser_algo, model_type, index_name)

    # Save results to DB
    conn = get_db_connection()
    run_id = str(uuid.uuid4())
    conn.execute(
        'INSERT INTO analysis_runs (run_id, user_id, results_json) VALUES (?, ?, ?)',
        (run_id, session['user_id'], json.dumps(results.to_dict(orient='records')))
    )
    conn.commit()
    conn.close()

    # Update session
    session['run_id'] = run_id
    session['analysis_summary'] = {
        'created_at': datetime.now().isoformat(),
        'index_name': index_name,
        'parser': parser_algo,
        'model': model_type,
        'processing_time': processing_time
    }

    flash('Analysis complete!', 'success')
    return redirect(url_for('upload.analyzed_logs')) 