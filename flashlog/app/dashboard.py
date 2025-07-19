from flask import Blueprint, render_template, session, redirect, url_for, flash, request, current_app
from .helpers import compute_dashboard_metrics
from werkzeug.utils import secure_filename
from ..logai_handler import process_log_file
from ..routes import log_user_activity
from datetime import datetime
import os

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
@current_app.extensions['limiter'].limit('3 per minute')
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
            results, result_path = process_log_file(filepath, parser, model, index_name)
            session['analysis_file'] = result_path
            session['analysis_summary'] = {
                'total_logs': len(results),
                'total_anomalies': results['is_anomaly'].sum() if 'is_anomaly' in results else 0,
                'index_name': index_name,
                'parser': parser,
                'model': model,
                'created_at': datetime.now().isoformat()
            }
            # Log activity
            user_id = session['user_id']
            log_user_activity(
                user_id=user_id,
                activity_type='analysis',
                description='Log file analyzed',
                details=f'File: {filename}, Parser: {parser}, Model: {model}',
                file_name=filename,
                file_size=os.path.getsize(filepath),
                anomalies_detected=session['analysis_summary']['total_anomalies'],
                total_logs=session['analysis_summary']['total_logs']
            )
            flash('Analysis complete!', 'success')
            return redirect(url_for('upload.analyzed_logs'))
        except Exception as e:
            flash(f'Error processing file: {str(e)}', 'error')
            if os.path.exists(filepath):
                os.remove(filepath)
            return redirect(request.url)
    return render_template('index.html', metrics=dashboard_metrics)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'csv', 'txt', 'log'} 