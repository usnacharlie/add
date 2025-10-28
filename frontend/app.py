"""
Flask frontend application
"""
from flask import Flask, render_template
from frontend.routes import register_routes
import os

def create_app():
    """Application factory"""
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['API_BASE_URL'] = os.getenv('API_BASE_URL', 'http://localhost:9500/api/v1')
    
    # Register routes
    register_routes(app)
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return render_template('errors/500.html'), 500
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=9100, debug=True)
