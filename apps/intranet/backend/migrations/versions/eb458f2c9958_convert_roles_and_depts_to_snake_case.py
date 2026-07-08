"""convert_roles_and_depts_to_snake_case

Revision ID: eb458f2c9958
Revises: b8dd6dbd0fde
Create Date: 2026-06-17 14:25:56.198699

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'eb458f2c9958'
down_revision = 'b8dd6dbd0fde'
branch_labels = None
depends_on = None


def upgrade():
    # Convert roles to snake_case
    op.execute("UPDATE roles SET name = 'super_admin' WHERE name = 'super-admin'")
    op.execute("UPDATE roles SET name = 'call_centre_agent' WHERE name = 'call-centre-agent'")
    op.execute("UPDATE roles SET name = 'call_centre_admin' WHERE name = 'call-centre-admin'")

    # Convert departments to snake_case
    op.execute("UPDATE departments SET name = 'engineering' WHERE name = 'Engineering'")
    op.execute("UPDATE departments SET name = 'people_operations' WHERE name = 'People Operations'")
    op.execute("UPDATE departments SET name = 'executive' WHERE name = 'Executive'")
    op.execute("UPDATE departments SET name = 'call_centre' WHERE name = 'Call Centre'")
    op.execute("UPDATE departments SET name = 'sales' WHERE name = 'Sales'")
    op.execute("UPDATE departments SET name = 'marketing' WHERE name = 'Marketing'")
    op.execute("UPDATE departments SET name = 'operations' WHERE name = 'Operations'")
    op.execute("UPDATE departments SET name = 'software_development' WHERE name = 'Software Development'")
    op.execute("UPDATE departments SET name = 'cloud_and_business_ops' WHERE name = 'Cloud and Business Ops'")
    op.execute("UPDATE departments SET name = 'business_efficiency' WHERE name = 'Business Efficiency'")
    op.execute("UPDATE departments SET name = 'finance' WHERE name = 'Finance'")


def downgrade():
    # Revert roles back to kebab-case
    op.execute("UPDATE roles SET name = 'super-admin' WHERE name = 'super_admin'")
    op.execute("UPDATE roles SET name = 'call-centre-agent' WHERE name = 'call_centre_agent'")
    op.execute("UPDATE roles SET name = 'call-centre-admin' WHERE name = 'call_centre_admin'")

    # Revert departments back to Title Case
    op.execute("UPDATE departments SET name = 'Engineering' WHERE name = 'engineering'")
    op.execute("UPDATE departments SET name = 'People Operations' WHERE name = 'people_operations'")
    op.execute("UPDATE departments SET name = 'Executive' WHERE name = 'executive'")
    op.execute("UPDATE departments SET name = 'Call Centre' WHERE name = 'call_centre'")
    op.execute("UPDATE departments SET name = 'Sales' WHERE name = 'sales'")
    op.execute("UPDATE departments SET name = 'Marketing' WHERE name = 'marketing'")
    op.execute("UPDATE departments SET name = 'Operations' WHERE name = 'operations'")
    op.execute("UPDATE departments SET name = 'Software Development' WHERE name = 'software_development'")
    op.execute("UPDATE departments SET name = 'Cloud and Business Ops' WHERE name = 'cloud_and_business_ops'")
    op.execute("UPDATE departments SET name = 'Business Efficiency' WHERE name = 'business_efficiency'")
    op.execute("UPDATE departments SET name = 'Finance' WHERE name = 'finance'")
