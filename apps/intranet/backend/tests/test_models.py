from models import db, Role, Department, Employee

def test_create_role(app):
    """Test creating a new role."""
    role = Role(name="Software Engineer")
    db.session.add(role)
    db.session.commit()
    
    saved_role = Role.query.filter_by(name="Software Engineer").first()
    assert saved_role is not None
    assert saved_role.name == "Software Engineer"

def test_create_department(app):
    """Test creating a new department."""
    dept = Department(name="Design")
    db.session.add(dept)
    db.session.commit()
    
    saved_dept = Department.query.filter_by(name="Design").first()
    assert saved_dept is not None
    assert saved_dept.name == "Design"

def test_employee_nullable_fields(app):
    """
    Test the onboarding logic we discussed: 
    An employee should be able to be created WITHOUT a department or role initially.
    """
    emp = Employee(
        auth0_id="auth0|12345",
        email="test@adept.com",
        first_name="John",
        last_name="Doe"
    )
    db.session.add(emp)
    db.session.commit()
    
    saved_emp = Employee.query.filter_by(email="test@adept.com").first()
    assert saved_emp is not None
    assert saved_emp.auth0_id == "auth0|12345"
    assert saved_emp.is_approved is False # Default value
    assert saved_emp.department_id is None # Nullable
    assert saved_emp.role_id is None # Nullable

def test_employee_with_department_and_role(app):
    """Test creating an employee and assigning them a role and department."""
    role = Role(name="Manager")
    dept = Department(name="HR")
    
    db.session.add_all([role, dept])
    db.session.commit()
    
    emp = Employee(
        auth0_id="auth0|99999",
        email="jane@adept.com",
        first_name="Jane",
        last_name="Smith",
        role_id=role.id,
        department_id=dept.id,
        is_approved=True
    )
    db.session.add(emp)
    db.session.commit()
    
    saved_emp = Employee.query.filter_by(email="jane@adept.com").first()
    assert saved_emp.role.name == "Manager"
    assert saved_emp.department.name == "HR"
    assert saved_emp.is_approved is True
