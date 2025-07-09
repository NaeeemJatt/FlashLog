from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from datetime import datetime, timedelta
import uuid

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
        
        # Validation
        if not username or not email or not password:
            flash('All fields are required!', 'error')
            return render_template('auth/register.html')
        
        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return render_template('auth/register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long!', 'error')
            return render_template('auth/register.html')
        
        # Check if user already exists
        conn = get_db_connection()
        existing_user = conn.execute(
            'SELECT * FROM users WHERE username = ? OR email = ?', 
            (username, email)
        ).fetchone()
        conn.close()
        
        if existing_user:
            flash('Username or email already exists!', 'error')
            return render_template('auth/register.html')
        
        # Create new user
        password_hash = generate_password_hash(password)
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
            (username, email, password_hash)
        )
        conn.commit()
        conn.close()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember') == 'on'
        
        if not username or not password:
            flash('Please enter both username and password!', 'error')
            return render_template('auth/login.html')
        
        # Check user credentials
        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM users WHERE username = ? AND is_active = 1', 
            (username,)
        ).fetchone()
        conn.close()
        
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
            
            flash(f'Welcome back, {user["username"]}!', 'success')
            return redirect(url_for('main.index'))
        else:
            flash('Invalid username or password!', 'error')
    
    return render_template('auth/login.html')

@auth.route('/logout')
def logout():
    """User logout"""
    if 'session_token' in session:
        # Remove session from database
        conn = get_db_connection()
        conn.execute(
            'DELETE FROM user_sessions WHERE session_token = ?',
            (session['session_token'],)
        )
        conn.commit()
        conn.close()
    
    # Clear session
    session.clear()
    flash('You have been logged out successfully!', 'success')
    return redirect(url_for('auth.login'))

def login_required(f):
    """Decorator to require login for routes"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page!', 'error')
            return redirect(url_for('auth.login'))
        
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
                return redirect(url_for('auth.login'))
        
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
    
    return user

@auth.route('/profile')
@login_required
def profile():
    """User profile page"""
    user = get_current_user()
    if not user:
        return redirect(url_for('auth.login'))
    
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
        
        flash('Password changed successfully!', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/change_password.html')

# Initialize database when module is imported
init_db() 