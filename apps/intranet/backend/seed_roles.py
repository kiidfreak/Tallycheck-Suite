import os
import sys
from app import app
from auth_routes import seed_roles as seed_canonical_roles

def seed() -> None:
    with app.app_context():
        print("Seeding canonical roles...")
        seed_canonical_roles()
        print("Role seeding complete!")

if __name__ == '__main__':
    seed()
