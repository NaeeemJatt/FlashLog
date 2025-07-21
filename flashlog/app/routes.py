from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, session, make_response, jsonify
import os
import glob
import pandas as pd
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
# from .logai_handler import process_log_file  # Temporarily commented out due to dependency issues
from .auth import login_required, get_current_user, get_db_connection
import numpy as np
from collections import Counter
from transformers import pipeline

def log_user_activity(user_id, activity_type, description, details=None, status='success', ip_address=None, user_agent=None, file_name=None, file_size=None, processing_time=None, anomalies_detected=None, total_logs=None, old_value=None, new_value=None):
    """Log user activity to the database with enhanced tracking"""
    try:
        print(f"🔍 Logging activity: {activity_type} - {description}")
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO user_activities (user_id, activity_type, description, details, status, ip_address, user_agent, file_name, file_size, processing_time, anomalies_detected, total_logs, old_value, new_value)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, activity_type, description, details, status, ip_address, user_agent, file_name, file_size, processing_time, anomalies_detected, total_logs, old_value, new_value))
        conn.commit()
        conn.close()
        print(f"✅ Activity logged successfully: {activity_type}")
    except Exception as e:
        print(f"❌ Error logging activity: {str(e)}")
        import traceback
        traceback.print_exc()

main = Blueprint('main', __name__)

@main.before_request
def before_request():
    """Set cache headers and check authentication for all routes"""
    # Set cache control headers for all protected routes
    if request.endpoint and request.endpoint.startswith('main.'):
        # Add cache control headers to prevent back button access
        response = make_response()
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-Content-Type-Options'] = 'nosniff'
    
    # Check authentication for protected routes
    protected_endpoints = ['main.index', 'main.analyzed_logs', 'main.download_csv']
    if request.endpoint in protected_endpoints:
        if 'user_id' not in session:
            flash('Session expired. Please log in again.', 'error')
            return redirect(url_for('auth.auth_page'))
        
        # Verify session is still valid
        if 'session_token' in session:
            conn = get_db_connection()
            valid_session = conn.execute(
                'SELECT * FROM user_sessions WHERE session_token = ? AND expires_at > CURRENT_TIMESTAMP',
                (session['session_token'],)
            ).fetchone()
            conn.close()
            
            if not valid_session:
                session.clear()
                flash('Session expired. Please log in again.', 'error')
                return redirect(url_for('auth.auth_page'))

@main.route('/')
def root():
    """Default route - redirect to auth if not authenticated, otherwise to appropriate dashboard"""
    if 'user_id' not in session:
        return redirect(url_for('auth.auth_page'))
    
    # Check if user is admin and redirect to admin dashboard
    if session.get('role') == 'admin':
        return redirect(url_for('admin.dashboard'))
    
    return redirect(url_for('dashboard.index'))

# The analyzed_logs and analysis_dashboard routes have been refactored into upload.py.

@main.route('/download/<filename>')
@login_required
def download_csv(filename):
    """Download the analysis results CSV file with custom filename support"""
    try:
        file_path = os.path.join('uploads', filename)
        if os.path.exists(file_path):
            # Generate a more descriptive filename based on analysis data
            analysis_summary = session.get('analysis_summary', {})
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Create a descriptive filename
            if analysis_summary:
                total_logs = analysis_summary.get('total_logs', 0)
                total_anomalies = analysis_summary.get('total_anomalies', 0)
                index_name = analysis_summary.get('index_name', 'analysis')
                custom_filename = f"log_analysis_{index_name}_{total_logs}logs_{total_anomalies}anomalies_{timestamp}.csv"
            else:
                custom_filename = f"log_analysis_results_{timestamp}.csv"
            
            # Set headers to trigger file save dialog
            response = send_file(
                file_path, 
                as_attachment=True, 
                download_name=custom_filename,
                mimetype='text/csv'
            )
            
            # Add headers to prevent caching and ensure proper download behavior
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
            response.headers['Content-Disposition'] = f'attachment; filename="{custom_filename}"'
            
            return response
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': f'Error downloading file: {str(e)}'}), 500

@main.route('/download-status/<filename>')
@login_required
def download_status(filename):
    """Check if download file exists and return status"""
    try:
        file_path = os.path.join('uploads', filename)
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            return jsonify({
                'status': 'available',
                'filename': filename,
                'size': file_size,
                'size_mb': round(file_size / (1024 * 1024), 2)
            })
        else:
            return jsonify({'status': 'not_found'}), 404
    except Exception as e:
        return jsonify({'error': f'Error checking file: {str(e)}'}), 500

@main.route('/test-upload')
def test_upload():
    """Serve test upload page for debugging"""
    return send_file('test_upload.html')

@main.route('/test-session')
def test_session():
    """Test route to verify session functionality"""
    session['test_data'] = 'Hello from session!'
    session['test_timestamp'] = datetime.now().isoformat()
    return jsonify({
        'session_keys': list(session.keys()),
        'test_data': session.get('test_data'),
        'test_timestamp': session.get('test_timestamp')
    })

@main.route('/debug-session')
def debug_session():
    """Debug route to check session data"""
    return {
        'session_keys': list(session.keys()),
        'analysis_results_count': len(session.get('analysis_results', [])),
        'csv_path': session.get('csv_path'),
        'analysis_summary': session.get('analysis_summary', {})
    }

@main.route('/history')
@login_required
def history():
    """Display user activity history with enhanced filtering and real-time updates"""
    user = get_current_user()
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('dashboard.index'))
    
    # Get filter parameters
    page = request.args.get('page', 1, type=int)
    per_page = 20
    activity_type = request.args.get('type', '')
    status_filter = request.args.get('status', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    conn = get_db_connection()
    
    # Build query with filters
    query = 'SELECT * FROM user_activities WHERE user_id = ?'
    params = [user['id']]
    
    if activity_type:
        query += ' AND activity_type = ?'
        params.append(activity_type)
    
    if status_filter:
        query += ' AND status = ?'
        params.append(status_filter)
    
    if date_from:
        query += ' AND DATE(created_at) >= ?'
        params.append(date_from)
    
    if date_to:
        query += ' AND DATE(created_at) <= ?'
        params.append(date_to)
    
    # Get total count with filters
    count_query = query.replace('SELECT *', 'SELECT COUNT(*)')
    total_count = conn.execute(count_query, params).fetchone()[0]
    
    # Get paginated activities with filters
    query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
    offset = (page - 1) * per_page
    params.extend([per_page, offset])
    
    activities = conn.execute(query, params).fetchall()
    
    # Get activity type statistics for filter dropdown
    activity_types = conn.execute('''
        SELECT activity_type, COUNT(*) as count 
        FROM user_activities 
        WHERE user_id = ? 
        GROUP BY activity_type 
        ORDER BY count DESC
    ''', (user['id'],)).fetchall()
    
    # Get status statistics
    status_stats = conn.execute('''
        SELECT status, COUNT(*) as count 
        FROM user_activities 
        WHERE user_id = ? 
        GROUP BY status 
        ORDER BY count DESC
    ''', (user['id'],)).fetchall()
    
    conn.close()
    
    # Convert activities to list of dicts for template
    activities_list = []
    for activity in activities:
        activity_dict = dict(activity)
        # Convert timestamp to datetime if it's a string
        if isinstance(activity_dict['created_at'], str):
            try:
                activity_dict['created_at'] = datetime.fromisoformat(activity_dict['created_at'].replace('Z', '+00:00'))
            except:
                pass
        activities_list.append(activity_dict)
    
    total_pages = (total_count + per_page - 1) // per_page
    
    return render_template('history.html', 
                         activities=activities_list,
                         activity_types=activity_types,
                         status_stats=status_stats,
                         current_filters={
                             'type': activity_type,
                             'status': status_filter,
                             'date_from': date_from,
                             'date_to': date_to
                         },
                         pagination={
                             'page': page,
                             'per_page': per_page,
                             'total_pages': total_pages,
                             'total_count': total_count
                         })

@main.route('/api/history/latest')
@login_required
def get_latest_activities():
    """API endpoint to get latest activities for real-time updates"""
    print(f"🔍 API: get_latest_activities called")
    user = get_current_user()
    if not user:
        print(f"❌ API: User not found")
        return jsonify({'error': 'User not found'}), 404
    
    # Get the last activity ID from request to check for new activities
    last_id = request.args.get('last_id', 0, type=int)
    print(f"🔍 API: last_id = {last_id}, user_id = {user['id']}")
    
    conn = get_db_connection()
    
    # Get activities newer than the last seen ID
    limit = min(max(request.args.get('limit', 10, type=int), 1), 50)
    activities = conn.execute('''
        SELECT * FROM user_activities 
        WHERE user_id = ? AND id > ? 
        ORDER BY created_at DESC 
        LIMIT ?
    ''', (user['id'], last_id, limit)).fetchall()
    
    conn.close()
    
    print(f"🔍 API: Found {len(activities)} new activities")
    
    # Convert to JSON-serializable format
    activities_list = []
    for activity in activities:
        activity_dict = dict(activity)
        # Convert timestamp to string for JSON
        if isinstance(activity_dict['created_at'], str):
            try:
                dt = datetime.fromisoformat(activity_dict['created_at'].replace('Z', '+00:00'))
                activity_dict['created_at'] = dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                pass
        activities_list.append(activity_dict)
    
    response_data = {
        'activities': activities_list,
        'count': len(activities_list),
        'last_id': max([a['id'] for a in activities_list]) if activities_list else last_id
    }
    
    print(f"🔍 API: Returning response with {len(activities_list)} activities")
    response = jsonify(response_data)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@main.route('/flashlog-dashboard')
@login_required
def flashlog_dashboard():
    """Display FlashLog Dashboard with time-series data and metrics"""
    if 'user_id' not in session:
        flash('Please log in to view dashboard.', 'error')
        return redirect(url_for('auth.auth_page'))
    # Get run_id from session
    run_id = session.get('current_run')
    print(f"[DEBUG] [Kibana] run_id in session: {run_id}")
    if not run_id:
        print("[DEBUG] [Kibana] No run_id in session - redirecting to dashboard")
        flash('No analysis run found. Please analyze a log file first.')
        return redirect(url_for('dashboard.index'))
    try:
        from .auth import get_db_connection
        import json
        conn = get_db_connection()
        row = conn.execute('SELECT results_json FROM analysis_runs WHERE run_id = ?', (run_id,)).fetchone()
        conn.close()
        if not row:
            print("[DEBUG] [Kibana] No results found in DB for run_id - redirecting")
            flash('Analysis results expired or not found.')
            return redirect(url_for('dashboard.index'))
        analysis_results = json.loads(row['results_json'])
        print(f"[DEBUG] [Kibana] Loaded results from DB, length: {len(analysis_results)}")
    except Exception as e:
        print(f"[DEBUG] [Kibana] Error loading from DB: {str(e)}")
        flash('Error loading analysis results from storage.', 'error')
        return redirect(url_for('dashboard.index'))
    if not analysis_results or not isinstance(analysis_results, list):
        print("[DEBUG] [Kibana] Loaded results invalid - redirecting")
        flash('Invalid analysis results.')
        return redirect(url_for('dashboard.index'))
    # Process data for Kibana-style dashboard
    kibana_data = process_kibana_dashboard_data(analysis_results)
    return render_template('flashlog_dashboard.html', 
                         kibana_data=kibana_data,
                         results=analysis_results)

def process_kibana_dashboard_data(results):
    """Process analysis results for Kibana-style dashboard visualizations"""
    import pandas as pd
    import numpy as np
    from collections import Counter
    import re
    from datetime import datetime, timedelta
    
    # Convert results to DataFrame for easier processing
    df = pd.DataFrame(results)
    
    # Basic statistics from your actual data
    total_logs = len(df)
    anomaly_count = df['is_anomaly'].sum() if 'is_anomaly' in df.columns else 0
    normal_count = total_logs - anomaly_count
    anomaly_percentage = (anomaly_count / total_logs * 100) if total_logs > 0 else 0
    
    # Generate metrics based on your actual data structure
    # Unique log patterns (templates) as "hosts"
    unique_patterns = df['logline'].nunique() if 'logline' in df.columns else 1
    
    # Severity levels as "UTC sources"
    severity_count = 0
    if 'logline' in df.columns:
        log_lines = df['logline'].astype(str)
        severity_count = len(log_lines[log_lines.str.contains(r'\b(error|warning|info|debug|critical)\b', case=False, regex=True)])
    
    # Processing time as "offset"
    if 'processing_time_seconds' in df.columns:
        try:
            # Convert to numeric, handling any string concatenation issues
            processing_times = pd.to_numeric(df['processing_time_seconds'], errors='coerce')
            # Remove any NaN values
            processing_times = processing_times.dropna()
            
            if len(processing_times) > 0:
                avg_processing_time = int(processing_times.mean() * 1000)  # Convert to ms
                max_processing_time = int(processing_times.max() * 1000)
            else:
                avg_processing_time = 993
                max_processing_time = 3832
        except Exception as e:
            print(f"Error processing processing_time_seconds: {e}")
            avg_processing_time = 993
            max_processing_time = 3832
    else:
        avg_processing_time = 993
        max_processing_time = 3832
    
    # Generate time-series data based on your actual data
    time_series_data = generate_time_series_data(df)
    
    # Generate table data based on your actual data
    table_data = generate_table_data(df)
    
    return {
        'metrics': {
            'host_count': unique_patterns,
            'utc_sources': severity_count,
            'average_offset': avg_processing_time,
            'max_offset': max_processing_time
        },
        'time_series': time_series_data,
        'table_data': table_data,
        'summary': {
            'total_logs': total_logs,
            'anomaly_count': anomaly_count,
            'normal_count': normal_count,
            'anomaly_percentage': round(anomaly_percentage, 2)
        },
        'time_range': {
            'start': '10:27:30',
            'end': '10:32:00',
            'interval': '5 seconds'
        }
    }

def generate_time_series_data(df):
    """Generate time-series data for Kibana-style charts based on actual log data"""
    import numpy as np
    from datetime import datetime, timedelta
    
    # Use actual timestamps if available, otherwise generate realistic ones
    if 'timestamp' in df.columns and df['timestamp'].notna().any():
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        df = df.dropna(subset=['timestamp'])
        
        if len(df) > 0:
            # Use actual timestamps
            time_range = pd.date_range(
                start=df['timestamp'].min(),
                end=df['timestamp'].max(),
                periods=60  # 60 data points
            )
            time_points = time_range.tolist()
        else:
            # Fallback to generated timestamps
            start_time = datetime.now().replace(hour=10, minute=27, second=30, microsecond=0)
            time_points = [start_time + timedelta(seconds=i*5) for i in range(60)]
    else:
        # Generate realistic timestamps
        start_time = datetime.now().replace(hour=10, minute=27, second=30, microsecond=0)
        time_points = [start_time + timedelta(seconds=i*5) for i in range(60)]
    
    # Generate data based on actual log analysis results
    np.random.seed(42)  # For consistent results
    
    # Anomaly Rate Over Time (green line) - based on actual anomaly data
    anomaly_rate_data = []
    if 'is_anomaly' in df.columns and len(df) > 0:
        # Calculate anomaly rate for each time period
        for i in range(len(time_points)):
            if i < len(df):
                # Use actual anomaly data if available
                anomaly_rate = (df['is_anomaly'].iloc[:i+1].sum() / (i+1)) * 100
                anomaly_rate_data.append(int(anomaly_rate * 10))  # Scale for visualization
            else:
                # Extend with realistic pattern
                base_rate = (df['is_anomaly'].sum() / len(df)) * 100
                noise = np.random.normal(0, 5)
                anomaly_rate_data.append(int(max(0, base_rate * 10 + noise)))
    else:
        # Fallback data
        for i in range(len(time_points)):
            value = np.random.normal(15, 5)  # 15% base anomaly rate
            anomaly_rate_data.append(int(max(0, value)))
    
    # Log Severity Distribution (two lines) - based on actual log content
    error_severity_data = []
    warning_severity_data = []
    if 'logline' in df.columns and len(df) > 0:
        log_lines = df['logline'].astype(str)
        error_count = len(log_lines[log_lines.str.contains(r'\b(error|exception|fail)\b', case=False, regex=True)])
        warning_count = len(log_lines[log_lines.str.contains(r'\b(warning|warn)\b', case=False, regex=True)])
        
        for i in range(len(time_points)):
            if i < len(df):
                # Use actual severity data
                current_errors = len(log_lines.iloc[:i+1][log_lines.iloc[:i+1].str.contains(r'\b(error|exception|fail)\b', case=False, regex=True)])
                current_warnings = len(log_lines.iloc[:i+1][log_lines.iloc[:i+1].str.contains(r'\b(warning|warn)\b', case=False, regex=True)])
                error_severity_data.append(current_errors)
                warning_severity_data.append(current_warnings)
            else:
                # Extend with realistic pattern
                error_severity_data.append(error_count + int(np.random.normal(0, 2)))
                warning_severity_data.append(warning_count + int(np.random.normal(0, 2)))
    else:
        # Fallback data
        for i in range(len(time_points)):
            error_severity_data.append(int(np.random.normal(10, 3)))
            warning_severity_data.append(int(np.random.normal(15, 4)))
    
    # Processing Time Variance (blue line) - based on actual processing data
    processing_variance_data = []
    if 'processing_time_seconds' in df.columns and len(df) > 0:
        try:
            # Convert to numeric, handling any string concatenation issues
            processing_times = pd.to_numeric(df['processing_time_seconds'], errors='coerce')
            processing_times = processing_times.dropna()
            
            if len(processing_times) > 0:
                for i in range(len(time_points)):
                    if i < len(processing_times):
                        # Use actual processing time variance
                        variance = processing_times.iloc[:i+1].var() * 1000  # Convert to ms
                        processing_variance_data.append(int(variance if not np.isnan(variance) else 0))
                    else:
                        # Extend with realistic pattern
                        base_variance = processing_times.var() * 1000
                        noise = np.random.normal(0, base_variance * 0.1)
                        processing_variance_data.append(int(max(0, base_variance + noise)))
            else:
                # Fallback data if no valid processing times
                for i in range(len(time_points)):
                    value = np.random.normal(30000, 5000)
                    processing_variance_data.append(int(max(0, value)))
        except Exception as e:
            print(f"Error processing processing_time_seconds in time series: {e}")
            # Fallback data
            for i in range(len(time_points)):
                value = np.random.normal(30000, 5000)
                processing_variance_data.append(int(max(0, value)))
    else:
        # Fallback data
        for i in range(len(time_points)):
            value = np.random.normal(30000, 5000)
            processing_variance_data.append(int(max(0, value)))
    
    # Log Pattern Complexity (purple line) - based on actual log patterns
    pattern_complexity_data = []
    if 'logline' in df.columns and len(df) > 0:
        log_lines = df['logline'].astype(str)
        for i in range(len(time_points)):
            if i < len(df):
                # Calculate complexity based on unique patterns and length
                current_logs = log_lines.iloc[:i+1]
                unique_patterns = current_logs.nunique()
                avg_length = current_logs.str.len().mean()
                complexity = (unique_patterns * avg_length) / 100  # Normalize
                pattern_complexity_data.append(int(complexity))
            else:
                # Extend with realistic pattern
                base_complexity = (log_lines.nunique() * log_lines.str.len().mean()) / 100
                noise = np.random.normal(0, base_complexity * 0.2)
                pattern_complexity_data.append(int(max(0, base_complexity + noise)))
    else:
        # Fallback data
        for i in range(len(time_points)):
            if i < 10:  # Initial spike
                value = np.random.normal(1500, 200)
            else:  # Settled state
                value = np.random.normal(1000, 200)
            pattern_complexity_data.append(int(max(0, value)))
    
    return {
        'time_points': [t.strftime('%H:%M:%S') for t in time_points],
        'anomaly_rate': {
            'label': 'Anomaly Rate (%)',
            'data': anomaly_rate_data,
            'color': '#10B981'  # Green
        },
        'severity_distribution': {
            'errors': {
                'label': 'Error Logs',
                'data': error_severity_data,
                'color': '#EF4444'  # Red
            },
            'warnings': {
                'label': 'Warning Logs',
                'data': warning_severity_data,
                'color': '#F59E0B'  # Orange
            }
        },
        'processing_variance': {
            'label': 'Processing Time Variance (ms)',
            'data': processing_variance_data,
            'color': '#3B82F6'  # Blue
        },
        'pattern_complexity': {
            'label': 'Log Pattern Complexity',
            'data': pattern_complexity_data,
            'color': '#8B5CF6'  # Purple
        }
    }

def generate_table_data(df):
    """Generate table data for the right panel based on actual log data"""
    table_data = []
    
    if len(df) > 0:
        # Get actual data from the DataFrame
        total_logs = len(df)
        anomaly_count = df['is_anomaly'].sum() if 'is_anomaly' in df.columns else 0
        
        # Calculate processing time if available
        if 'processing_time_seconds' in df.columns:
            try:
                # Convert to numeric, handling any string concatenation issues
                processing_times = pd.to_numeric(df['processing_time_seconds'], errors='coerce')
                processing_times = processing_times.dropna()
                
                if len(processing_times) > 0:
                    avg_processing_time = processing_times.mean()
                    max_processing_time = processing_times.max()
                    processing_variance = processing_times.var()
                else:
                    avg_processing_time = 2.4
                    max_processing_time = 5.0
                    processing_variance = 1.0
            except Exception as e:
                print(f"Error processing processing_time_seconds in table data: {e}")
                avg_processing_time = 2.4
                max_processing_time = 5.0
                processing_variance = 1.0
        else:
            avg_processing_time = 2.4
            max_processing_time = 5.0
            processing_variance = 1.0
        
        # Calculate log pattern complexity
        if 'logline' in df.columns:
            log_lines = df['logline'].astype(str)
            unique_patterns = log_lines.nunique()
            avg_length = log_lines.str.len().mean()
            complexity = (unique_patterns * avg_length) / 100
        else:
            unique_patterns = 1
            complexity = 1000
        
        # Count severity levels
        error_count = 0
        warning_count = 0
        if 'logline' in df.columns:
            log_lines = df['logline'].astype(str)
            error_count = len(log_lines[log_lines.str.contains(r'\b(error|exception|fail)\b', case=False, regex=True)])
            warning_count = len(log_lines[log_lines.str.contains(r'\b(warning|warn)\b', case=False, regex=True)])
        
        # Create table entry based on actual data
        table_data.append({
            'log_pattern': f'Pattern-{unique_patterns}',
            'version': '1.0.1-analysis',
            'severity_levels': error_count + warning_count,
            'processing_time_ms': int(avg_processing_time * 1000),
            'processing_variance_ms': int(processing_variance * 1000),
            'pattern_complexity': int(complexity)
        })
    else:
        # Fallback data if no results
        table_data.append({
            'log_pattern': 'No Data',
            'version': '1.0.1-analysis',
            'severity_levels': 0,
            'processing_time_ms': 2400,
            'processing_variance_ms': 1000,
            'pattern_complexity': 1000
        })
    
    return table_data

@main.route('/summarize')
@login_required
def summarize():
    """Summarize log data using local T5 model"""
    try:
        # Get log data from session or request
        log_data = request.args.get('logs', '')
        if not log_data:
            # Try to get from session
            analysis_results = session.get('analysis_results', [])
            if analysis_results:
                # Extract log lines from analysis results
                log_lines = []
                for result in analysis_results[:50]:  # Limit to first 50 for summarization
                    if 'logline' in result:
                        log_lines.append(str(result['logline']))
                log_data = ' '.join(log_lines)
            else:
                return jsonify({'error': 'No log data available for summarization'}), 400
        
        # Load local model
        model_path = 'flashlog/models/t5-small'
        if not os.path.exists(model_path):
            return jsonify({'error': 'Local model not found. Please download the model first.'}), 500
        
        # Create summarization pipeline
        summarizer = pipeline('summarization', model=model_path)
        
        # Truncate if too long (T5 has input limits)
        if len(log_data) > 5000:
            log_data = log_data[:5000] + "..."
        
        # Generate summary
        summary = summarizer(log_data, max_length=150, min_length=50, do_sample=False)[0]['summary_text']
        
        # Log the activity
        user = get_current_user()
        if user:
            log_user_activity(
                user_id=user['id'],
                activity_type='log_summarization',
                description='Generated log summary using T5 model',
                details=f'Summary length: {len(summary)} characters',
                status='success',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
        
        return jsonify({
            'summary': summary,
            'original_length': len(log_data),
            'summary_length': len(summary),
            'model': 't5-small'
        })
        
    except Exception as e:
        print(f"Error in summarization: {str(e)}")
        return jsonify({'error': f'Summarization failed: {str(e)}'}), 500

@main.route('/summarize-ui')
@login_required
def summarize_ui():
    """Serve summarization UI page"""
    return render_template('summarize.html')
