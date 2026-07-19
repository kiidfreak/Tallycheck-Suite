import os
import sys

# Ensure the current directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

workspace_libs = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../libs'))
if workspace_libs not in sys.path:
    sys.path.insert(0, workspace_libs)

from app import app
from models import db, Organization, Role, Department

def seed_daystar_roles_and_departments() -> None:
    role_names = ['staff', 'school_admin', 'lecturer', 'teacher', 'guardian', 'super_admin']
    for name in role_names:
        if not Role.query.filter_by(role=name).first():
            db.session.add(Role(role=name))
            
    dept_names = [
        'school_of_science_engineering_and_technology',
        'school_of_communication_languages_and_performing_arts',
        'school_of_business_and_economics',
        'school_of_law',
        'school_of_arts_and_humanities',
        'school_of_human_and_social_sciences',
        'school_of_nursing',
        'daystar_church'
    ]
    for name in dept_names:
        if not Department.query.filter_by(name=name).first():
            db.session.add(Department(name=name))
    db.session.commit()

def seed_tenant():
    with app.app_context():
        # 1. Create Organization in public schema
        # Force search path to public first
        db.session.execute(db.text("SET search_path TO public"))
        
        org_id = "org_0D0uiOBBi91ZiW0v"
        subdomain = "daystar"
        schema_name = f"tenant_{org_id.lower()}"
        
        org = Organization.query.get(org_id)
        if not org:
            org = Organization(
                id=org_id,
                name="Daystar University",
                domain=subdomain,
                schema_name=schema_name,
                is_active=True
            )
            db.session.add(org)
            db.session.commit()
            print(f"Created Organization: {org.name}")
        else:
            print(f"Organization {org.name} already exists.")
            
        # 2. Create Schema in Postgres
        db.session.execute(db.text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"'))
        db.session.commit()
        print(f"Created Schema: {schema_name}")
        
        # 3. Create Tables in Schema
        conn = db.session.connection()
        conn.execute(db.text(f'SET search_path TO "{schema_name}"'))
        db.metadata.create_all(bind=conn)
        db.session.commit()
        print(f"Created all tables in schema: {schema_name}")
        
        # 4. Seed Roles and Departments in Schema
        seed_daystar_roles_and_departments()
        print(f"Seeded roles and departments in schema: {schema_name}")

if __name__ == '__main__':
    seed_tenant()
