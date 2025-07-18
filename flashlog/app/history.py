from flask import Blueprint, render_template, session, redirect, url_for, flash, request, jsonify
import os
import pandas as pd

history_bp = Blueprint('history', __name__)

@history_bp.route('/history')
def history():
    if 'user_id' not in session:
        flash('Please log in to view history.', 'error')
        return redirect(url_for('auth.auth_page'))
    uploads_dir = 'uploads'
    history_files = [f for f in os.listdir(uploads_dir) if f.startswith('anomaly_results_')]
    history_data = []
    for file in history_files:
        file_path = os.path.join(uploads_dir, file)
        try:
            df = pd.read_csv(file_path)
            if not df.empty:
                history_data.append({
                    'filename': file,
                    'num_logs': len(df),
                    'num_anomalies': df['is_anomaly'].sum() if 'is_anomaly' in df.columns else 0
                })
        except Exception as e:
            continue
    return render_template('history.html', history=history_data)

@history_bp.route('/api/history/latest')
def get_latest_activities():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    uploads_dir = 'uploads'
    history_files = [f for f in os.listdir(uploads_dir) if f.startswith('anomaly_results_')]
    latest = sorted(history_files)[-1] if history_files else None
    return jsonify({'latest': latest}) 