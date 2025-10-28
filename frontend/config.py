"""
Flask Application Configuration
"""
import os
from datetime import timedelta

class Config:
    """Base configuration"""

    # Basic Config
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    PORT = int(os.environ.get('PORT', 5000))
    HOST = os.environ.get('HOST', '0.0.0.0')

    # API Configuration
    API_BASE_URL = os.environ.get('API_URL', 'http://backend:8000')
    API_VERSION = 'v1'
    API_TIMEOUT = 30

    # Party Information
    PARTY_NAME = 'Alliance for Democracy and Development'
    PARTY_ABBREVIATION = 'ADD'
    PARTY_FOUNDED = 'May 14, 2010'
    PARTY_FOUNDER = 'Charles Milupi'
    PARTY_PRESIDENT = 'Charles Milupi'
    PARTY_SLOGAN = 'Democracy and Development for All'
    PARTY_COLORS = ['#0066CC', '#FF6600']  # Blue and Orange
    PARTY_ALLIANCE = 'UPND Alliance Partner'
    PARTY_STATUS = 'Alliance Partner'
    CURRENT_GOVERNMENT = 'UPND Government Partner'

    # Party Contact Information
    PARTY_HEADQUARTERS = 'Lusaka, Zambia'
    PARTY_PHONE = '+260 211 123 456'
    PARTY_EMAIL = 'info@add.org.zm'
    PARTY_WEBSITE = 'www.add.org.zm'
    PARTY_FACEBOOK = 'https://www.facebook.com/profile.php?id=61576153207214'
    MILUPI_FACEBOOK = 'https://www.facebook.com/p/Charles-Lubasi-Milupi-100025627500028/'
    MILUPI_FOLLOWERS = '40,000+'

    # Database (for Flask sessions if needed)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL',
        'postgresql://member_admin:secure_password_123@postgres:5432/party_membership')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Session Configuration
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # File Upload Configuration
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}

    # Pagination
    ITEMS_PER_PAGE = 20

    # Language Configuration
    LANGUAGES = {
        'en': 'English',
        'bem': 'Bemba',
        'nya': 'Nyanja',
        'ton': 'Tonga',
        'loz': 'Lozi',
        'luv': 'Luvale',
        'kao': 'Kaonde',
        'lun': 'Lunda'
    }
    DEFAULT_LANGUAGE = 'en'

    # Cache Configuration
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300

    # Security Headers
    SECURITY_HEADERS = {
        'X-Frame-Options': 'SAMEORIGIN',
        'X-Content-Type-Options': 'nosniff',
        'X-XSS-Protection': '1; mode=block'
    }

    # Rate Limiting
    RATELIMIT_STORAGE_URL = 'redis://localhost:6379'
    RATELIMIT_DEFAULT = '200/hour'

    # Logging
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT', 'False').lower() == 'true'
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    WTF_CSRF_ENABLED = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    WTF_CSRF_ENABLED = True
    SESSION_COOKIE_SECURE = True

    # Override with production values
    SECRET_KEY = os.environ.get('SECRET_KEY', 'production-secret-key-change-this')

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}