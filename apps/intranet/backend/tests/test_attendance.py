import json
import pytest
from unittest.mock import patch
from datetime import datetime, timedelta
from models import Employee, AttendanceRecord, Role, Department, db

@pytest.fixture
def mock_verify_jwt():
    with patch('helpers.auth_helper.verify_jwt') as mock_jwt:
        mock_jwt.return_value = {
            'sub': 'auth0|mock-staff',
            'email': 'staff@adept.com'
        }
        yield mock_jwt

@pytest.fixture
def mock_time():
    """Mock datetime in attendance_routes to always be 8:00 AM to avoid cutoff failures."""
    with patch('attendance_routes.datetime') as mock_dt:
        from datetime import datetime
        mock_dt.utcnow.side_effect = datetime.utcnow
        mock_dt.now.return_value = datetime.utcnow().replace(hour=8, minute=0)
        mock_dt.date.side_effect = datetime.date
        yield mock_dt

@pytest.fixture
def auth_employee(app):
    """Creates a seeded approved employee for tests."""
    with app.app_context():
        role = Role.query.filter_by(name='staff').first()
        dept = Department.query.filter_by(name='software_development').first()
        
        emp = Employee(
            auth0_id='auth0|mock-staff',
            email='staff@adept.com',
            first_name='Mock',
            last_name='Staff',
            role_id=role.id,
            department_id=dept.id,
            is_approved=True
        )
        db.session.add(emp)
        db.session.commit()
    return emp

def get_auth_headers():
    return {'Authorization': 'Bearer fake-token'}

def test_clock_in_success(client, auth_employee, mock_verify_jwt, mock_time):
    """Test successful clock-in creates an open attendance record."""
    response = client.post(
        "/attendance/clock-in",
        headers=get_auth_headers(),
        json={"notes": "Starting shift", "source": "web"}
    )
    assert response.status_code == 201
    data = response.json["data"]
    record = data["record"]
    assert record["status"] == "open"
    assert record["notes"] == "Starting shift"
    assert record["source"] == "web"
    assert record["clock_out"] is None
    assert record["worked_hours"] is None
    assert record["work_date"] is not None

    record_db = AttendanceRecord.query.filter_by(status="open").first()
    assert record_db is not None
    assert record_db.notes == "Starting shift"

def test_double_clock_in_prevention(client, auth_employee, mock_verify_jwt, mock_time):
    """Test that a user cannot clock in twice without clocking out first."""
    res1 = client.post("/attendance/clock-in", headers=get_auth_headers())
    assert res1.status_code == 201

    res2 = client.post("/attendance/clock-in", headers=get_auth_headers())
    assert res2.status_code == 409
    assert res2.json["error"] == "already_clocked_in"

def test_clock_out_without_clock_in(client, auth_employee, mock_verify_jwt):
    """Test that clocking out without an active clock-in returns an error."""
    response = client.post(
        "/attendance/clock-out",
        headers=get_auth_headers(),
        json={"notes": "Trying to clock out"}
    )
    assert response.status_code == 409
    assert response.json["error"] == "not_clocked_in"

def test_clock_out_success(client, auth_employee, mock_verify_jwt, mock_time, app):
    """Test successful clock-out closes the record and calculates worked hours."""
    client.post("/attendance/clock-in", headers=get_auth_headers(), json={"notes": "In"})

    with app.app_context():
        record = AttendanceRecord.query.filter_by(clock_out=None).first()
        record.clock_in = datetime.utcnow() - timedelta(hours=10)
        db.session.commit()

    response = client.post(
        "/attendance/clock-out",
        headers=get_auth_headers(),
        json={"notes": "Out"}
    )
    assert response.status_code == 200
    data = response.json["data"]
    record = data["record"]
    assert record["status"] == "closed"
    assert record["clock_out"] is not None
    assert record["worked_hours"] == 10.0
    assert "In" in record["notes"]
    assert "Out" in record["notes"]

def test_unapproved_employee_cannot_clock(client, auth_employee, mock_verify_jwt, app):
    """Test that unapproved employees are rejected from clocking in/out."""
    with app.app_context():
        emp = Employee.query.filter_by(email="staff@adept.com").first()
        emp.is_approved = False
        db.session.commit()

    res1 = client.post("/attendance/clock-in", headers=get_auth_headers())
    assert res1.status_code == 403
    assert res1.json["error"] == "insufficient_permissions"

    res2 = client.post("/attendance/clock-out", headers=get_auth_headers())
    assert res2.status_code == 403
    assert res2.json["error"] == "insufficient_permissions"

def test_attendance_history_pagination_and_filter(client, auth_employee, mock_verify_jwt, app):
    """Test GET /attendance/me pagination and date range filtering."""
    with app.app_context():
        emp = Employee.query.filter_by(email="staff@adept.com").first()
        base_date = datetime.utcnow().date()
        for i in range(15):
            record = AttendanceRecord(
                employee_id=emp.id,
                clock_in=datetime.utcnow() - timedelta(days=i, hours=2),
                clock_out=datetime.utcnow() - timedelta(days=i),
                work_date=base_date - timedelta(days=i),
                source="web",
                status="closed",
                notes=f"Record {i}"
            )
            db.session.add(record)
        db.session.commit()

    response = client.get("/attendance/me?page=1&per_page=10", headers=get_auth_headers())
    assert response.status_code == 200
    data = response.json
    assert len(data["data"]) == 10
    assert data["meta"]["total"] == 15
    assert data["meta"]["page"] == 1
    assert data["meta"]["pages"] == 2
    assert data["meta"]["per_page"] == 10

    response2 = client.get("/attendance/me?page=2&per_page=10", headers=get_auth_headers())
    assert response2.status_code == 200
    assert len(response2.json["data"]) == 5

    with app.app_context():
        start_date = (base_date - timedelta(days=4)).isoformat()
        end_date = base_date.isoformat()
        response_filter = client.get(
            f"/attendance/me?date_from={start_date}&date_to={end_date}",
            headers=get_auth_headers()
        )
    assert response_filter.status_code == 200
    # Should only return records within those 5 days
    assert len(response_filter.json["data"]) == 5

def test_get_stats(client, auth_employee, mock_verify_jwt, app):
    """Test retrieving attendance stats for the authenticated employee."""
    with app.app_context():
        emp = Employee.query.filter_by(email="staff@adept.com").first()
        AttendanceRecord.query.filter_by(employee_id=emp.id).delete()
        db.session.commit()

    response = client.get("/attendance/stats", headers=get_auth_headers())
    print(response.status_code)
    print(response.json)
    assert response.status_code == 200
    assert response.json["data"]["hours_this_week"] == 0.0

    with app.app_context():
        emp = Employee.query.filter_by(email="staff@adept.com").first()
        now = datetime.utcnow()
        start_of_week = now - timedelta(days=now.weekday())
        start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)

        # Seed completed record (5 hours)
        record1 = AttendanceRecord(
            employee_id=emp.id,
            clock_in=start_of_week + timedelta(hours=8),
            clock_out=start_of_week + timedelta(hours=13),
            work_date=start_of_week.date(),
            source="web",
            status="closed",
            notes="Completed shift"
        )
        db.session.add(record1)
        db.session.commit()

    # Fetch updated stats
    response2 = client.get(
        "/attendance/stats",
        headers={"Authorization": "Bearer mock-staff"}
    )
    assert response2.status_code == 200
    # Expected hours: 5
    assert response2.json["data"]["hours_this_week"] == 5.0

    with app.app_context():
        emp = Employee.query.filter_by(email="staff@adept.com").first()
        # Add an active shift of 2 hours
        record2 = AttendanceRecord(
            employee_id=emp.id,
            clock_in=datetime.utcnow() - timedelta(hours=2),
            clock_out=None,
            work_date=datetime.utcnow().date(),
            source="web",
            status="open",
            notes="Active shift"
        )
        db.session.add(record2)
        db.session.commit()

    response3 = client.get("/attendance/stats", headers=get_auth_headers())
    assert response3.status_code == 200
    assert response3.json["data"]["hours_this_week"] == 7.0
