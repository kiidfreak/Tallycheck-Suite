import os
import sys
import random
import uuid
from datetime import datetime, timedelta, date, time, timezone

# Ensure the current directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

workspace_libs = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../libs'))
if workspace_libs not in sys.path:
    sys.path.insert(0, workspace_libs)

from app import app
from models import db, Employee, AttendanceRecord, Department, Role

def seed():
    with app.app_context():
        schema_name = "tenant_org_0d0uiobbi91ziw0v"
        
        # Set search path to tenant schema
        db.session.execute(db.text(f'SET search_path TO "{schema_name}", public'))
        db.session.commit()
        
        # 1. Fetch departments and roles to link
        depts = Department.query.all()
        roles = Role.query.all()
        
        dept_map = {d.name: d.id for d in depts}
        role_map = {r.role: r.id for r in roles}
        
        print(f"Loaded departments: {list(dept_map.keys())}")
        print(f"Loaded roles: {list(role_map.keys())}")
        
        # 2. Define mock employees to seed
        mock_employees_data = [
            # Admins/Lecturers
            {
                "email": "anne@daystar.tallycheck.co.ke",
                "first_name": "Anne",
                "last_name": "Admin",
                "role_name": "school_admin",
                "dept_name": "school_of_science_engineering_and_technology",
                "is_manager": True,
                "is_active": True,
                "is_approved": True
            },
            {
                "email": "jane@daystar.tallycheck.co.ke",
                "first_name": "Jane",
                "last_name": "Lecturer",
                "role_name": "lecturer",
                "dept_name": "school_of_science_engineering_and_technology",
                "is_manager": True,
                "is_active": True,
                "is_approved": True
            },
            {
                "email": "esther@daystar.tallycheck.co.ke",
                "first_name": "Esther",
                "last_name": "Teacher",
                "role_name": "teacher",
                "dept_name": "daystar_church",
                "is_manager": False,
                "is_active": True,
                "is_approved": True
            },
            {
                "email": "grace@daystar.tallycheck.co.ke",
                "first_name": "Grace",
                "last_name": "Guardian",
                "role_name": "guardian",
                "dept_name": "daystar_church",
                "is_manager": False,
                "is_active": True,
                "is_approved": True
            },
            # Mock Students/Staff to populate stats
            {
                "email": "albert@daystar.tallycheck.co.ke",
                "first_name": "Albert",
                "last_name": "Einstein",
                "role_name": "staff",
                "dept_name": "school_of_science_engineering_and_technology",
                "is_manager": False,
                "is_active": True,
                "is_approved": True
            },
            {
                "email": "marie@daystar.tallycheck.co.ke",
                "first_name": "Marie",
                "last_name": "Curie",
                "role_name": "staff",
                "dept_name": "school_of_science_engineering_and_technology",
                "is_manager": False,
                "is_active": True,
                "is_approved": True
            },
            {
                "email": "john@daystar.tallycheck.co.ke",
                "first_name": "John",
                "last_name": "Locke",
                "role_name": "staff",
                "dept_name": "school_of_law",
                "is_manager": False,
                "is_active": True,
                "is_approved": True
            },
            {
                "email": "adam@daystar.tallycheck.co.ke",
                "first_name": "Adam",
                "last_name": "Smith",
                "role_name": "staff",
                "dept_name": "school_of_business_and_economics",
                "is_manager": False,
                "is_active": True,
                "is_approved": True
            },
            {
                "email": "florence@daystar.tallycheck.co.ke",
                "first_name": "Florence",
                "last_name": "Nightingale",
                "role_name": "staff",
                "dept_name": "school_of_nursing",
                "is_manager": False,
                "is_active": True,
                "is_approved": True
            },
            {
                "email": "plato@daystar.tallycheck.co.ke",
                "first_name": "Plato",
                "last_name": "Philosopher",
                "role_name": "staff",
                "dept_name": "school_of_arts_and_humanities",
                "is_manager": False,
                "is_active": True,
                "is_approved": True
            }
        ]
        
        employees = []
        for item in mock_employees_data:
            emp = Employee.query.filter_by(email=item["email"]).first()
            if not emp:
                emp = Employee(
                    id=str(uuid.uuid4()),
                    auth0_id=f"auth0|mock_{item['first_name'].lower()}",
                    email=item["email"],
                    first_name=item["first_name"],
                    last_name=item["last_name"],
                    role_id=role_map[item["role_name"]],
                    department_id=dept_map[item["dept_name"]],
                    is_manager=item["is_manager"],
                    is_active=item["is_active"],
                    is_approved=item["is_approved"],
                    is_internal=True,
                    shift_type="standard",
                    shift_hours="8am-5pm",
                    created_at=datetime.now(timezone.utc)
                )
                db.session.add(emp)
                print(f"Created Employee: {emp.first_name} {emp.last_name}")
            else:
                # Update existing
                emp.role_id = role_map[item["role_name"]]
                emp.department_id = dept_map[item["dept_name"]]
                emp.is_approved = True
                emp.is_active = True
                print(f"Updated Employee: {emp.first_name} {emp.last_name}")
            employees.append(emp)
            
        db.session.commit()
        
        # Add the logged-in test user if they exist
        test_user = Employee.query.filter_by(email="imaina@daystar.ac.ke").first()
        if test_user:
            # Let's assign them to a department so they show up in charts!
            test_user.department_id = dept_map["school_of_science_engineering_and_technology"]
            db.session.commit()
            employees.append(test_user)
            print("Linked Test Student account to School of Science, Engineering & Technology department")
            
        # 3. Seed 30 days of attendance
        print("Generating realistic attendance records for the last 30 days...")
        
        # Clear existing attendance first to avoid duplicates
        AttendanceRecord.query.delete()
        
        today = date.today()
        start_date = today - timedelta(days=30)
        records_created = 0
        
        for i in range(31):
            current_date = start_date + timedelta(days=i)
            # Skip weekends
            if current_date.weekday() >= 5:
                continue
                
            for emp in employees:
                # Skip guardians/external helpers
                if emp.role.role in ('guardian', 'super_admin'):
                    continue
                    
                # 10% chance of absence
                if random.random() < 0.10:
                    continue
                    
                # 60% chance they clock in early, 40% chance late
                is_late = random.random() < 0.25
                if is_late:
                    in_hour = 8
                    in_minute = random.randint(1, 45)
                else:
                    in_hour = 7
                    in_minute = random.randint(30, 59)
                    
                clock_in_dt = datetime.combine(current_date, time(in_hour, in_minute))
                
                # Worked between 7.5 to 9.5 hours
                work_duration = timedelta(hours=random.uniform(7.5, 9.5))
                clock_out_dt = clock_in_dt + work_duration
                
                record = AttendanceRecord(
                    employee_id=emp.id,
                    clock_in=clock_in_dt,
                    clock_out=clock_out_dt,
                    work_date=current_date,
                    source='web',
                    status='closed'
                )
                db.session.add(record)
                records_created += 1
                
        db.session.commit()
        print(f"Successfully generated {records_created} attendance records!")

if __name__ == '__main__':
    seed()
