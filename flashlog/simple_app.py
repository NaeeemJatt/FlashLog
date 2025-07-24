#!/usr/bin/env python3
"""
Simple Flask App for AI Log Summarization
This app focuses on the AI summarization feature without complex dependencies.
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import os
from transformers import pipeline
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this in production

# Simple user management (for demo purposes)
USERS = {
    'admin': {'password': 'admin123', 'role': 'admin'},
    'user': {'password': 'user123', 'role': 'user'}
}

def login_required(f):
    """Simple login decorator"""
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first.', 'error')
            return redirect('/login')
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/')
def index():
    """Main page"""
    if 'user_id' in session:
        return redirect('/dashboard')
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Simple login"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username in USERS and USERS[username]['password'] == password:
            session['user_id'] = username
            session['username'] = username
            session['role'] = USERS[username]['role']
            flash('Login successful!', 'success')
            return redirect('/dashboard')
        else:
            flash('Invalid username or password!', 'error')
    
    return render_template('simple_login.html')

@app.route('/logout')
def logout():
    """Logout"""
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect('/login')

# Update all dashboard references to use standardized routes/templates
@app.route('/user/dashboard')
def user_dashboard():
    return render_template('user_dashboard.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    return render_template('admin/dashboard.html')

@app.route('/summarize', methods=['GET', 'POST'])
@login_required
def summarize():
    """AI Summarization endpoint"""
    try:
        # Get log data
        if request.method == 'POST':
            log_data = request.form.get('logs', '')
        else:
            log_data = request.args.get('logs', '')
        
        if not log_data:
            return jsonify({'error': 'No log data provided'}), 400
        
        # Check if model exists
        model_path = 'models/t5-small'
        if not os.path.exists(model_path):
            return jsonify({'error': 'AI model not found. Please download the model first.'}), 500
        
        # Load model and generate summary
        summarizer = pipeline('summarization', model=model_path)
        
        # Truncate if too long
        if len(log_data) > 5000:
            log_data = log_data[:5000] + "..."
        
        # Generate summary
        result = summarizer(log_data, max_length=150, min_length=50, do_sample=False)
        summary = result[0]['summary_text']
        
        return jsonify({
            'summary': summary,
            'original_length': len(log_data),
            'summary_length': len(summary),
            'model': 't5-small',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': f'Summarization failed: {str(e)}'}), 500

@app.route('/summarize-ui')
@login_required
def summarize_ui():
    """AI Summarization UI"""
    return render_template('simple_summarize.html')

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000) 