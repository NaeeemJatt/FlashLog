from flask import Flask, render_template, request, redirect
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import secrets
import os
from datetime import timedelta

def create_app():
    app = Flask(__name__)
    app.config['UPLOAD_FOLDER'] = 'uploads'
    
    # Force session cookie settings for local development
    app.config['SESSION_COOKIE_SECURE'] = False  # Always False for local dev
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    
    # Set the template folder explicitly to ensure correct path
    app.template_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
    
    # Generate secure secret key directly (no reliance on environment)
    app.secret_key = 'NaeemJatt027@@'  # Set static secret key for session management
    
    # Determine environment (hardcoded to development if needed)
    env = 'development'
    is_production = env == 'production'
    
    # Configure session settings
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)  # 1 hour
    app.config['SESSION_COOKIE_SECURE'] = is_production  # Secure in production
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Strict' if is_production else 'Lax'  # Stricter in production
    app.config['SESSION_REFRESH_EACH_REQUEST'] = True
    
    # Initialize CSRF protection
    csrf = CSRFProtect(app)
    
    # Initialize rate limiting with Redis-like storage (or use memory for development)
    try:
        from flask_limiter.util import get_remote_address
        from flask_limiter import Limiter
        limiter = Limiter(
            app=app,
            key_func=get_remote_address,
            default_limits=["200 per day", "50 per hour"],
            storage_uri="memory://"  # Use memory storage for development
        )
    except ImportError:
        # Fallback if flask-limiter is not available
        limiter = None
    
    # Add security headers
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' cdn.tailwindcss.com; style-src 'self' cdn.tailwindcss.com; img-src 'self' data:; font-src 'self' cdn.tailwindcss.com;"
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        return response
    
    # Global error handler
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403

    # Register blueprints
    from .routes import main
    from .auth import auth
    from .admin import admin
    from .dashboard import dashboard_bp
    from .download import download_bp
    from .history import history_bp
    from .kibana import kibana_bp
    from .upload import upload_bp
    
    app.register_blueprint(main)
    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(admin, url_prefix='/admin')
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(download_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(kibana_bp)
    app.register_blueprint(upload_bp)

    @app.before_request
    def enforce_https():
        if is_production and not request.is_secure:
            url = request.url.replace('http://', 'https://', 1)
            return redirect(url, code=301)

    return app
