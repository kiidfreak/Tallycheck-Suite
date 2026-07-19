"""add sunday school classes and teacher assignment

Sunday School runs separate classes with their own teachers, but Child.group_name
was a free-text label with no link to any Employee -- so every teacher saw the
entire church roster. This adds:

  sunday_school_classes  - the classes themselves
  class_teachers         - which teacher(s) run which class
  children.class_id      - which class a child belongs to

Existing children are backfilled by distinct group_name, so current rows keep
working without manual data entry.

Revision ID: d4b2c9e15f70
Revises: c1a7f3e08b21
Create Date: 2026-07-19

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'd4b2c9e15f70'
down_revision = 'c1a7f3e08b21'
branch_labels = None
depends_on = None


def _schema(conn) -> str:
    return conn.execute(sa.text("SELECT current_schema()")).scalar()


def upgrade():
    conn = op.get_bind()
    schema = _schema(conn)
    inspector = sa.inspect(conn)
    tables = set(inspector.get_table_names(schema=schema))

    if 'sunday_school_classes' not in tables:
        op.create_table(
            'sunday_school_classes',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=100), nullable=False),
            sa.Column('description', sa.String(length=255), nullable=True),
            sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('name'),
        )

    if 'class_teachers' not in tables:
        op.create_table(
            'class_teachers',
            sa.Column('class_id', sa.Integer(), nullable=False),
            sa.Column('teacher_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('is_lead', sa.Boolean(), server_default='false', nullable=False),
            sa.Column('assigned_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['class_id'], ['sunday_school_classes.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['teacher_id'], ['employees.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('class_id', 'teacher_id'),
        )

    # 'children' only exists once the safechild migration has run for this schema.
    if 'children' in tables:
        child_columns = {c['name'] for c in inspector.get_columns('children', schema=schema)}
        if 'class_id' not in child_columns:
            op.add_column('children', sa.Column('class_id', sa.Integer(), nullable=True))
            op.create_foreign_key(
                'fk_children_class', 'children', 'sunday_school_classes',
                ['class_id'], ['id'], ondelete='SET NULL',
            )

            # Backfill: one class per distinct group_name, then point children at it.
            conn.execute(sa.text("""
                INSERT INTO sunday_school_classes (name, description, is_active, created_at)
                SELECT DISTINCT c.group_name, 'Backfilled from group_name', true, NOW()
                FROM children c
                WHERE c.group_name IS NOT NULL
                  AND c.group_name <> ''
                  AND NOT EXISTS (
                    SELECT 1 FROM sunday_school_classes s WHERE s.name = c.group_name
                  )
            """))
            conn.execute(sa.text("""
                UPDATE children c
                SET class_id = s.id
                FROM sunday_school_classes s
                WHERE s.name = c.group_name AND c.class_id IS NULL
            """))


def downgrade():
    conn = op.get_bind()
    schema = _schema(conn)
    inspector = sa.inspect(conn)
    tables = set(inspector.get_table_names(schema=schema))

    if 'children' in tables:
        child_columns = {c['name'] for c in inspector.get_columns('children', schema=schema)}
        if 'class_id' in child_columns:
            op.drop_constraint('fk_children_class', 'children', type_='foreignkey')
            op.drop_column('children', 'class_id')

    if 'class_teachers' in tables:
        op.drop_table('class_teachers')
    if 'sunday_school_classes' in tables:
        op.drop_table('sunday_school_classes')
