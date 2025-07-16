from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from .auth import admin_required, get_db_connection, login_required
import sqlite3
from datetime import datetime
import re

admin = Blueprint('admin', __name__)

@admin.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Admin dashboard main page"""
    # Get user statistics
    conn = get_db_connection()
    
    # Total users
    total_users = conn.execute('SELECT COUNT(*) as count FROM users').fetchone()['count']
    
    # Active users
    active_users = conn.execute('SELECT COUNT(*) as count FROM users WHERE is_active = 1').fetchone()['count']
    
    # Admin users
    admin_users = conn.execute('SELECT COUNT(*) as count FROM users WHERE role = "admin"').fetchone()['count']
    
    # Recent logins (last 24 hours)
    recent_logins = conn.execute('''
        SELECT COUNT(*) as count FROM users 
        WHERE last_login >= datetime('now', '-1 day')
    ''').fetchone()['count']
    
    conn.close()
    
    return render_template('admin/dashboard.html', 
                         total_users=total_users,
                         active_users=active_users,
                         admin_users=admin_users,
                         recent_logins=recent_logins)

@admin.route('/users')
@login_required
@admin_required
def users():
    """User management page"""
    from datetime import datetime
    
    conn = get_db_connection()
    users_raw = conn.execute('''
        SELECT id, username, email, role, is_active, created_at, last_login 
        FROM users 
        ORDER BY created_at DESC
    ''').fetchall()
    conn.close()
    
    # Convert string dates to datetime objects for template formatting
    users_list = []
    for user in users_raw:
        user_dict = dict(user)
        
        # Add is_admin property for template compatibility
        user_dict['is_admin'] = user_dict['role'] == 'admin'
        
        # Convert created_at string to datetime if it exists
        if user_dict['created_at']:
            try:
                user_dict['created_at'] = datetime.fromisoformat(user_dict['created_at'].replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                user_dict['created_at'] = None
        
        # Convert last_login string to datetime if it exists
        if user_dict['last_login']:
            try:
                user_dict['last_login'] = datetime.fromisoformat(user_dict['last_login'].replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                user_dict['last_login'] = None
        
        users_list.append(user_dict)
    
    return render_template('admin/users.html', users=users_list)

@admin.route('/users/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    """Create new user"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'user')
        
        # Enhanced validation
        if not username or not email or not password:
            flash('All fields are required!', 'error')
            return redirect(url_for('admin.create_user'))
        
        # Sanitize inputs
        username = username.strip()
        email = email.strip().lower()
        
        # Validate username format
        if not re.match(r'^[a-zA-Z0-9_]{3,20}$', username):
            flash('Username must be 3-20 characters long and contain only letters, numbers, and underscores!', 'error')
            return redirect(url_for('admin.create_user'))
        
        # Validate email format
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            flash('Please enter a valid email address!', 'error')
            return redirect(url_for('admin.create_user'))
        
        # Enhanced password validation
        if len(password) < 12:
            flash('Password must be at least 12 characters long!', 'error')
            return redirect(url_for('admin.create_user'))
        
        # Check password complexity
        if not re.search(r'[A-Z]', password):
            flash('Password must contain at least one uppercase letter!', 'error')
            return redirect(url_for('admin.create_user'))
        
        if not re.search(r'[a-z]', password):
            flash('Password must contain at least one lowercase letter!', 'error')
            return redirect(url_for('admin.create_user'))
        
        if not re.search(r'\d', password):
            flash('Password must contain at least one number!', 'error')
            return redirect(url_for('admin.create_user'))
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            flash('Password must contain at least one special character!', 'error')
            return redirect(url_for('admin.create_user'))
        
        if role not in ['user', 'admin']:
            flash('Invalid role selected!', 'error')
            return redirect(url_for('admin.create_user'))
        
        # Check if user already exists
        conn = get_db_connection()
        existing_user = conn.execute(
            'SELECT * FROM users WHERE username = ? OR email = ?', 
            (username, email)
        ).fetchone()
        conn.close()
        
        if existing_user:
            flash('Username or email already exists!', 'error')
            return redirect(url_for('admin.create_user'))
        
        # Create new user
        password_hash = generate_password_hash(password)
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)',
            (username, email, password_hash, role)
        )
        conn.commit()
        conn.close()
        
        flash(f'User "{username}" created successfully!', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('admin/create_user.html')

@admin.route('/users/<int:user_id>/delete', methods=['GET', 'POST'])
@login_required
@admin_required
def delete_user(user_id):
    """Delete user"""
    # Handle GET requests (someone trying to access via URL)
    if request.method == 'GET':
        print(f"DEBUG: GET request to delete user {user_id} from IP {request.remote_addr}")
        flash('Delete action must be performed through the form. Please use the delete button.', 'error')
        return redirect(url_for('admin.users'))
    
    # Prevent admin from deleting themselves
    if user_id == session.get('user_id'):
        flash('You cannot delete your own account!', 'error')
        return redirect(url_for('admin.users'))
    
    conn = get_db_connection()
    user = conn.execute('SELECT username FROM users WHERE id = ?', (user_id,)).fetchone()
    
    if not user:
        flash('User not found!', 'error')
        return redirect(url_for('admin.users'))
    
    try:
        # Delete user activities first (due to foreign key constraint)
        conn.execute('DELETE FROM user_activities WHERE user_id = ?', (user_id,))
        # Delete user sessions
        conn.execute('DELETE FROM user_sessions WHERE user_id = ?', (user_id,))
        # Delete user
        conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()
    except sqlite3.IntegrityError as e:
        conn.close()
        flash(f'Error deleting user: Database constraint violation. {str(e)}', 'error')
        return redirect(url_for('admin.users'))
    except Exception as e:
        conn.close()
        flash(f'Error deleting user: {str(e)}', 'error')
        return redirect(url_for('admin.users'))
    
    # Log the deletion activity
    try:
        from .routes import log_user_activity
        log_user_activity(
            user_id=session.get('user_id'),
            activity_type='admin_action',
            description=f'Deleted user account',
            details=f'Admin deleted user: {user["username"]} (ID: {user_id})',
            status='success',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', 'Unknown')
        )
    except Exception as e:
        # Log error but don't fail the deletion
        print(f"Warning: Could not log user deletion activity: {e}")
    
    flash(f'User "{user["username"]}" deleted successfully!', 'success')
    return redirect(url_for('admin.users'))

@admin.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(user_id):
    """Toggle user active/inactive status"""
    # Prevent admin from deactivating themselves
    if user_id == session.get('user_id'):
        flash('You cannot deactivate your own account!', 'error')
        return redirect(url_for('admin.users'))
    
    conn = get_db_connection()
    user = conn.execute('SELECT username, is_active FROM users WHERE id = ?', (user_id,)).fetchone()
    
    if not user:
        flash('User not found!', 'error')
        return redirect(url_for('admin.users'))
    
    new_status = 0 if user['is_active'] else 1
    status_text = 'activated' if new_status else 'deactivated'
    
    conn.execute('UPDATE users SET is_active = ? WHERE id = ?', (new_status, user_id))
    conn.commit()
    conn.close()
    
    # Log the status change activity
    try:
        from .routes import log_user_activity
        log_user_activity(
            user_id=session.get('user_id'),
            activity_type='admin_action',
            description=f'Changed user status',
            details=f'Admin {status_text} user: {user["username"]} (ID: {user_id})',
            status='success',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', 'Unknown')
        )
    except Exception as e:
        # Log error but don't fail the status change
        print(f"Warning: Could not log user status change activity: {e}")
    
    flash(f'User "{user["username"]}" {status_text} successfully!', 'success')
    return redirect(url_for('admin.users'))

@admin.route('/users/<int:user_id>/change-role', methods=['POST'])
@login_required
@admin_required
def change_user_role(user_id):
    """Change user role"""
    # Prevent admin from changing their own role
    if user_id == session.get('user_id'):
        flash('You cannot change your own role!', 'error')
        return redirect(url_for('admin.users'))
    
    new_role = request.form.get('role')
    if new_role not in ['user', 'admin']:
        flash('Invalid role selected!', 'error')
        return redirect(url_for('admin.users'))
    
    conn = get_db_connection()
    user = conn.execute('SELECT username FROM users WHERE id = ?', (user_id,)).fetchone()
    
    if not user:
        flash('User not found!', 'error')
        return redirect(url_for('admin.users'))
    
    conn.execute('UPDATE users SET role = ? WHERE id = ?', (new_role, user_id))
    conn.commit()
    conn.close()
    
    flash(f'User "{user["username"]}" role changed to {new_role} successfully!', 'success')
    return redirect(url_for('admin.users'))

@admin.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    """Edit user information"""
    from datetime import datetime
    
    conn = get_db_connection()
    user_raw = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    
    if not user_raw:
        flash('User not found!', 'error')
        return redirect(url_for('admin.users'))
    
    # Convert user to dict and handle date conversion
    user = dict(user_raw)
    
    # Convert created_at string to datetime if it exists
    if user['created_at']:
        try:
            user['created_at'] = datetime.fromisoformat(user['created_at'].replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            user['created_at'] = None
    
    # Convert last_login string to datetime if it exists
    if user['last_login']:
        try:
            user['last_login'] = datetime.fromisoformat(user['last_login'].replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            user['last_login'] = None
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        role = request.form.get('role')
        is_active = request.form.get('is_active') == 'on'
        
        # Validation
        if not username or not email:
            flash('Username and email are required!', 'error')
            return redirect(url_for('admin.edit_user', user_id=user_id))
        
        if role not in ['user', 'admin']:
            flash('Invalid role selected!', 'error')
            return redirect(url_for('admin.edit_user', user_id=user_id))
        
        # Check if username/email already exists (excluding current user)
        conn = get_db_connection()
        existing_user = conn.execute(
            'SELECT * FROM users WHERE (username = ? OR email = ?) AND id != ?', 
            (username, email, user_id)
        ).fetchone()
        
        if existing_user:
            flash('Username or email already exists!', 'error')
            conn.close()
            return redirect(url_for('admin.edit_user', user_id=user_id))
        
        # Update user
        conn.execute(
            'UPDATE users SET username = ?, email = ?, role = ?, is_active = ? WHERE id = ?',
            (username, email, role, is_active, user_id)
        )
        conn.commit()
        conn.close()
        
        flash(f'User "{username}" updated successfully!', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('admin/edit_user.html', user=user)

@admin.route('/activities')
@login_required
@admin_required
def activities():
    """Admin activities view - shows all user activities"""
    from datetime import datetime
    
    print("🔍 Admin activities route called")
    
    # Get filter parameters
    activity_type = request.args.get('activity_type', '')
    status = request.args.get('status', '')
    user_id = request.args.get('user_id', '')
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    conn = get_db_connection()
    
    # First, let's check if the user_activities table exists and has data
    try:
        table_check = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_activities'").fetchone()
        if not table_check:
            print("❌ user_activities table does not exist!")
            conn.close()
            return render_template('admin/activities.html', 
                                 activities=[],
                                 activity_types=[],
                                 statuses=[],
                                 users=[],
                                 current_page=1,
                                 total_pages=1,
                                 total_activities=0,
                                 filters={'activity_type': '', 'status': '', 'user_id': ''})
        
        # Check total activities
        total_check = conn.execute("SELECT COUNT(*) as count FROM user_activities").fetchone()
        print(f"📊 Total activities in database: {total_check['count']}")
        
        if total_check['count'] == 0:
            print("⚠️ No activities found in database")
            conn.close()
            return render_template('admin/activities.html', 
                                 activities=[],
                                 activity_types=[],
                                 statuses=[],
                                 users=[],
                                 current_page=1,
                                 total_pages=1,
                                 total_activities=0,
                                 filters={'activity_type': '', 'status': '', 'user_id': ''})
        
    except Exception as e:
        print(f"❌ Error checking database: {str(e)}")
        conn.close()
        return render_template('admin/activities.html', 
                             activities=[],
                             activity_types=[],
                             statuses=[],
                             users=[],
                             current_page=1,
                             total_pages=1,
                             total_activities=0,
                             filters={'activity_type': '', 'status': '', 'user_id': ''})
    
    # Build the query with filters
    query = '''
        SELECT ua.*, u.username 
        FROM user_activities ua 
        LEFT JOIN users u ON ua.user_id = u.id
        WHERE 1=1
    '''
    params = []
    
    if activity_type:
        query += ' AND ua.activity_type = ?'
        params.append(activity_type)
    
    if status:
        query += ' AND ua.status = ?'
        params.append(status)
    
    if user_id:
        query += ' AND ua.user_id = ?'
        params.append(user_id)
    
    # Get total count for pagination
    count_query = f"SELECT COUNT(*) as count FROM ({query})"
    total_activities = conn.execute(count_query, params).fetchone()['count']
    print(f"📊 Activities matching filters: {total_activities}")
    
    # Add ordering and pagination
    query += ' ORDER BY ua.created_at DESC LIMIT ? OFFSET ?'
    params.extend([per_page, (page - 1) * per_page])
    
    activities_raw = conn.execute(query, params).fetchall()
    print(f"📊 Retrieved {len(activities_raw)} activities for display")
    
    # Get unique activity types and statuses for filter dropdowns
    activity_types = conn.execute('SELECT DISTINCT activity_type FROM user_activities ORDER BY activity_type').fetchall()
    statuses = conn.execute('SELECT DISTINCT status FROM user_activities ORDER BY status').fetchall()
    users = conn.execute('SELECT id, username FROM users ORDER BY username').fetchall()
    
    conn.close()
    
    # Convert activities to list of dicts for template
    activities_list = []
    for activity in activities_raw:
        activity_dict = dict(activity)
        
        # Convert created_at string to datetime if it exists
        if activity_dict['created_at']:
            try:
                activity_dict['created_at'] = datetime.fromisoformat(activity_dict['created_at'].replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                activity_dict['created_at'] = None
        
        activities_list.append(activity_dict)
    
    # Calculate pagination
    total_pages = (total_activities + per_page - 1) // per_page
    
    return render_template('admin/activities.html', 
                         activities=activities_list,
                         activity_types=activity_types,
                         statuses=statuses,
                         users=users,
                         current_page=page,
                         total_pages=total_pages,
                         total_activities=total_activities,
                         filters={
                             'activity_type': activity_type,
                             'status': status,
                             'user_id': user_id
                         })

@admin.route('/users/<int:user_id>/reset-password', methods=['POST'])
@login_required
@admin_required
def reset_user_password(user_id):
    """Reset user password"""
    new_password = request.form.get('new_password')
    
    if not new_password or len(new_password) < 6:
        flash('Password must be at least 6 characters long!', 'error')
        return redirect(url_for('admin.users'))
    
    conn = get_db_connection()
    user = conn.execute('SELECT username FROM users WHERE id = ?', (user_id,)).fetchone()
    
    if not user:
        flash('User not found!', 'error')
        return redirect(url_for('admin.users'))
    
    password_hash = generate_password_hash(new_password)
    conn.execute('UPDATE users SET password_hash = ? WHERE id = ?', (password_hash, user_id))
    conn.commit()
    conn.close()
    
    flash(f'Password for user "{user["username"]}" reset successfully!', 'success')
    return redirect(url_for('admin.users')) 