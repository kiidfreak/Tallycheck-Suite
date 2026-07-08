"""Update attendance status enum

Revision ID: b9d8e3f9a1b2
Revises: a7c7e2dcb002
Create Date: 2026-07-03 14:55:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b9d8e3f9a1b2'
down_revision = 'a7c7e2dcb002'
branch_labels = None
depends_on = None


def upgrade():
    # Update existing attendance_records rows
    op.execute("UPDATE attendance_records SET status = 'open' WHERE status = 'clocked_in'")
    op.execute("UPDATE attendance_records SET status = 'closed' WHERE status = 'present'")


def downgrade():
    op.execute("UPDATE attendance_records SET status = 'clocked_in' WHERE status = 'open'")
    op.execute("UPDATE attendance_records SET status = 'present' WHERE status = 'closed'")
