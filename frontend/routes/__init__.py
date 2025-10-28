"""
Flask routes package
"""
from .main import main_bp
from .members import members_bp
from .locations import locations_bp
from .auth import auth_bp
from .reports import reports_bp
from .roles import roles_bp
from .events import events_bp
from .referrals import referrals_bp


def register_routes(app):
    """Register all blueprints with the Flask app"""
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(members_bp, url_prefix='/members')
    app.register_blueprint(locations_bp, url_prefix='/locations')
    app.register_blueprint(reports_bp, url_prefix='/reports')
    app.register_blueprint(roles_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(referrals_bp)
