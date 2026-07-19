import pytest
from unittest.mock import patch
from models import db, Employee, Department, Role

@pytest.fixture
def mock_verify_jwt():
    with patch('helpers.auth_helper.verify_jwt') as mock_jwt:
        yield mock_jwt

def get_auth_headers():
    return {'Authorization': 'Bearer fake-token'}

@pytest.fixture
def setup_data(app):
    with app.app_context():
        hr_role = Role.query.filter_by(name='hr_admin').first()
        staff_role = Role.query.filter_by(name='staff').first()
        dept_eng = Department.query.filter_by(name='software_development').first()
        
        hr_user = Employee(auth0_id='auth0|hr', email='hr@example.com', first_name='H', last_name='R', is_approved=True, role_id=hr_role.id)
        staff_user = Employee(auth0_id='auth0|staff', email='staff@example.com', first_name='S', last_name='T', is_approved=True, role_id=staff_role.id, department_id=dept_eng.id)
        unapproved_user = Employee(auth0_id='auth0|pend', email='pend@example.com', first_name='P', last_name='E', is_approved=False)
        db.session.add_all([hr_user, staff_user, unapproved_user])
        db.session.commit()

def test_list_employees_default_approved(client, mock_verify_jwt, setup_data):
    mock_verify_jwt.return_value = {'sub': 'auth0|hr'}
    response = client.get('/employees', headers=get_auth_headers())
    assert response.status_code == 200
    data = response.get_json()['data']['data']
    assert len(data) == 2  # Only hr and staff (approved), not pend
    assert data[0]['is_approved'] is True

def test_list_employees_filter_unapproved(client, mock_verify_jwt, setup_data):
    mock_verify_jwt.return_value = {'sub': 'auth0|hr'}
    response = client.get('/employees?is_approved=false', headers=get_auth_headers())
    assert response.status_code == 200
    data = response.get_json()['data']['data']
    assert len(data) == 1
    assert data[0]['email'] == 'pend@example.com'

def test_list_employees_search(client, mock_verify_jwt, setup_data):
    mock_verify_jwt.return_value = {'sub': 'auth0|hr'}
    # S T -> ST -> st
    response = client.get('/employees?search=st', headers=get_auth_headers())
    data = response.get_json()['data']['data']
    assert len(data) == 1
    assert data[0]['email'] == 'staff@example.com'

def test_create_employee(client, app, mock_verify_jwt, setup_data):
    mock_verify_jwt.return_value = {'sub': 'auth0|hr'}
    
    with app.app_context():
        eng_id = Department.query.filter_by(name='software_development').first().id
        staff_role_id = Role.query.filter_by(name='staff').first().id

    payload = {
        "email": "new@example.com",
        "first_name": "New",
        "last_name": "Employee",
        "department_id": eng_id,
        "role_id": staff_role_id,
        "is_approved": True
    }
    
    response = client.post('/employees', headers=get_auth_headers(), json=payload)
    assert response.status_code == 201
    
    with app.app_context():
        emp = Employee.query.filter_by(email="new@example.com").first()
        assert emp is not None
        assert emp.is_approved is True  # Auto-approved
        assert emp.department_id == eng_id

def test_update_employee(client, app, mock_verify_jwt, setup_data):
    mock_verify_jwt.return_value = {'sub': 'auth0|hr'}
    
    with app.app_context():
        staff = Employee.query.filter_by(email='staff@example.com').first()
        staff_id = staff.id
        sales_dept = Department.query.filter_by(name='sales').first().id

    response = client.put(f'/employees/{staff_id}', headers=get_auth_headers(), json={"department_id": sales_dept, "first_name": "Changed"})
    assert response.status_code == 200
    
    with app.app_context():
        updated = Employee.query.get(staff_id)
        assert updated.first_name == "Changed"
        assert updated.department_id == sales_dept

def test_deactivate_employee(client, app, mock_verify_jwt, setup_data):
    mock_verify_jwt.return_value = {'sub': 'auth0|hr'}
    
    with app.app_context():
        staff = Employee.query.filter_by(email='staff@example.com').first()
        staff_id = staff.id

    response = client.post(f'/employees/{staff_id}/deactivate', headers=get_auth_headers())
    assert response.status_code == 200
    
    with app.app_context():
        updated = Employee.query.get(staff_id)
        assert updated.is_active is False

def test_hr_cannot_create_super_admin(client, app, mock_verify_jwt, setup_data):
    mock_verify_jwt.return_value = {'sub': 'auth0|hr'}
    
    with app.app_context():
        super_admin_role = Role.query.filter_by(name='super_admin').first()
        super_admin_role_id = super_admin_role.id

    payload = {
        "email": "hacker@example.com",
        "first_name": "Hacker",
        "last_name": "Man",
        "role_id": super_admin_role_id
    }
    
    response = client.post('/employees', headers=get_auth_headers(), json=payload)
    assert response.status_code == 403
    assert "Only a super admin can create another super admin" in response.get_json()['message']

def test_hr_cannot_assign_super_admin(client, app, mock_verify_jwt, setup_data):
    mock_verify_jwt.return_value = {'sub': 'auth0|hr'}
    
    with app.app_context():
        staff = Employee.query.filter_by(email='staff@example.com').first()
        staff_id = staff.id
        super_admin_role = Role.query.filter_by(name='super_admin').first()
        super_admin_role_id = super_admin_role.id

    response = client.put(f'/employees/{staff_id}', headers=get_auth_headers(), json={"role_id": super_admin_role_id})
    assert response.status_code == 403
    assert "Only a super admin can assign the super admin role" in response.get_json()['message']
