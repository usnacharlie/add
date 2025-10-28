#!/usr/bin/env python3
"""
Main Flask application entry point for the Political Party Membership System
"""

from app_factory import create_app
import os

# Create the Flask application
app = create_app(config_name=os.environ.get('FLASK_ENV', 'development'))

if __name__ == '__main__':
    # Run the development server
    app.run(
        host='0.0.0.0',
        port=57020,
        debug=app.config['DEBUG']
    )