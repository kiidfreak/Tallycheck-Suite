import pytest
import json
from unittest.mock import patch
from datetime import date, timedelta
from models import db, Employee, AttendanceRecord, Department, Role

@pytest.fixture
def mock_verify_jwt():
    with patch('helpers.auth_helper.verify_jwt') as mock_jwt:
        mock_jwt.return_value = {
            'sub': 'auth0|mock-hr',
            'email': 'hr@adept.com'
        }
        yield mock_jwt

@pytest.fixture
def hr_employee(app):
    """Creates a seeded approved HR employee for tests."""
    with app.app_context():
        role = Role.query.filter_by(name='hr_admin').first()
        dept = Department.query.filter_by(name='hr').first()
        
        emp = Employee(
            auth0_id='auth0|mock-hr',
            email='hr@adept.com',
            first_name='Mock',
            last_name='HR',
            role_id=role.id,
            department_id=dept.id,
            is_approved=True
        )
        db.session.add(emp)
        db.session.commit()
    return emp

def get_auth_headers():
    return {'Authorization': 'Bearer fake-token'}

def test_get_dashboard_metrics(client, mock_verify_jwt, hr_employee):
    """Test the dashboard KPIs"""
    # Seed some dummy data for today
    today = date.today()
    eng_dept = Department.query.filter_by(name='software_development').first()
    
    emp1 = Employee(
        auth0_id="test|emp1",
        email="emp1@test.com",
        first_name="Emp",
        last_name="One",
        role_id=1,  # Avoid DetachedInstanceError
        department_id=eng_dept.id,
        is_approved=True
    )
    db.session.add(emp1)
    db.session.commit()

    from datetime import datetime
    record1 = AttendanceRecord(
        employee_id=emp1.id,
        work_date=today,
        clock_in=datetime.now(),
        status='open'
    )
    db.session.add(record1)
    db.session.commit()

    res = client.get('/reports/dashboard', headers=get_auth_headers())
    assert res.status_code == 200
    data = res.get_json()['data']
    
    assert "total_headcount" in data
    assert "present_today" in data
    assert "absent_today" in data
    assert "currently_clocked_in" in data
    assert "attendance_rate_today" in data
    assert data["currently_clocked_in"] == 1


def test_get_attendance_report_json(client, mock_verify_jwt, hr_employee):
    """Test getting attendance report in JSON format"""
    res = client.get('/reports/attendance', headers=get_auth_headers())
    assert res.status_code == 200
    data = res.get_json()
    
    assert "data" in data
    assert "meta" in data
    assert "page" in data["meta"]
    assert "total" in data["meta"]


def test_get_attendance_report_csv(client, mock_verify_jwt, hr_employee):
    """Test getting attendance report in CSV format"""
    # Seed an attendance record so CSV is not empty
    from datetime import datetime
    today = date.today()
    with client.application.app_context():
        emp = Employee.query.filter_by(email='hr@adept.com').first()
        if emp:
            rec = AttendanceRecord(
                employee_id=emp.id,
                work_date=today,
                clock_in=datetime(today.year, today.month, today.day, 8, 0),
                clock_out=datetime(today.year, today.month, today.day, 17, 0),
                status='closed'
            )
            db.session.add(rec)
            db.session.commit()

    res = client.get('/reports/attendance?format=csv', headers=get_auth_headers())
    assert res.status_code == 200
    assert 'text/csv' in res.headers['Content-Type']
    
    # Check that CSV headers are present
    content = res.data.decode('utf-8')
    assert "employee_id" in content
    assert "total_hours_worked" in content


def test_get_department_report(client, mock_verify_jwt, hr_employee):
    """Test department aggregations"""
    res = client.get('/reports/attendance/departments', headers=get_auth_headers())
    assert res.status_code == 200
    data = res.get_json()
    
    assert "data" in data
    assert isinstance(data["data"], list)
    
    if len(data["data"]) > 0:
        dept_data = data["data"][0]
        assert "department_id" in dept_data
        assert "total_employees" in dept_data
        assert "avg_attendance_rate" in dept_data
        assert "employees" in dept_data
        assert isinstance(dept_data["employees"], list)

def test_get_single_department_report(client, mock_verify_jwt, hr_employee):
    """Test single department aggregations"""
    dept = Department.query.first()
    res = client.get(f'/reports/attendance/departments/{dept.id}', headers=get_auth_headers())
    assert res.status_code == 200
    data = res.get_json()
    
    assert "data" in data
    dept_data = data["data"]
    assert dept_data["department_id"] == dept.id
    assert "avg_attendance_rate" in dept_data
    assert "employees" in dept_data

def test_department_report_invalid_dates(client, mock_verify_jwt, hr_employee):
    """Test date parsing error handling"""
    res = client.get('/reports/attendance/departments?date_from=invalid-date', headers=get_auth_headers())
    assert res.status_code == 422
    data = res.get_json()
    assert "error" in data
