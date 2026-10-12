import os
os.environ['DISABLE_SQLALCHEMY_CEXT'] = '1'

import sys
from datetime import datetime
from flask import Flask, render_template
from flask_login import LoginManager, current_user
from flask_wtf.csrf import CSRFProtect

from config import config_by_name
from models import db, User
from routes import register_blueprints

def create_app(config_name=None):
    if not config_name:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config_by_name.get(config_name, config_by_name['development']))

    # Ensure upload directories exist
    upload_dirs = [
        app.config['UPLOAD_FOLDER'],
        os.path.join(app.config['UPLOAD_FOLDER'], 'portfolios'),
        os.path.join(app.config['UPLOAD_FOLDER'], 'avatars'),
        os.path.join(app.config['UPLOAD_FOLDER'], 'deliverables'),
    ]
    for d in upload_dirs:
        os.makedirs(d, exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    csrf = CSRFProtect(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    register_blueprints(app)

    # Context processors
    @app.context_processor
    def inject_global_data():
        unread_count = 0
        if current_user.is_authenticated:
            try:
                unread_count = current_user.unread_notifications_count()
            except Exception:
                unread_count = 0
        return {
            'current_user': current_user,
            'unread_notifications_count': unread_count,
            'current_year': datetime.utcnow().year
        }

    # Custom Error Handlers
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    # CLI Seed Command
    @app.cli.command("seed")
    def seed_cmd():
        """Seeds database with realistic demo accounts and sample campaigns."""
        from seed import seed_database
        seed_database()

    return app

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Auto-seed if database is empty
        if User.query.count() == 0:
            from seed import seed_database
            seed_database()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
