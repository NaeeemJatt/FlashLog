import os
import sys

# Explicitly disable python-dotenv to prevent parsing attempts
os.environ['DOTENV_DISABLE'] = 'true'

from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
