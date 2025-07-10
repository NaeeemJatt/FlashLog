from flask import Flask
from app import create_app
import os

template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates'))

app = create_app()
app.template_folder = template_dir

if __name__ == '__main__':
    # Disable debug mode in production
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)
