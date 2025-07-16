from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, session, make_response, jsonify
import os
import glob
import pandas as pd
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from .logai_handler import process_log_file
from .auth import login_required, get_current_user, get_db_connection
import numpy as np

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
    
    return redirect(url_for('main.index'))

def compute_dashboard_metrics():
    """Compute dashboard metrics from all previous analysis results"""
    uploads_dir = 'uploads'
    anomaly_files = glob.glob(os.path.join(uploads_dir, 'anomaly_results_*.csv'))
    
    total_logs = 0
    total_anomalies = 0
    total_processing_time = 0
    file_count = 0
    processing_times = []
    
    for file_path in anomaly_files:
        try:
            df = pd.read_csv(file_path)
            if not df.empty:
                total_logs += len(df)
                if 'is_anomaly' in df.columns:
                    total_anomalies += df['is_anomaly'].sum()
                
                # Get processing time if available
                if 'processing_time_seconds' in df.columns:
                    processing_time = df['processing_time_seconds'].iloc[0]  # Same for all rows in file
                    processing_times.append(processing_time)
                    total_processing_time += processing_time
                
                file_count += 1
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
    
    # Calculate metrics
    success_rate = ((total_logs - total_anomalies) / total_logs * 100) if total_logs > 0 else 0
    
    # Calculate average processing time
    if processing_times:
        avg_processing_time = sum(processing_times) / len(processing_times)
    else:
        avg_processing_time = 2.4  # Default fallback
    
    # Calculate month-over-month change (simplified)
    # For now, we'll use a simple calculation based on file count
    if file_count > 0:
        # Estimate based on number of files processed
        growth_rate = min(15.1, max(-10, (file_count - 1) * 5))  # Between -10% and +15%
    else:
        growth_rate = 0
    
    return {
        'total_logs': total_logs,
        'total_anomalies': total_anomalies,
        'success_rate': round(success_rate, 1),
        'avg_processing_time': round(avg_processing_time, 1),
        'growth_rate': growth_rate,
        'files_processed': file_count
    }

@main.route('/dashboard', methods=['GET', 'POST'])
def index():
    # Authentication is now handled in before_request
    # User is authenticated, proceed with the original functionality
    
    # Check if user is admin and redirect to admin dashboard
    if session.get('role') == 'admin':
        return redirect(url_for('admin.dashboard'))
    
    # Compute dashboard metrics for regular users
    dashboard_metrics = compute_dashboard_metrics()

    if request.method == 'POST':
        print("📝 POST request received")
        print(f"   - Content-Type: {request.content_type}")
        print(f"   - Form data keys: {list(request.form.keys())}")
        print(f"   - Files: {list(request.files.keys())}")
        
        parser = request.form.get("parser", "drain")
        model = request.form.get("model", "isolation_forest")
        user_index = request.form.get("index_name", "").strip()
        index_name = user_index if user_index else f"logai-{datetime.utcnow().strftime('%Y-%m-%d')}"
        
        print(f"   - Parser: {parser}")
        print(f"   - Model: {model}")
        print(f"   - Index: {index_name}")

        file = request.files.get('logfile')
        if not file:
            print("❌ No file uploaded")
            flash('No file uploaded.', 'error')
            return redirect(url_for('main.index'))

        # File upload security validation
        ALLOWED_EXTENSIONS = {'log', 'txt', 'csv'}
        MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
        
        def allowed_file(filename):
            return '.' in filename and \
                   filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
        
        # Check file extension
        if not allowed_file(file.filename):
            flash('Invalid file type. Only .log, .txt, and .csv files are allowed.', 'error')
            return redirect(url_for('main.index'))
        
        # Check file size
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        
        if file_size > MAX_FILE_SIZE:
            flash(f'File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB.', 'error')
            return redirect(url_for('main.index'))
        
        # Secure filename and save
        filename = secure_filename(file.filename or 'unknown_file')
        filepath = os.path.join('uploads', filename)
        print(f"   - Saving file: {filepath}")
        file.save(filepath)
        print(f"   - File saved successfully")

        try:
            print("🔍 Starting log analysis...")
            result_data, csv_path = process_log_file(filepath, parser, model, index_name)
            print("✅ Log analysis completed successfully")
        except KeyError as e:
            print(f"❌ KeyError during analysis: {str(e)}")
            # Log failed analysis attempt
            user = get_current_user()
            if user:
                log_user_activity(
                    user_id=user['id'],
                    activity_type='log_analysis',
                    description=f'Failed to analyze log file: {filename}',
                    details=f'KeyError: {str(e)}',
                    status='failed',
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent', 'Unknown'),
                    file_name=filename
                )
            flash(f'Analysis failed: {str(e)}', 'error')
            return redirect(url_for('main.index'))
        except Exception as e:
            print(f"❌ Exception during analysis: {str(e)}")
            import traceback
            traceback.print_exc()
            # Log failed analysis attempt
            user = get_current_user()
            if user:
                log_user_activity(
                    user_id=user['id'],
                    activity_type='log_analysis',
                    description=f'Failed to analyze log file: {filename}',
                    details=f'Exception: {str(e)}',
                    status='failed',
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent', 'Unknown'),
                    file_name=filename
                )
            flash(f'Error during analysis: {str(e)}', 'error')
            return redirect(url_for('main.index'))

        print("📊 Processing results...")
        num_logs = len(result_data)
        num_anomalies = result_data["is_anomaly"].sum()
        print(f"   - Total logs: {num_logs}")
        print(f"   - Anomalies: {num_anomalies}")
        
        # Debug: Check the actual boolean values
        print("🔍 Debug: Checking anomaly values...")
        anomaly_values = result_data["is_anomaly"].value_counts()
        print(f"   - Anomaly value counts: {anomaly_values.to_dict()}")
        print(f"   - Sample anomaly values: {result_data['is_anomaly'].head(10).tolist()}")

        if "timestamp" not in result_data.columns or result_data["timestamp"].isnull().all():
            print("⚠️ Timestamp column missing in file — using system time instead.")

        # Convert DataFrame to JSON-serializable format
        print("💾 Converting results to JSON-serializable format...")
        results_dict = []
        for _, row in result_data.iterrows():
            row_dict = {}
            for col, value in row.items():
                if pd.isna(value):
                    row_dict[col] = None
                elif hasattr(value, 'item'):  # Handle numpy types
                    row_dict[col] = value.item()
                elif col == 'is_anomaly':  # Handle anomaly flag specifically
                    # Convert to proper boolean: 1.0/1 = True, 0.0/0 = False
                    if isinstance(value, (int, float)):
                        row_dict[col] = bool(value)
                    elif isinstance(value, str):
                        row_dict[col] = float(value) == 1.0
                    else:
                        row_dict[col] = bool(value)
                elif isinstance(value, bool):  # Handle other boolean values properly
                    row_dict[col] = bool(value)
                else:
                    row_dict[col] = str(value)
            results_dict.append(row_dict)
        
        print(f"💾 Converted {len(results_dict)} results to JSON format")
        
        # Debug: Check JSON conversion preserved boolean values
        print("🔍 Debug: Checking JSON conversion...")
        anomaly_count_in_json = sum(1 for r in results_dict if r.get('is_anomaly') is True)
        print(f"   - Anomalies in JSON: {anomaly_count_in_json}")
        print(f"   - Sample JSON anomaly values: {[r.get('is_anomaly') for r in results_dict[:10]]}")
        
        # Check if this is an AJAX request (X-Requested-With header)
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        # Always redirect to separate page for better user experience
        # Store results in session for traditional form submission
        print("💾 Storing data in session...")
        print(f"   - Session before storing: {list(session.keys())}")
        
        try:
            # Set session timeout based on user preference
            session.permanent = True
            session.modified = True  # Update session timestamp
            
            # Store only essential data in session to avoid size limits
            session['analysis_file'] = csv_path  # Store the CSV file path
            session['kibana_url'] = f"http://localhost:5601/app/discover#/?_a=(index:'{index_name}',columns:!(_source))"
            session['analysis_summary'] = {
                'total_logs': int(num_logs),
                'total_anomalies': int(num_anomalies),
                'success_rate': round(((num_logs - num_anomalies) / num_logs * 100), 1),
                'index_name': index_name
            }
            
            print(f"   - Session after storing: {list(session.keys())}")
            print(f"   - Analysis file in session: {session.get('analysis_file')}")
            print(f"   - CSV path: {csv_path}")
            print(f"   - Analysis summary in session: {session.get('analysis_summary')}")
            print(f"   - Session data types: analysis_file={type(session.get('analysis_file'))}, summary={type(session.get('analysis_summary'))}")

            print(f"✅ Analysis completed successfully. Results stored in session.")
            print(f"   - Total logs: {num_logs}")
            print(f"   - Anomalies: {num_anomalies}")
            print(f"   - Results count: {len(results_dict)}")
            print(f"   - Session keys: {list(session.keys())}")

            # Log user activity with enhanced details
            user = get_current_user()
            if user:
                file_size = os.path.getsize(filepath) if os.path.exists(filepath) else None
                log_user_activity(
                    user_id=user['id'],
                    activity_type='log_analysis',
                    description=f'Analyzed log file: {filename}',
                    details=f'Parser: {parser}, Model: {model}, Index: {index_name}',
                    status='success',
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent', 'Unknown'),
                    file_name=filename,
                    file_size=file_size,
                    processing_time=None,  # Could be calculated if needed
                    anomalies_detected=int(num_anomalies),
                    total_logs=int(num_logs)
                )

            # Always redirect to separate results page
            flash(f"✅ {num_logs} log entries processed. {num_anomalies} anomalies detected. Sent to index: {index_name}")
            print("🔄 Redirecting to /analyzed-logs...")
            print(f"   - Final session check before redirect: {list(session.keys())}")
            return redirect(url_for('main.analyzed_logs'))
            
        except Exception as e:
            print(f"❌ Error storing results in session: {str(e)}")
            import traceback
            traceback.print_exc()
            flash(f"Error processing results: {str(e)}", 'error')
            return redirect(url_for('main.index'))

    return render_template('index.html', metrics=dashboard_metrics)

@main.route('/analyzed-logs')
@login_required
def analyzed_logs():
    """Display analysis results with pagination"""
    print("🔍 Analyzed logs route called")
    print(f"   - Request method: {request.method}")
    print(f"   - Request URL: {request.url}")
    print(f"   - Session ID: {session.get('_id', 'No session ID')}")
    print(f"   - All session keys: {list(session.keys())}")
    
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Get data from session
    analysis_file = session.get('analysis_file')
    kibana_url = session.get('kibana_url')
    analysis_summary = session.get('analysis_summary', {})
    
    print(f"   - Analysis file in session: {analysis_file}")
    print(f"   - Analysis summary: {analysis_summary}")
    print(f"   - All session keys: {list(session.keys())}")
    
    if not analysis_file or not os.path.exists(analysis_file):
        print("❌ No analysis file found in session or file doesn't exist, redirecting to index")
        print(f"   - Session keys available: {list(session.keys())}")
        print(f"   - analysis_file key exists: {'analysis_file' in session}")
        flash('No analysis results found. Please upload and analyze a log file first.')
        return redirect(url_for('main.index'))
    
    # Load results from the CSV file
    try:
        print(f"📂 Loading results from file: {analysis_file}")
        results_df = pd.read_csv(analysis_file)
        results = []
        
        for _, row in results_df.iterrows():
            row_dict = {}
            for col, value in row.items():
                if pd.isna(value):
                    row_dict[col] = None
                elif hasattr(value, 'item'):  # Handle numpy types
                    row_dict[col] = value.item()
                elif col == 'is_anomaly':  # Handle anomaly flag specifically
                    if isinstance(value, (int, float)):
                        row_dict[col] = bool(value)
                    elif isinstance(value, str):
                        row_dict[col] = float(value) == 1.0
                    else:
                        row_dict[col] = bool(value)
                elif isinstance(value, bool):
                    row_dict[col] = bool(value)
                else:
                    row_dict[col] = str(value)
            results.append(row_dict)
        
        print(f"✅ Loaded {len(results)} results from file")
        
    except Exception as e:
        print(f"❌ Error loading results from file: {str(e)}")
        flash('Error loading analysis results. Please try again.', 'error')
        return redirect(url_for('main.index'))
    
    # Ensure timestamps are strings to prevent template errors
    for result in results:
        if 'timestamp' in result and result['timestamp'] is not None:
            if isinstance(result['timestamp'], (int, float)):
                # Convert Unix timestamp to ISO format
                result['timestamp'] = datetime.fromtimestamp(result['timestamp']).isoformat()
            elif not isinstance(result['timestamp'], str):
                # Convert any other type to string
                result['timestamp'] = str(result['timestamp'])
    
    # Pagination
    total_results = len(results)
    total_pages = (total_results + per_page - 1) // per_page
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_results = results[start_idx:end_idx]
    
    # Set cache headers to prevent caching issues
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
        return redirect(url_for('main.index'))
    
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
    activities = conn.execute('''
        SELECT * FROM user_activities 
        WHERE user_id = ? AND id > ? 
        ORDER BY created_at DESC 
        LIMIT 10
    ''', (user['id'], last_id)).fetchall()
    
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
