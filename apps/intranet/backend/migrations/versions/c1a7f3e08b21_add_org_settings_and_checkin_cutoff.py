"""add org_settings table and employees.checkin_cutoff_hour

Backfills the two model changes that shipped without a migration: the
org_settings table (models.OrgSettings) and Employee.checkin_cutoff_hour.

Both are created defensively. Tenant schemas are provisioned two different
ways in this project -- older ones by db.metadata.create_all() in seed_org.py,
newer ones by this migration chain -- so a given schema may already have one,
both, or neither. Plain create_table/add_column would fail on the schemas that
already have them.

Revision ID: c1a7f3e08b21
Revises: b309859846bf
Create Date: 2026-07-19

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c1a7f3e08b21'
down_revision = 'b309859846bf'
branch_labels = None
depends_on = None


def _current_schema(conn) -> str:
    """The schema this pass is targeting, per the connection's search_path."""
    return conn.execute(sa.text("SELECT current_schema()")).scalar()


def upgrade():
    conn = op.get_bind()
    schema = _current_schema(conn)
    inspector = sa.inspect(conn)

    if 'org_settings' not in inspector.get_table_names(schema=schema):
        op.create_table(
            'org_settings',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('checkin_cutoff_hours_after_start', sa.Integer(),
                      server_default='5', nullable=False),
            sa.Column('reminder_enabled', sa.Boolean(),
                      server_default='false', nullable=False),
            sa.Column('reminder_minutes_before_cutoff', sa.Integer(),
                      server_default='30', nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.Column('updated_by', sa.dialects.postgresql.UUID(as_uuid=True),
                      nullable=True),
            sa.ForeignKeyConstraint(['updated_by'], ['employees.id'],
                                    ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id'),
        )

    employee_columns = {c['name'] for c in inspector.get_columns('employees', schema=schema)}
    if 'checkin_cutoff_hour' not in employee_columns:
        op.add_column('employees', sa.Column('checkin_cutoff_hour', sa.Integer(), nullable=True))


def downgrade():
    conn = op.get_bind()
    schema = _current_schema(conn)
    inspector = sa.inspect(conn)

    employee_columns = {c['name'] for c in inspector.get_columns('employees', schema=schema)}
    if 'checkin_cutoff_hour' in employee_columns:
        op.drop_column('employees', 'checkin_cutoff_hour')

    if 'org_settings' in inspector.get_table_names(schema=schema):
        op.drop_table('org_settings')
