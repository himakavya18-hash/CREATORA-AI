# Routes package
from flask import Blueprint

def register_blueprints(app):
    from routes.auth_routes import auth_bp
    from routes.creator_routes import creator_bp
    from routes.brand_routes import brand_bp
    from routes.brief_routes import brief_bp
    from routes.matching_routes import matching_bp
    from routes.application_routes import app_bp
    from routes.project_routes import project_bp
    from routes.messaging_routes import messaging_bp
    from routes.notification_routes import notif_bp
    from routes.admin_routes import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(creator_bp)
    app.register_blueprint(brand_bp)
    app.register_blueprint(brief_bp)
    app.register_blueprint(matching_bp)
    app.register_blueprint(app_bp)
    app.register_blueprint(project_bp)
    app.register_blueprint(messaging_bp)
    app.register_blueprint(notif_bp)
    app.register_blueprint(admin_bp)
