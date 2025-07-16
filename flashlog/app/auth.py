from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from datetime import datetime, timedelta
import uuid
import re

auth = Blueprint('auth', __name__)

def init_db():
    """Initialize the database with users table"""
    db_path = 'flashlog/users.db'
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            role TEXT DEFAULT 'user'
        )
    ''')
    
    # Create sessions table for better session management
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            session_token TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create user activity table for tracking user actions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            activity_type TEXT NOT NULL,
            description TEXT NOT NULL,
            details TEXT,
            status TEXT DEFAULT 'success',
            ip_address TEXT,
            user_agent TEXT,
            file_name TEXT,
            file_size INTEGER,
            processing_time REAL,
            anomalies_detected INTEGER,
            total_logs INTEGER,
            old_value TEXT,
            new_value TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect('flashlog/users.db')
    conn.row_factory = sqlite3.Row
    return conn

@auth.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Input validation and sanitization
        if not username or not email or not password:
            flash('All fields are required!', 'error')
            return render_template('auth/auth.html')
        
        # Sanitize inputs
        username = username.strip()
        email = email.strip().lower()
        
        # Validate username format
        if not re.match(r'^[a-zA-Z0-9_]{3,20}$', username):
            flash('Username must be 3-20 characters long and contain only letters, numbers, and underscores!', 'error')
            return render_template('auth/auth.html')
        
        # Validate email format
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            flash('Please enter a valid email address!', 'error')
            return render_template('auth/auth.html')
        
        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return render_template('auth/auth.html')
        
        # Enhanced password validation
        if len(password) < 12:
            flash('Password must be at least 12 characters long!', 'error')
            return render_template('auth/auth.html')
        
        # Check password complexity
        if not re.search(r'[A-Z]', password):
            flash('Password must contain at least one uppercase letter!', 'error')
            return render_template('auth/auth.html')
        
        if not re.search(r'[a-z]', password):
            flash('Password must contain at least one lowercase letter!', 'error')
            return render_template('auth/auth.html')
        
        if not re.search(r'\d', password):
            flash('Password must contain at least one number!', 'error')
            return render_template('auth/auth.html')
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            flash('Password must contain at least one special character!', 'error')
            return render_template('auth/auth.html')
        
        # Check if user already exists
        conn = get_db_connection()
        existing_user = conn.execute(
            'SELECT * FROM users WHERE username = ? OR email = ?', 
            (username, email)
        ).fetchone()
        conn.close()
        
        if existing_user:
            flash('Username or email already exists!', 'error')
            return render_template('auth/auth.html')
        
        # Create new user
        password_hash = generate_password_hash(password)
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
            (username, email, password_hash)
        )
        conn.commit()
        
        # Get the newly created user ID for logging
        new_user = conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        # Log user registration activity
        if new_user and new_user['id']:
            from .routes import log_user_activity
            log_user_activity(
                user_id=new_user['id'],
                activity_type='registration',
                description=f'New user account created',
                details=f'Registration completed for username: {username}, email: {email}',
                status='success',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent', 'Unknown')
            )
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/auth.html')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember') == 'on'
        
        if not username or not password:
            flash('Please enter both username and password!', 'error')
            return render_template('auth/auth.html')
        
        # Check for account lockout
        conn = get_db_connection()
        
        # Check failed login attempts in last 15 minutes
        failed_attempts = conn.execute('''
            SELECT COUNT(*) as count FROM user_activities 
            WHERE activity_type = 'login' AND status = 'failed' 
            AND user_id = (SELECT id FROM users WHERE username = ?)
            AND created_at >= datetime('now', '-15 minutes')
        ''', (username,)).fetchone()['count']
        
        # Lock account after 5 failed attempts
        if failed_attempts >= 5:
            flash('Account temporarily locked due to too many failed login attempts. Please try again in 15 minutes.', 'error')
            conn.close()
            return render_template('auth/auth.html')
        
        user = conn.execute(
            'SELECT * FROM users WHERE username = ? AND is_active = 1', 
            (username,)
        ).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password_hash'], password):
            # Log successful login (will be logged after session creation)
            pass
        else:
            # Log failed login attempt
            if user:
                from .routes import log_user_activity
                log_user_activity(
                    user_id=user['id'],
                    activity_type='login',
                    description=f'Failed login attempt',
                    details=f'Invalid password for user: {username}',
                    status='failed',
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent', 'Unknown')
                )
            else:
                # Log failed login for non-existent user
                from .routes import log_user_activity
                log_user_activity(
                    user_id=0,  # No user ID for non-existent user
                    activity_type='login',
                    description=f'Failed login attempt for non-existent user',
                    details=f'Username not found: {username}',
                    status='failed',
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent', 'Unknown')
                )
            
            flash('Invalid username or password!', 'error')
            return render_template('auth/auth.html')
        
        if user and check_password_hash(user['password_hash'], password):
            # Create session
            session_token = str(uuid.uuid4())
            session_duration = timedelta(days=30) if remember else timedelta(hours=24)
            expires_at = datetime.now() + session_duration
            
            conn = get_db_connection()
            conn.execute(
                'INSERT INTO user_sessions (user_id, session_token, expires_at) VALUES (?, ?, ?)',
                (user['id'], session_token, expires_at)
            )
            conn.execute(
                'UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?',
                (user['id'],)
            )
            conn.commit()
            conn.close()
            
            # Set session
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['session_token'] = session_token
            session['role'] = user['role']
            
            # Log login activity with enhanced details
            from .routes import log_user_activity
            log_user_activity(
                user_id=user['id'],
                activity_type='login',
                description=f'User logged in successfully',
                details=f'Login from session: {session_token[:8]}...',
                status='success',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent', 'Unknown')
            )
            
            flash(f'Welcome back, {user["username"]}!', 'success')
            return redirect(url_for('main.index'))
        else:
            flash('Invalid username or password!', 'error')
    
    return render_template('auth/auth.html')

@auth.route('/logout')
def logout():
    """User logout with secure session termination"""
    if 'session_token' in session:
        # Remove session from database
        conn = get_db_connection()
        conn.execute(
            'DELETE FROM user_sessions WHERE session_token = ?',
            (session['session_token'],)
        )
        conn.commit()
        conn.close()
    
    # Log logout activity before clearing session
    if 'user_id' in session:
        from .routes import log_user_activity
        log_user_activity(
            user_id=session['user_id'],
            activity_type='logout',
            description=f'User logged out',
            details=f'Logout from session: {session.get("session_token", "")[:8] if session.get("session_token") else "unknown"}...',
            status='success',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', 'Unknown')
        )
    
    # Clear session completely
    session.clear()
    
    # Set cache control headers to prevent back button access
    response = redirect(url_for('auth.auth_page'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    
    flash('You have been logged out successfully!', 'success')
    return response

@auth.route('/auth')
def auth_page():
    """Combined authentication page"""
    # If user is already logged in, redirect to main page
    if 'user_id' in session:
        return redirect(url_for('main.index'))
    
    return render_template('auth/auth.html')

def login_required(f):
    """Decorator to require login for routes"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page!', 'error')
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
                flash('Your session has expired. Please log in again!', 'error')
                return redirect(url_for('auth.auth_page'))
        
        return f(*args, **kwargs)
    
    return decorated_function

def admin_required(f):
    """Decorator to require admin role for routes"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'role' not in session or session['role'] != 'admin':
            flash('Admin access required!', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    
    return decorated_function

def get_current_user():
    """Get current user information"""
    if 'user_id' not in session:
        return None
    
    conn = get_db_connection()
    user = conn.execute(
        'SELECT * FROM users WHERE id = ? AND is_active = 1', 
        (session['user_id'],)
    ).fetchone()
    conn.close()
    
    if user:
        # Convert datetime strings to datetime objects
        try:
            if user['created_at']:
                user = dict(user)  # Convert to dict to make it mutable
                user['created_at'] = datetime.strptime(user['created_at'], '%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError):
            pass
        
        try:
            if user['last_login']:
                user = dict(user) if not isinstance(user, dict) else user
                user['last_login'] = datetime.strptime(user['last_login'], '%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError):
            pass
    
    return user

@auth.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile page with update functionality"""
    user = get_current_user()
    if not user:
        return redirect(url_for('auth.login'))
    
    # Clear any existing flash messages that are not profile-related
    if request.method == 'GET':
        # Get all flash messages and clear them
        from flask import get_flashed_messages
        flashed_messages = get_flashed_messages(with_categories=True)
        
        # Only keep profile-related messages
        profile_messages = []
        for category, message in flashed_messages:
            if any(keyword in message.lower() for keyword in ['profile', 'account', 'password', 'welcome']):
                profile_messages.append((category, message))
        
        # Clear all flash messages and re-add only profile-related ones
        from flask import session
        if '_flashes' in session:
            del session['_flashes']
        
        # Re-add only profile-related messages
        for category, message in profile_messages:
            flash(message, category)
    
    if request.method == 'POST':
        # Handle profile updates
        new_email = request.form.get('email', '').strip().lower()
        new_username = request.form.get('username', '').strip()
        
        # Validate inputs
        if not new_email or not new_username:
            flash('Email and username are required!', 'error')
            return render_template('auth/profile.html', user=user)
        
        # Validate email format
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', new_email):
            flash('Please enter a valid email address!', 'error')
            return render_template('auth/profile.html', user=user)
        
        # Validate username format
        if not re.match(r'^[a-zA-Z0-9_]{3,20}$', new_username):
            flash('Username must be 3-20 characters long and contain only letters, numbers, and underscores!', 'error')
            return render_template('auth/profile.html', user=user)
        
        # Check if email/username already exists (excluding current user)
        conn = get_db_connection()
        existing_user = conn.execute(
            'SELECT * FROM users WHERE (username = ? OR email = ?) AND id != ?', 
            (new_username, new_email, user.get('id', 0))
        ).fetchone()
        conn.close()
        
        if existing_user:
            flash('Username or email already exists!', 'error')
            return render_template('auth/profile.html', user=user)
        
        # Store old values for logging
        old_username = user.get('username', '')
        old_email = user.get('email', '')
        
        # Update profile
        conn = get_db_connection()
        conn.execute(
            'UPDATE users SET username = ?, email = ? WHERE id = ?',
            (new_username, new_email, user.get('id', 0))
        )
        conn.commit()
        conn.close()
        
        # Log profile update activity
        from .routes import log_user_activity
        changes = []
        if old_username != new_username:
            changes.append(f"username: {old_username} → {new_username}")
        if old_email != new_email:
            changes.append(f"email: {old_email} → {new_email}")
        
        log_user_activity(
            user_id=user.get('id', 0),
            activity_type='profile_update',
            description='Profile information updated',
            details=f'Updated: {", ".join(changes)}',
            status='success',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', 'Unknown'),
            old_value=f"username: {old_username}, email: {old_email}",
            new_value=f"username: {new_username}, email: {new_email}"
        )
        
        # Update session with new username
        session['username'] = new_username
        
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/profile.html', user=user)

@auth.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change user password"""
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not current_password or not new_password or not confirm_password:
            flash('All fields are required!', 'error')
            return render_template('auth/change_password.html')
        
        if new_password != confirm_password:
            flash('New passwords do not match!', 'error')
            return render_template('auth/change_password.html')
        
        if len(new_password) < 6:
            flash('New password must be at least 6 characters long!', 'error')
            return render_template('auth/change_password.html')
        
        # Verify current password
        user = get_current_user()
        if not user:
            flash('User session invalid. Please log in again!', 'error')
            return render_template('auth/change_password.html')
            
        if not check_password_hash(user['password_hash'], current_password):
            flash('Current password is incorrect!', 'error')
            return render_template('auth/change_password.html')
        
        # Update password
        new_password_hash = generate_password_hash(new_password)
        conn = get_db_connection()
        conn.execute(
            'UPDATE users SET password_hash = ? WHERE id = ?',
            (new_password_hash, user['id'])
        )
        conn.commit()
        conn.close()
        
        # Log password change activity
        from .routes import log_user_activity
        log_user_activity(
            user_id=user.get('id', 0),
            activity_type='password_change',
            description='Password changed successfully',
            details='Password was updated',
            status='success',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', 'Unknown'),
            old_value='[HIDDEN]',
            new_value='[HIDDEN]'
        )
        
        flash('Password changed successfully!', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/change_password.html')

# Initialize database when module is imported
init_db() 