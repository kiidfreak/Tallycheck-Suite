import pytest
from unittest.mock import patch
from models import db, Employee, Role, Department

# Helper fixture to mock the JWT verification so we don't hit the real Auth0
@pytest.fixture
def mock_verify_jwt():
    with patch('helpers.auth_helper.verify_jwt') as mock_jwt:
        yield mock_jwt

# Helper to create fake authorization headers
def get_auth_headers():
    return {'Authorization': 'Bearer fake-token'}

# --- EMPLOYEE ENDPOINT TESTS ---

def test_register_employee(client, app, mock_verify_jwt):
    """Test that registering creates an unapproved employee in the DB."""
    # Mock the Auth0 payload for a brand new user
    mock_verify_jwt.return_value = {
        'sub': 'auth0|newuser',
        'email': 'newuser@adept.com'
    }
    
    response = client.post('/auth/register', 
                           headers=get_auth_headers(),
                           json={'first_name': 'New', 'last_name': 'User'})
    
    assert response.status_code == 201
    data = response.get_json()
    assert "successfully registered" in data['message']
    
    # Verify the database state
    with app.app_context():
        emp = Employee.query.filter_by(auth0_id='auth0|newuser').first()
        assert emp is not None
        assert emp.is_approved is False
        assert emp.role_id is None

def test_login_unapproved(client, app, mock_verify_jwt):
    """Test that unapproved users are blocked from logging in."""
    # Seed an unapproved user
    with app.app_context():
        emp = Employee(auth0_id='auth0|unapproved', email='unapp@adept.com', first_name='A', last_name='B')
        db.session.add(emp)
        db.session.commit()
        
    mock_verify_jwt.return_value = {'sub': 'auth0|unapproved'}
    
    response = client.post('/auth/login', headers=get_auth_headers())
    assert response.status_code == 403
    assert response.get_json()['error'] == 'insufficient_permissions'

def test_get_me_approved(client, app, mock_verify_jwt):
    """Test getting profile data for a fully approved employee."""
    with app.app_context():
        role = Role.query.filter_by(name='staff').first()
        dept = Department.query.filter_by(name='software_development').first()
        
        emp = Employee(
            auth0_id='auth0|approved', 
            email='app@adept.com', 
            first_name='App', 
            last_name='User',
            role_id=role.id,
            department_id=dept.id,
            is_approved=True
        )
        db.session.add(emp)
        db.session.commit()
        
    mock_verify_jwt.return_value = {'sub': 'auth0|approved'}
    
    response = client.get('/auth/me', headers=get_auth_headers())
    assert response.status_code == 200
    data = response.get_json()['data']
    assert data['role_name'] == 'staff'
    assert data['department_name'] == 'software_development'
    assert data['is_approved'] is True

# --- ADMIN ENDPOINT TESTS ---

def test_admin_metadata(client, app, mock_verify_jwt):
    """Test that admins can fetch metadata."""
    with app.app_context():
        admin_role = Role.query.filter_by(name='super_admin').first()
        
        admin = Employee(auth0_id='auth0|admin', email='admin@adept.com', first_name='Admin', last_name='User', role_id=admin_role.id, is_approved=True)
        db.session.add(admin)
        db.session.commit()

    mock_verify_jwt.return_value = {'sub': 'auth0|admin'}
    
    response = client.get('/auth/metadata', headers=get_auth_headers())
    assert response.status_code == 200
    data = response.get_json()['data']
    assert 'roles' in data
    assert 'departments' in data

def test_admin_guard_blocks_regular_user(client, app, mock_verify_jwt):
    """SECURITY TEST: Ensure a regular employee cannot access admin endpoints."""
    with app.app_context():
        regular_role = Role(name='Employee')
        db.session.add(regular_role)
        db.session.commit()
        
        regular_user = Employee(auth0_id='auth0|regular', email='reg@adept.com', first_name='Reg', last_name='User', role_id=regular_role.id, is_approved=True)
        db.session.add(regular_user)
        db.session.commit()

    mock_verify_jwt.return_value = {'sub': 'auth0|regular'}
    
    # Try to access an admin-only endpoint
    response = client.get('/auth/metadata', headers=get_auth_headers())
    assert response.status_code == 403
    assert response.get_json()['error'] == 'insufficient_permissions'

def test_get_pending_users(client, app, mock_verify_jwt):
    """Test that HR/Admins can retrieve a list of pending users."""
    with app.app_context():
        hr_role = Role.query.filter_by(name='hr').first()
        hr_user = Employee(auth0_id='auth0|hr', email='hr@adept.com', first_name='HR', last_name='User', role_id=hr_role.id, is_approved=True)
        pending_user = Employee(auth0_id='auth0|pending', email='pending@adept.com', first_name='Pen', last_name='Ding', is_approved=False)
        db.session.add_all([hr_user, pending_user])
        db.session.commit()

    mock_verify_jwt.return_value = {'sub': 'auth0|hr'}
    
    response = client.get('/auth/users/pending', headers=get_auth_headers())
    assert response.status_code == 200
    data = response.get_json()['data']
    assert len(data) == 1
    assert data[0]['email'] == 'pending@adept.com'

def test_admin_approve_user(client, app, mock_verify_jwt):
    """Test the full flow of an HR admin approving a pending user and assigning roles."""
    with app.app_context():
        hr_role = Role.query.filter_by(name='hr').first()
        
        hr_user = Employee(auth0_id='auth0|hr', email='hr@adept.com', first_name='HR', last_name='User', role_id=hr_role.id, is_approved=True)
        
        # Unapproved user
        pending_user = Employee(auth0_id='auth0|pending', email='pending@adept.com', first_name='Pen', last_name='Ding')
        
        dev_role = Role.query.filter_by(name='staff').first()
        dept = Department.query.filter_by(name='software_development').first()
        
        db.session.add_all([hr_user, pending_user])
        db.session.commit()
        
        pending_user_id = str(pending_user.id)
        dev_role_id = dev_role.id
        dept_id = dept.id

    # Log in as HR
    mock_verify_jwt.return_value = {'sub': 'auth0|hr'}
    
    payload = {
        'role_id': dev_role_id,
        'department_id': dept_id
    }
    
    response = client.post(f'/auth/users/{pending_user_id}/approve', headers=get_auth_headers(), json=payload)
    assert response.status_code == 200
    
    # Verify the user was successfully updated in the DB
    with app.app_context():
        approved_user = Employee.query.filter_by(auth0_id='auth0|pending').first()
        assert approved_user.is_approved is True
        assert approved_user.role.name == 'staff'
        assert approved_user.department.name == 'software_development'
