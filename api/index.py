import os
import tempfile
from flashlog.app import create_app

# Create app instance
app = create_app()

# Configure for serverless environment
app.config['UPLOAD_FOLDER'] = '/tmp'  # Use temporary directory for Vercel
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs('/tmp', exist_ok=True)

# Handle Vercel's serverless environment
@app.before_request
def before_request():
    """Configure for serverless environment"""
    # Set temporary upload folder for this request
    app.config['UPLOAD_FOLDER'] = '/tmp'

if __name__ == '__main__':
    app.run(debug=True) 