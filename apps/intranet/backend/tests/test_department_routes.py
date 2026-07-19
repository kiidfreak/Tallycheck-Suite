import pytest
from unittest.mock import patch
from models import db, Employee, Department, Role
import uuid

@pytest.fixture
def mock_verify_jwt():
    with patch('helpers.auth_helper.verify_jwt') as mock_jwt:
        yield mock_jwt

def get_auth_headers():
    return {'Authorization': 'Bearer fake-token'}

@pytest.fixture
def setup_users(app):
    with app.app_context():
        hr_role = Role.query.filter_by(name='hr_admin').first()
        staff_role = Role.query.filter_by(name='staff').first()
        
        hr_user = Employee(auth0_id='auth0|hr', email='hr@example.com', first_name='H', last_name='R', is_approved=True, role_id=hr_role.id)
        staff_user = Employee(auth0_id='auth0|staff', email='staff@example.com', first_name='S', last_name='T', is_approved=True, role_id=staff_role.id)
        db.session.add_all([hr_user, staff_user])
        db.session.commit()

def test_list_departments(client, app, mock_verify_jwt, setup_users):
    mock_verify_jwt.return_value = {'sub': 'auth0|staff'}

    response = client.get('/departments', headers=get_auth_headers())
    assert response.status_code == 200
    data = response.get_json()
    assert len(data['data']) > 0

def test_create_department_hr(client, app, mock_verify_jwt, setup_users):
    mock_verify_jwt.return_value = {'sub': 'auth0|hr'}
    response = client.post('/departments', headers=get_auth_headers(), json={"name": "New Test Dept"})
    assert response.status_code == 201
    
    with app.app_context():
        assert Department.query.filter_by(name="new_test_dept").first() is not None

def test_create_department_staff_forbidden(client, app, mock_verify_jwt, setup_users):
    mock_verify_jwt.return_value = {'sub': 'auth0|staff'}
    response = client.post('/departments', headers=get_auth_headers(), json={"name": "Another Dept"})
    assert response.status_code == 403

def test_update_department(client, app, mock_verify_jwt, setup_users):
    mock_verify_jwt.return_value = {'sub': 'auth0|hr'}
    with app.app_context():
        dept = Department(name="Old Name")
        db.session.add(dept)
        db.session.commit()
        dept_id = dept.id

    response = client.put(f'/departments/{dept_id}', headers=get_auth_headers(), json={"name": "New Name"})
    assert response.status_code == 200
    
    with app.app_context():
        assert Department.query.get(dept_id).name == "new_name"

def test_delete_department(client, app, mock_verify_jwt, setup_users):
    mock_verify_jwt.return_value = {'sub': 'auth0|hr'}
    with app.app_context():
        dept = Department(name="To Delete")
        db.session.add(dept)
        db.session.commit()
        dept_id = dept.id

    response = client.delete(f'/departments/{dept_id}', headers=get_auth_headers())
    assert response.status_code == 204
    
    with app.app_context():
        assert Department.query.get(dept_id) is None

def test_delete_department_with_employees(client, app, mock_verify_jwt, setup_users):
    mock_verify_jwt.return_value = {'sub': 'auth0|hr'}
    with app.app_context():
        dept = Department(name="Has Employees")
        db.session.add(dept)
        db.session.commit()
        
        emp = Employee.query.filter_by(auth0_id='auth0|staff').first()
        emp.department_id = dept.id
        db.session.commit()
        dept_id = dept.id

    response = client.delete(f'/departments/{dept_id}', headers=get_auth_headers())
    assert response.status_code == 409
