"""change attendance id to int and add edited_by field

Revision ID: d13d99531a5a
Revises: fff21b2dfb18
Create Date: 2026-06-25 07:54:56.908773

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.

revision = 'd13d99531a5a'
down_revision = 'fff21b2dfb18'
branch_labels = None
depends_on = None


def upgrade():
    # Drop constraints that depend on attendance_records
    op.drop_constraint('audit_log_record_changed_fkey', 'audit_log', type_='foreignkey')
    
    # Drop and recreate attendance_records to guarantee column order
    op.execute('DROP TABLE attendance_records CASCADE')
    
    op.create_table(
        'attendance_records',
        sa.Column('id', sa.Integer(), autoincrement=True, primary_key=True, nullable=False),
        sa.Column('employee_id', sa.UUID(), sa.ForeignKey('employees.id', ondelete='CASCADE'), nullable=False),
        sa.Column('clock_in', sa.DateTime(), nullable=False),
        sa.Column('clock_out', sa.DateTime(), nullable=True),
        sa.Column('work_date', sa.Date(), nullable=False),
        sa.Column('source', sa.String(length=50), nullable=False, server_default='web'),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('edited_by', sa.UUID(), sa.ForeignKey('employees.id', ondelete='SET NULL'), nullable=True)
    )
    op.create_index('idx_emp_work_date', 'attendance_records', ['employee_id', 'work_date'])
    op.create_index(op.f('ix_attendance_records_employee_id'), 'attendance_records', ['employee_id'])
    
    # Fix audit_log record_changed column
    op.execute('ALTER TABLE audit_log DROP COLUMN record_changed CASCADE')
    op.execute('ALTER TABLE audit_log ADD COLUMN record_changed INTEGER NOT NULL')
    op.create_foreign_key('audit_log_record_changed_fkey', 'audit_log', 'attendance_records', ['record_changed'], ['id'], ondelete='CASCADE')

def downgrade():
    op.drop_constraint('audit_log_record_changed_fkey', 'audit_log', type_='foreignkey')
    
    op.execute('DROP TABLE attendance_records CASCADE')
    
    op.create_table(
        'attendance_records',
        sa.Column('id', sa.UUID(), primary_key=True, server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('employee_id', sa.UUID(), sa.ForeignKey('employees.id', ondelete='CASCADE'), nullable=False),
        sa.Column('clock_in', sa.DateTime(), nullable=False),
        sa.Column('clock_out', sa.DateTime(), nullable=True),
        sa.Column('work_date', sa.Date(), nullable=False),
        sa.Column('source', sa.String(length=50), nullable=False, server_default='web'),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True)
    )
    op.create_index('idx_emp_work_date', 'attendance_records', ['employee_id', 'work_date'])
    op.create_index(op.f('ix_attendance_records_employee_id'), 'attendance_records', ['employee_id'])
    
    op.execute('ALTER TABLE audit_log DROP COLUMN record_changed CASCADE')
    op.execute('ALTER TABLE audit_log ADD COLUMN record_changed UUID NOT NULL')
    op.create_foreign_key('audit_log_record_changed_fkey', 'audit_log', 'attendance_records', ['record_changed'], ['id'], ondelete='CASCADE')
