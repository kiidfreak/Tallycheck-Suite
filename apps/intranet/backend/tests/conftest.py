import pytest
from __init__ import create_app
from models import db, Department
from auth_routes import seed_roles

# Departments are tenant-specific in production (a university has schools, a
# company has business units), so nothing seeds a default set. Tests declare the
# departments they rely on here rather than depending on production seed data.
TEST_DEPARTMENTS: tuple[str, ...] = ('sales', 'marketing', 'hr', 'it', 'operations')

@pytest.fixture
def app():
    # Create the app with testing configuration
    flask_app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"
    })
    
    # Push an application context so db operations work
    with flask_app.app_context():
        # Create all tables in the in-memory SQLite database
        db.create_all()
        seed_roles()
        for name in TEST_DEPARTMENTS:
            db.session.add(Department(name=name))
        db.session.commit()

        yield flask_app
        
        # Clean up after tests are done
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()
