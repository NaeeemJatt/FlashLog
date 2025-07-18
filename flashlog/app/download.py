from flask import Blueprint, send_file, session, redirect, url_for, flash, request
import os

download_bp = Blueprint('download', __name__)

@download_bp.route('/download/<filename>')
def download_csv(filename):
    """Download the specified CSV file if it exists and user is authenticated"""
    if 'user_id' not in session:
        flash('Please log in to download files.', 'error')
        return redirect(url_for('auth.auth_page'))
    uploads_dir = 'uploads'
    file_path = os.path.join(uploads_dir, filename)
    if not os.path.exists(file_path):
        flash('File not found.', 'error')
        return redirect(url_for('dashboard.index'))
    return send_file(file_path, as_attachment=True)

@download_bp.route('/download-status/<filename>')
def download_status(filename):
    """Check if a file exists for download (AJAX endpoint)"""
    uploads_dir = 'uploads'
    file_path = os.path.join(uploads_dir, filename)
    exists = os.path.exists(file_path)
    return {'exists': exists} 