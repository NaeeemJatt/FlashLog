"""
Admin module for FlashLog application
Provides administrative functionality including learning management
"""

from .learning_routes import admin_learning_bp

def register_admin_blueprints(app):
    """Register all admin blueprints with the Flask app"""
    app.register_blueprint(admin_learning_bp)
    print("✅ Admin blueprints registered")