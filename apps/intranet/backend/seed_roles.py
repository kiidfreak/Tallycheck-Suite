import os
import sys
from app import app
from auth_routes import seed_roles_and_departments

def seed() -> None:
    with app.app_context():
        print("Seeding database (roles, departments, and mock employees)...")
        seed_roles_and_departments()
        print("Database seeding complete!")

if __name__ == '__main__':
    seed()
