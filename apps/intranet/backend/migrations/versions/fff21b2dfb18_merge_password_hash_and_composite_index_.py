"""Merge password_hash and composite index branches

Revision ID: fff21b2dfb18
Revises: 7b786ee992b7, b23108964fdf
Create Date: 2026-06-18 12:56:13.775555

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fff21b2dfb18'
down_revision = ('7b786ee992b7', 'b23108964fdf')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
