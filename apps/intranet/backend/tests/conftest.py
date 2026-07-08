import pytest
from __init__ import create_app
from models import db
from auth_routes import seed_roles_and_departments

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
        seed_roles_and_departments()
        
        yield flask_app
        
        # Clean up after tests are done
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()
