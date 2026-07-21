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
    origins: list[str] = [
        r"https?://localhost(:\d+)?",
        r"https?://127\.0\.0\.1(:\d+)?",
        r"https?://.*\.tallycheck\.co\.ke(:\d+)?",
        r"https?://.*\.tallycheck\.co\.ke"
    ]
    if frontend_url and frontend_url not in origins:
        origins.append(frontend_url)

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
    from auth_routes import auth_bp, seed_roles
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

    from zone_routes import zone_bp
    api_v2.register_blueprint(zone_bp)

    from safechild_routes import safechild_bp
    api_v2.register_blueprint(safechild_bp)

    from settings_routes import settings_bp
    api_v2.register_blueprint(settings_bp)

    from platform_routes import platform_bp
    api_v2.register_blueprint(platform_bp)

    app.register_blueprint(api_v2)

    # Register tenant resolution middleware
    from utils.tenant_middleware import set_tenant_schema
    app.before_request(set_tenant_schema)

    @app.teardown_request
    def _reset_search_path(exc: Optional[BaseException] = None) -> None:
        """Defense-in-depth against a leaked search_path.

        `tenant_scope` already restores the path in its own finally, but a bug
        or an exception path that bypasses it must never let a pooled connection
        carry one tenant's schema into the next request. Reset unconditionally at
        request teardown; swallow errors so teardown itself cannot fail.
        """
        try:
            db.session.execute(db.text("SET search_path TO public"))
        except Exception:
            pass

    @app.cli.command("seed-db")
    def seed_db() -> None:
        """Seed the canonical roles into the active tenant schema."""
        seed_roles()
        print("Roles seeded!")

    @app.cli.command("stamp-tenants")
    def stamp_tenants() -> None:
        """Baseline tenant schemas that predate tenant-aware migrations.

        Schemas built by seed_org.py's db.metadata.create_all() carry no
        alembic_version row, so `flask db upgrade` would try to replay the whole
        history against tables that already exist. This stamps each such schema
        at the revision matching what create_all() produced, giving the upgrade
        somewhere to start from.

        Idempotent: schemas that already have an alembic_version row are left
        alone, so this is safe to re-run.
        """
        from models import db as _db, Organization

        # The revision whose cumulative state equals what create_all() built
        # before tenant-aware migrations existed.
        BASELINE_REVISION = 'b309859846bf'

        with _db.engine.connect() as conn:
            exists = conn.execute(_db.text("SELECT to_regclass('public.organizations')")).scalar()
            if not exists:
                print("No organizations table - nothing to stamp.")
                return

            rows = conn.execute(_db.text(
                "SELECT schema_name FROM public.organizations ORDER BY schema_name"
            )).fetchall()

            present = set(conn.execute(_db.text("SELECT nspname FROM pg_namespace")).scalars().all())

            stamped, skipped, missing = 0, 0, 0
            for (schema,) in rows:
                if schema not in present:
                    print(f"  missing  {schema} (registered but not provisioned)")
                    missing += 1
                    continue

                has_version = conn.execute(_db.text(
                    "SELECT to_regclass(:t)"
                ), {"t": f"{schema}.alembic_version"}).scalar()

                if has_version:
                    current = conn.execute(_db.text(
                        f'SELECT version_num FROM "{schema}".alembic_version'
                    )).scalar()
                    print(f"  skip     {schema} (already at {current})")
                    skipped += 1
                    continue

                conn.execute(_db.text(
                    f'CREATE TABLE "{schema}".alembic_version ('
                    f'version_num VARCHAR(32) NOT NULL, '
                    f'CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num))'
                ))
                conn.execute(_db.text(
                    f'INSERT INTO "{schema}".alembic_version (version_num) VALUES (:rev)'
                ), {"rev": BASELINE_REVISION})
                print(f"  stamped  {schema} -> {BASELINE_REVISION}")
                stamped += 1

            conn.commit()

        print(f"\n{stamped} stamped, {skipped} already versioned, {missing} missing.")
        print("Now run: flask db upgrade")

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