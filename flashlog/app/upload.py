from flask import Blueprint, render_template, session, redirect, url_for, flash, request, make_response
import os
import pandas as pd
from datetime import datetime
from .auth import get_db_connection
import json
import uuid

upload_bp = Blueprint('upload', __name__)

@upload_bp.route('/analyzed-logs')
def analyzed_logs():
    if 'user_id' not in session:
        print("[DEBUG] No user_id in session - redirecting to auth")
        flash('Please log in to view analysis results.', 'error')
        return redirect(url_for('auth.auth_page'))
    page = request.args.get('page', 1, type=int)
    per_page = 10
    analysis_summary = session.get('analysis_summary', {})
    print(f"[DEBUG] Session keys on load: {list(session.keys())}")
    run_id = session.get('current_run')
    print(f"[DEBUG] run_id in session: {run_id}")
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
        print(f"[DEBUG] Loaded results from DB, length: {len(analysis_results)}")
    except Exception as e:
        print(f"[DEBUG] Error loading from DB: {str(e)}")
        flash('Error loading analysis results from storage.', 'error')
        return redirect('/user/dashboard')
    if not analysis_results or not isinstance(analysis_results, list):
        print("[DEBUG] Loaded results invalid - redirecting")
        flash('Invalid analysis results.')
        return redirect('/user/dashboard')
    results = analysis_results
    total_results = len(results)
    total_pages = (total_results + per_page - 1) // per_page
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_results = results[start_idx:end_idx]
    response = make_response(render_template('analyzed_logs.html',
                         results=paginated_results,
                         csv_path=None,
                         kibana_url=session.get('kibana_url'),
                         analysis_summary=analysis_summary,
                         pagination={
                             'page': page,
                             'per_page': per_page,
                             'total_pages': total_pages,
                             'total_results': total_results,
                             'start_idx': start_idx + 1,
                             'end_idx': min(end_idx, total_results)
                         }))
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
    session['current_run'] = run_id
    session['analysis_summary'] = {
        'created_at': datetime.now().isoformat(),
        'index_name': index_name,
        'parser': parser_algo,
        'model': model_type,
        'processing_time': processing_time
    }

    flash('Analysis complete!', 'success')
    return redirect(url_for('upload.analyzed_logs')) 