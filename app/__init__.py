from flask import Flask, render_template, session
from app.config import Config
from app.models import db, User


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)

    # Register Blueprints
    from app.routes.public import public_bp
    from app.routes.booking import booking_bp
    from app.routes.gate import gate_bp
    from app.routes.admin import admin_bp
    from app.routes.auth import auth_bp
    from app.routes.api import api_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(booking_bp)
    app.register_blueprint(gate_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)

    # Context processors for templates
    @app.context_processor
    def inject_user():
        user = None
        if 'user_id' in session:
            user = User.query.get(session['user_id'])
        return {
            'current_user': user,
            'is_logged_in': 'user_id' in session,
            'is_admin': session.get('user_role') == 'admin',
            'is_attendant': session.get('user_role') in ('admin', 'attendant')
        }

    # Custom Error Handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('public/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('public/500.html'), 500

    # Auto-create tables if they don't exist
    with app.app_context():
        db.create_all()

    return app
