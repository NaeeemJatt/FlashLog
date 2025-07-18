from flask import Flask
from app import create_app
import os

template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates'))

app = create_app()
app.template_folder = template_dir

if __name__ == '__main__':
    # Debug mode should only be enabled in development
    # Set FLASK_DEBUG=1 in environment for debug mode
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() in ['true', '1']
    app.run(debug=debug_mode, host='127.0.0.1', port=5000)
