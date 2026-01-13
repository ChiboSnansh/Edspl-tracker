# WSGI configuration for PythonAnywhere
# This file is used by PythonAnywhere to serve the Flask app

import sys
import os

# Add project directory to path
project_home = '/home/YOUR_USERNAME/edspl-tracker'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set environment variable for Flask
os.environ['FLASK_ENV'] = 'production'

# Import Flask app
from app import app as application
