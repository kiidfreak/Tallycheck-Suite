import os
import sys
from typing import Any, Optional, Tuple

# Ensure the current directory is in sys.path for absolute imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

workspace_libs: str = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../libs'))
if workspace_libs not in sys.path:
    sys.path.insert(0, workspace_libs)

from flask import Flask, Response
from flask_migrate import Migrate
from flask_cors import CORS
from dotenv import load_dotenv

from py_config import get_config
from models import db
from py_errors import AppError, InternalError

env_path: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
load_dotenv(dotenv_path=env_path)

migrate: Migrate = Migrate()
cors: CORS = CORS()

def create_app(test_config: Optional[dict[str, Any]] = None) -> Flask:
    app: Flask = Flask(__name__)
    app.config.from_object(get_config())
    
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'

    if test_config is not None:
        app.config.update(test_config)

    # ==========================================================
    # EXTENSIONS
    # ==========================================================
    db.init_app(app)
    migrate.init_app(app, db)

    frontend_url: str = os.environ.get('FRONTEND_URL', 'http://localhost:4200')
    origins: list[str] = [frontend_url]
    if "localhost" in frontend_url:
        origins.append(frontend_url.replace("localhost", "127.0.0.1"))
    elif "127.0.0.1" in frontend_url:
        origins.append(frontend_url.replace("127.0.0.1", "localhost"))

    cors.init_app(app, resources={
        r"/*": {
            "origins": origins,
            "allow_headers": ["Authorization", "Content-Type"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        }
    })

    # ==========================================================
    # BLUEPRINTS
    # ==========================================================
    # Create Blueprint for v2 of the app
    from flask import Blueprint
    prefix = '' if app.config.get("TESTING") else '/api/v2'
    api_v2: Blueprint = Blueprint('api_v2', __name__, url_prefix=prefix)

    # Register child Blueprints with the parent Blueprint
    from auth_routes import auth_bp, seed_roles_and_departments
    api_v2.register_blueprint(auth_bp)

    from attendance_routes import attendance_bp
    api_v2.register_blueprint(attendance_bp)

    from department_routes import department_bp
    api_v2.register_blueprint(department_bp)

    from employee_routes import employee_bp
    api_v2.register_blueprint(employee_bp)

    from report_routes import report_bp
    api_v2.register_blueprint(report_bp)

    from beacon_routes import beacon_bp
    api_v2.register_blueprint(beacon_bp)

    from safechild_routes import safechild_bp
    api_v2.register_blueprint(safechild_bp)

    app.register_blueprint(api_v2)

    # Register tenant resolution middleware
    from utils.tenant_middleware import set_tenant_schema
    app.before_request(set_tenant_schema)

    @app.cli.command("seed-db")
    def seed_db() -> None:
        """Seed roles and departments."""
        seed_roles_and_departments()
        print("Database seeded!")

    # ==========================================================
    # ERROR HANDLERS
    # ==========================================================
    @app.errorhandler(AppError)
    def handle_app_error(e: AppError) -> Tuple[Response, int]:
        return e.write_response(debug=app.debug)

    from werkzeug.exceptions import HTTPException
    @app.errorhandler(Exception)
    def handle_unexpected_error(e: Exception) -> Any:
        if isinstance(e, HTTPException):
            return e.get_response()
        err: InternalError = InternalError(details=str(e))
        return err.write_response(debug=app.debug)

    # ==========================================================
    # HEALTH
    # ==========================================================
    @app.route('/')
    def hello() -> str:
        return "Omni Intranet API is running!"

    @app.route('/health')
    def health_check() -> Tuple[dict[str, str], int]:
        try:
            db.session.execute(db.text('SELECT 1'))
            return {"status": "ok", "db": "connected"}, 200
        except Exception as e:
            return {"status": "error", "db": str(e)}, 500

    return app