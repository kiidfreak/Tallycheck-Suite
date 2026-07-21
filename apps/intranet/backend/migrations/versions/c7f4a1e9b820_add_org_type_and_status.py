"""Add org_type and status to public.organizations.

Revision ID: c7f4a1e9b820
Revises: a8e5d31c7b60
Create Date: 2026-07-21

`org_type` drives which report shape a tenant renders; `status` tracks the
provisioning lifecycle. Both live ONLY on public.organizations.

env.py replays every migration once per schema (public + each tenant), and these
ops target `public.organizations` explicitly — so without a guard the tenant
passes would re-alter the same public table and fail with "column already
exists". The `_is_public_pass()` guard runs the body only during the public
pass; on tenant passes it is a no-op that still advances that schema's
alembic_version, keeping every schema at the same head.

(The older organizations migration avoided this only by accident — tenant
schemas were stamped at a baseline past it, so they never replayed it.)

Cannot fail on existing data: both columns arrive with a server default, and
every current org is a live corporate/education tenant that satisfies
org_type='corporate' / status='active'. The operator can correct org_type for
church/visitor tenants afterward via PUT /organizations.
"""

from alembic import op
import sqlalchemy as sa


revision = 'c7f4a1e9b820'
down_revision = 'a8e5d31c7b60'
branch_labels = None
depends_on = None


def _is_public_pass() -> bool:
    """True during the public schema pass. env.py sets version_table_schema to
    the schema currently being migrated."""
    return op.get_context().version_table_schema == 'public'


def upgrade() -> None:
    if not _is_public_pass():
        return
    op.add_column(
        'organizations',
        sa.Column('org_type', sa.String(length=20), nullable=False, server_default='corporate'),
        schema='public',
    )
    op.add_column(
        'organizations',
        sa.Column('status', sa.String(length=20), nullable=False, server_default='active'),
        schema='public',
    )
    op.create_check_constraint(
        'ck_org_type',
        'organizations',
        "org_type IN ('corporate','education','church','visitor')",
        schema='public',
    )
    op.create_check_constraint(
        'ck_org_status',
        'organizations',
        "status IN ('pending','provisioning','active','failed')",
        schema='public',
    )


def downgrade() -> None:
    if not _is_public_pass():
        return
    op.drop_constraint('ck_org_status', 'organizations', schema='public', type_='check')
    op.drop_constraint('ck_org_type', 'organizations', schema='public', type_='check')
    op.drop_column('organizations', 'status', schema='public')
    op.drop_column('organizations', 'org_type', schema='public')
