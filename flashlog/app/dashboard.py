from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from .helpers import compute_dashboard_metrics

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
def index():
    # Authentication is now handled in before_request (should be moved to a decorator or middleware)
    if session.get('role') == 'admin':
        return redirect(url_for('admin.dashboard'))
    dashboard_metrics = compute_dashboard_metrics()
    if request.method == 'POST':
        flash('POST requests are not handled in this refactored dashboard yet.', 'info')
        return redirect(url_for('dashboard.index'))
    return render_template('index.html', metrics=dashboard_metrics) 