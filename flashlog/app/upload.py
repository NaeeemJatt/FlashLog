from flask import Blueprint, render_template, session, redirect, url_for, flash, request, make_response
import os
import pandas as pd
from datetime import datetime

upload_bp = Blueprint('upload', __name__)

@upload_bp.route('/analyzed-logs')
def analyzed_logs():
    if 'user_id' not in session:
        flash('Please log in to view analysis results.', 'error')
        return redirect(url_for('auth.auth_page'))
    page = request.args.get('page', 1, type=int)
    per_page = 10
    analysis_file = session.get('analysis_file')
    kibana_url = session.get('kibana_url')
    analysis_summary = session.get('analysis_summary', {})
    if not analysis_file or not os.path.exists(analysis_file):
        flash('No analysis results found. Please upload and analyze a log file first.')
        return redirect(url_for('dashboard.index'))
    try:
        results_df = pd.read_csv(analysis_file)
        results = results_df.to_dict(orient='records')
    except Exception as e:
        flash('Error loading analysis results. Please try again.', 'error')
        return redirect(url_for('dashboard.index'))
    total_results = len(results)
    total_pages = (total_results + per_page - 1) // per_page
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_results = results[start_idx:end_idx]
    response = make_response(render_template('analyzed_logs.html',
                         results=paginated_results,
                         csv_path=analysis_file,
                         kibana_url=kibana_url,
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
    if not analysis_file or not os.path.exists(analysis_file):
        flash('No analysis results found. Please upload and analyze a log file first.', 'error')
        return redirect(url_for('dashboard.index'))
    try:
        results_df = pd.read_csv(analysis_file)
        results = results_df.to_dict(orient='records')
    except Exception as e:
        flash('Error loading analysis results. Please try again.', 'error')
        return redirect(url_for('dashboard.index'))
    analysis = {
        'id': analysis_id or analysis_summary.get('analysis_id', 'current'),
        'user_id': session['user_id'],
        'created_at': analysis_summary.get('created_at', datetime.now().isoformat()),
        'index_name': analysis_summary.get('index_name', 'Unknown'),
        'parser': analysis_summary.get('parser', 'Unknown'),
        'model': analysis_summary.get('model', 'Unknown')
    }
    # You may want to import and use process_dashboard_data here if needed
    return render_template('dashboard.html', analysis=analysis, results=results) 