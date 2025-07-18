from flask import Blueprint, render_template, session, redirect, url_for, flash
import os
import pandas as pd

kibana_bp = Blueprint('kibana', __name__)

@kibana_bp.route('/kibana-dashboard')
def kibana_dashboard():
    if 'user_id' not in session:
        flash('Please log in to view the Kibana dashboard.', 'error')
        return redirect(url_for('auth.auth_page'))
    analysis_file = session.get('analysis_file')
    if not analysis_file or not os.path.exists(analysis_file):
        flash('No analysis results found. Please upload and analyze a log file first.', 'error')
        return redirect(url_for('dashboard.index'))
    try:
        results_df = pd.read_csv(analysis_file)
        results = results_df.to_dict(orient='records')
    except Exception as e:
        flash('Error loading analysis results for Kibana dashboard.', 'error')
        return redirect(url_for('dashboard.index'))
    # Optionally, process results for Kibana dashboard here
    return render_template('kibana_dashboard.html', results=results) 