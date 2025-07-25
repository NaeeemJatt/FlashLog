from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from datetime import datetime, timedelta
import uuid
import re
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Length, EqualTo, Regexp
from flask_limiter.util import get_remote_address  # If needed

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
    
    # Create analysis_runs table for storing analysis results
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analysis_runs (
            run_id TEXT PRIMARY KEY,
            user_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            results_json TEXT NOT NULL,
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
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember') == 'on'
        # Validate input
        if not username or not password:
            flash('Please provide both username and password.', 'error')
            return redirect(url_for('auth.login'))
        # Check user in database
        print(f"[DEBUG] Attempting login for username: {username}")
        conn = get_db_connection()
        user_row = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        if user_row:
            print(f"[DEBUG] Username {username} found in database.")
            # Convert sqlite3.Row to dictionary
            user = dict(user_row)
            # Check for password field under different possible names
            password_field = None
            for field in ['password', 'password_hash', 'hashed_password']:
                if field in user:
                    password_field = field
                    break
            if password_field:
                print(f"[DEBUG] Password field '{password_field}' exists for user {username}, checking hash.")
                if check_password_hash(user[password_field], password):
                    print(f"[DEBUG] Password hash matches for user {username}.")
                    # Check if account is locked, default to False if key doesn't exist
                    if user.get('locked', False):
                        print(f"[DEBUG] Account for user {username} is locked.")
                        flash('Account is locked. Please contact support.', 'error')
                        return redirect(url_for('auth.login'))
                    session['user_id'] = user['id']
                    session['username'] = user['username']
                    session['role'] = user.get('role', 'user')  # Default to 'user' if role not set
                    session['session_token'] = str(uuid.uuid4())  # Generate a unique session token
                    session.permanent = remember  # Make session permanent if 'remember' is checked
                    print(f"[DEBUG] Session created for user {username} with token {session['session_token'][:8]}... and permanent={remember}")
                    # Insert session into user_sessions table
                    from datetime import datetime, timedelta
                    expires_at = datetime.now() + timedelta(hours=1)
                    conn = get_db_connection()
                    conn.execute(
                        'INSERT INTO user_sessions (user_id, session_token, expires_at) VALUES (?, ?, ?)',
                        (user['id'], session['session_token'], expires_at)
                    )
                    conn.commit()
                    conn.close()
                    # Log the login activity
                    try:
                        conn = get_db_connection()
                        conn.execute(
                            'INSERT INTO user_activities (user_id, activity_type, description, created_at) VALUES (?, ?, ?, ?)',
                            (user['id'], 'login', 'User logged in successfully', datetime.now())
                        )
                        conn.commit()
                        conn.close()
                        print(f"[DEBUG] Logged login activity for user {user['username']}.")
                    except Exception as e:
                        print(f"[ERROR] Failed to log login activity for user {user['username']}: {e}")
                    flash(f'Welcome back, {user["username"]}!', 'success')
                    print(f"[DEBUG] Session right before redirect after login: {dict(session)}")
                    # Redirect based on role
                    if session['role'] == 'admin':
                        print(f"[DEBUG] Redirecting admin user {user['username']} to admin dashboard.")
                        return redirect(url_for('main.dashboard'))  # Admin dashboard
                    else:
                        print(f"[DEBUG] Redirecting normal user {user['username']} to user dashboard.")
                        return redirect(url_for('main.user_dashboard'))  # Normal user to user dashboard
                else:
                    print(f"[DEBUG] Password hash does not match for user {username}.")
                    flash('Invalid username or password.', 'error')
                    try:
                        return render_template('auth/auth.html', title='Login')
                    except Exception as e:
                        print(f"[ERROR] Template rendering failed for auth/auth.html: {e}")
                        flash('Error rendering login page. Please try again.', 'error')
                        return redirect(url_for('auth.login'))
            else:
                print(f"[DEBUG] No password field found for user {username} under expected names (password, password_hash, hashed_password).")
                flash('Invalid username or password.', 'error')
                try:
                    return render_template('auth/auth.html', title='Login')
                except Exception as e:
                    print(f"[ERROR] Template rendering failed for auth/auth.html: {e}")
                    flash('Error rendering login page. Please try again.', 'error')
                    return redirect(url_for('auth.login'))
        else:
            print(f"[DEBUG] Username {username} not found in database.")
            flash('Invalid username or password.', 'error')
            try:
                return render_template('auth/auth.html', title='Login')
            except Exception as e:
                print(f"[ERROR] Template rendering failed for auth/auth.html: {e}")
                flash('Error rendering login page. Please try again.', 'error')
                return redirect(url_for('auth.login'))
    # GET request: render login template
    try:
        return render_template('auth/auth.html', title='Login')
    except Exception as e:
        print(f"[ERROR] Template rendering failed for auth/auth.html: {e}")
        flash('Error rendering login page. Please try again.', 'error')
        return redirect(url_for('auth.login'))

@auth.route('/logout')
def logout():
    """User logout with secure session termination"""
    anomaly_types_path = session.get('anomaly_types_path')
    if anomaly_types_path and os.path.exists(anomaly_types_path):
        os.remove(anomaly_types_path)
    session.pop('anomaly_types_path', None)
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('auth.auth_page'))

@auth.route('/auth')
def auth_page():
    """Combined authentication page"""
    # If user is already logged in, redirect to main page
    if 'user_id' in session:
        return redirect(url_for('dashboard.index'))
    
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
            return redirect(url_for('dashboard.index'))
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
        
        # Enhanced password validation
        if len(new_password) < 12:
            flash('New password must be at least 12 characters long!', 'error')
            return render_template('auth/change_password.html')
        if not re.search(r'[A-Z]', new_password):
            flash('New password must contain at least one uppercase letter!', 'error')
            return render_template('auth/change_password.html')
        if not re.search(r'[a-z]', new_password):
            flash('New password must contain at least one lowercase letter!', 'error')
            return render_template('auth/change_password.html')
        if not re.search(r'\d', new_password):
            flash('New password must contain at least one number!', 'error')
            return render_template('auth/change_password.html')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', new_password):
            flash('New password must contain at least one special character!', 'error')
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

class ForgotPasswordForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    submit = SubmitField('Next')

class ConfirmEmailForm(FlaskForm):
    username = HiddenField('Username', validators=[DataRequired()])
    confirm = SubmitField('Yes, this is my email')
    deny = SubmitField('No, not my email')

class ResetPasswordForm(FlaskForm):
    username = HiddenField('Username', validators=[DataRequired()])
    password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=12, message='Password must be at least 12 characters long.'),
        Regexp(r'.*[A-Z].*', message='Must contain an uppercase letter.'),
        Regexp(r'.*[a-z].*', message='Must contain a lowercase letter.'),
        Regexp(r'.*\d.*', message='Must contain a number.'),
        Regexp(r'.*[!@#$%^&*(),.?":{}|<>].*', message='Must contain a special character.')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match.')
    ])
    submit = SubmitField('Reset Password')

@auth.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        username = form.username.data.strip()
        session['reset_username'] = username  # Store in session
        return redirect(url_for('auth.forgot_password_confirm'))  # No query param
    return render_template('auth/forgot_password.html', form=form)

@auth.route('/forgot-password/confirm', methods=['GET', 'POST'])
def forgot_password_confirm():
    username = session.get('reset_username')
    if not username:
        flash('Invalid reset request.', 'error')
        return redirect(url_for('auth.forgot_password'))
    form = ConfirmEmailForm(username=username)
    email_masked = None
    user = None
    if username:
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        if user:
            email = user['email']
            # Mask email: show first character, then '***', then everything after '@'
            parts = email.split('@', 1)
            if len(parts) == 2 and len(parts[0]) > 0:
                masked = parts[0][0] + '***'
                email_masked = masked + '@' + parts[1]
            else:
                email_masked = '***@***'
    if request.method == 'POST':
        if 'confirm' in request.form:
            return redirect(url_for('auth.forgot_password_reset'))  # No param
        elif 'deny' in request.form:
            session.pop('reset_username', None)
            flash('Please contact support or try again.', 'error')
            return redirect(url_for('auth.login'))
    return render_template('auth/forgot_password_confirm.html', form=form, email_masked=email_masked)

@auth.route('/forgot-password/reset', methods=['GET', 'POST'])
def forgot_password_reset():
    username = session.get('reset_username')
    if not username:
        flash('Invalid reset request.', 'error')
        return redirect(url_for('auth.forgot_password'))
    form = ResetPasswordForm(username=username)
    if form.validate_on_submit():
        password = form.password.data
        if not password:
            flash('Password is required.', 'error')
            return render_template('auth/forgot_password_reset.html', form=form)
        # Update password if user exists
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        if user:
            password_hash = generate_password_hash(password)
            conn.execute('UPDATE users SET password_hash = ? WHERE username = ?', (password_hash, username))
            conn.commit()
            conn.close()
            session.pop('reset_username', None)  # Clear session
            flash('Password reset successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))
        conn.close()
        # If user not found, show generic message
        flash('Password reset successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/forgot_password_reset.html', form=form)

# Initialize database when module is imported
init_db() 