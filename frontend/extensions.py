"""
Flask Extensions Initialization
"""
from flask_login import LoginManager
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect
from flask_session import Session
import requests
from functools import wraps
from flask import current_app, session, redirect, url_for, flash

# Initialize extensions
login_manager = LoginManager()
csrf = CSRFProtect()
cors = CORS()
sess = Session()

def init_extensions(app):
    """Initialize Flask extensions"""

    # CORS
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})

    # CSRF Protection - only if enabled in config
    if app.config.get('WTF_CSRF_ENABLED', True):
        csrf.init_app(app)
    else:
        # Provide a dummy csrf_token function when CSRF is disabled
        @app.context_processor
        def csrf_token_processor():
            return {'csrf_token': lambda: ''}

    # Session
    sess.init_app(app)

    # Login Manager
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please login to access this page.'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        """Load user from session"""
        from models import User
        if 'user_data' in session:
            return User(session['user_data'])
        return None

# Custom decorators
def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            flash('You need administrator privileges to access this page.', 'danger')
            return redirect(url_for('member.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def api_required(f):
    """Decorator to check API availability"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Check if API is accessible
            response = requests.get(
                f"{current_app.config['API_BASE_URL']}/health",
                timeout=5
            )
            if response.status_code != 200:
                flash('System is currently unavailable. Please try again later.', 'warning')
                return redirect(url_for('public.index'))
        except:
            flash('Cannot connect to server. Please check your connection.', 'danger')
            return redirect(url_for('public.index'))
        return f(*args, **kwargs)
    return decorated_function

def language_required(f):
    """Decorator to ensure language is set"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'language' not in session:
            session['language'] = current_app.config.get('DEFAULT_LANGUAGE', 'en')
        return f(*args, **kwargs)
    return decorated_function

class APIClient:
    """API Client for backend communication"""

    def __init__(self):
        self.base_url = None
        self.headers = {}

    def init_app(self, app):
        """Initialize API client with app"""
        self.base_url = f"{app.config['API_BASE_URL']}/api/{app.config['API_VERSION']}"
        self.timeout = app.config.get('API_TIMEOUT', 30)

    def set_auth_token(self, token):
        """Set authentication token"""
        self.headers['Authorization'] = f'Bearer {token}'

    def get(self, endpoint, params=None):
        """GET request to API"""
        try:
            response = requests.get(
                f"{self.base_url}/{endpoint}",
                params=params,
                headers=self.headers,
                timeout=self.timeout
            )
            return response
        except Exception as e:
            current_app.logger.error(f"API GET error: {str(e)}")
            return None

    def post(self, endpoint, data=None, json=None):
        """POST request to API"""
        try:
            response = requests.post(
                f"{self.base_url}/{endpoint}",
                data=data,
                json=json,
                headers=self.headers,
                timeout=self.timeout
            )
            return response
        except Exception as e:
            current_app.logger.error(f"API POST error: {str(e)}")
            return None

    def put(self, endpoint, data=None, json=None):
        """PUT request to API"""
        try:
            response = requests.put(
                f"{self.base_url}/{endpoint}",
                data=data,
                json=json,
                headers=self.headers,
                timeout=self.timeout
            )
            return response
        except Exception as e:
            current_app.logger.error(f"API PUT error: {str(e)}")
            return None

    def delete(self, endpoint):
        """DELETE request to API"""
        try:
            response = requests.delete(
                f"{self.base_url}/{endpoint}",
                headers=self.headers,
                timeout=self.timeout
            )
            return response
        except Exception as e:
            current_app.logger.error(f"API DELETE error: {str(e)}")
            return None

# Initialize API client
api_client = APIClient()