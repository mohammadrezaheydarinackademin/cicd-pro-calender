import hmac
import secrets

from flask import Flask, abort, g, jsonify, request, session
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def _configure_database_engine(app: Flask) -> None:
    uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    options = {}

    if uri.startswith("sqlite"):
        options["connect_args"] = {"check_same_thread": False}
        if ":memory:" in uri or uri in {"sqlite://", "sqlite:///:memory:"}:
            from sqlalchemy.pool import StaticPool

            options["poolclass"] = StaticPool
    else:
        options["pool_pre_ping"] = True
        options["pool_recycle"] = 280
        options["connect_args"] = {"connect_timeout": 5}

    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = options


def create_app(config_object=None) -> Flask:
    app = Flask(__name__)

    if config_object is None:
        from config import Config

        app.config.from_object(Config)
    else:
        app.config.from_object(config_object)

    _configure_database_engine(app)
    db.init_app(app)

    from .auth import auth_bp
    from .routes import api_bp, main_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)

    from .models import User

    @app.before_request
    def load_user_and_protect_csrf():
        if request.endpoint in {"static", "main.health"}:
            return

        if "csrf_token" not in session:
            session["csrf_token"] = secrets.token_urlsafe(32)

        g.user = None
        user_id = session.get("user_id")
        if user_id is not None:
            user = db.session.get(User, user_id)
            if user is None:
                session.clear()
                session["csrf_token"] = secrets.token_urlsafe(32)
            else:
                g.user = user

        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            supplied = request.headers.get("X-CSRF-Token")
            if not supplied:
                supplied = request.form.get("csrf_token")
            expected = session.get("csrf_token")
            if not supplied or not expected or not hmac.compare_digest(supplied, expected):
                if request.path.startswith("/api/"):
                    return jsonify({"error": "Invalid or missing CSRF token."}), 400
                abort(400, description="Invalid or missing CSRF token.")

    @app.context_processor
    def inject_template_globals():
        return {
            "current_user": getattr(g, "user", None),
            "csrf_token": session.get("csrf_token"),
        }

    @app.errorhandler(400)
    def bad_request(error):
        if request.path.startswith("/api/"):
            return jsonify({"error": getattr(error, "description", "Bad request.")}), 400
        return error

    @app.errorhandler(403)
    def forbidden(error):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Forbidden."}), 403
        return error

    @app.errorhandler(404)
    def not_found(error):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Not found."}), 404
        return error

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        if request.path.startswith("/api/"):
            return jsonify({"error": "Internal server error."}), 500
        return error

    return app
