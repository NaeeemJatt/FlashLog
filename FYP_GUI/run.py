from flask import Flask
from app import create_app
import os

template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates'))

app = create_app()
app.template_folder = template_dir

if __name__ == '__main__':
    app.run(debug=True)
