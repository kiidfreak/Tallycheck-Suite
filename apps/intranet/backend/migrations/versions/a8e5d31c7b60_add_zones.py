"""Add zones, and place existing beacons in them.

Replaces `ble_beacons.location` (free text) with a structured `zones` table and a
`ble_beacons.zone_id` foreign key.

Revision ID: a8e5d31c7b60
Revises: f1a3c7b92e04
Create Date: 2026-07-20

Notes:

* `migrations/env.py` replays this once per tenant schema under that schema's
  `search_path`, so every statement is unqualified.

* The backfill turns each distinct non-empty `location` string into a zone and
  points the matching beacons at it. Without it the feature ships with an empty
  table and every beacon unplaced, which is a worse starting state than the free
  text it replaces. It is idempotent: re-running finds the zones already present
  and re-points the same beacons.

* `BeaconAssignment` is untouched. Beacon->department ("who uses this") is
  genuinely many-to-many and keeps its `uq_beacon_dept` constraint;
  beacon->zone ("where is it bolted") is one place, hence a column.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = 'a8e5d31c7b60'
down_revision = 'f1a3c7b92e04'
branch_labels = None
depends_on = None


ZONE_TYPES = (
    'room', 'classroom', 'hall', 'entrance', 'gate',
    'loading_bay', 'storage', 'ward', 'yard', 'general',
)


def upgrade() -> None:
    op.create_table(
        'zones',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('zone_type', sa.String(length=30), server_default='general', nullable=False),
        sa.Column('org_unit_id', sa.Integer(), nullable=True),
        sa.Column('code', sa.String(length=50), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('capacity', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        # Reserved for indoor mapping. Nullable now costs nothing; adding them
        # later means another migration fanned across every tenant schema.
        sa.Column('floor_label', sa.String(length=50), nullable=True),
        sa.Column('geometry', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('floor_plan_url', sa.String(length=512), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['org_unit_id'], ['departments.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint(
            "zone_type IN ('room','classroom','hall','entrance','gate',"
            "'loading_bay','storage','ward','yard','general')",
            name='ck_zone_type',
        ),
    )

    # Partial indexes, matching the departments pattern: a plain composite would
    # leave unassigned zones unconstrained, since Postgres treats NULLs as
    # distinct.
    op.create_index(
        'uq_zone_unit_name',
        'zones',
        ['org_unit_id', 'name'],
        unique=True,
        postgresql_where=sa.text('org_unit_id IS NOT NULL'),
    )
    op.create_index(
        'uq_zone_global_name',
        'zones',
        ['name'],
        unique=True,
        postgresql_where=sa.text('org_unit_id IS NULL'),
    )

    op.add_column('ble_beacons', sa.Column('zone_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_beacon_zone', 'ble_beacons', 'zones', ['zone_id'], ['id'], ondelete='SET NULL'
    )

    # --- backfill: distinct location strings become zones ------------------
    # Trimmed, and only where a location was actually recorded. Zones land
    # unassigned to an org unit (org_unit_id NULL), which the global partial
    # unique index covers.
    op.execute(
        """
        INSERT INTO zones (name, zone_type, is_active, created_at, updated_at)
        SELECT DISTINCT TRIM(b.location), 'general', true, now(), now()
        FROM ble_beacons b
        WHERE b.location IS NOT NULL
          AND TRIM(b.location) <> ''
          AND NOT EXISTS (
              SELECT 1 FROM zones z
              WHERE z.name = TRIM(b.location) AND z.org_unit_id IS NULL
          )
        """
    )
    op.execute(
        """
        UPDATE ble_beacons b
        SET zone_id = z.id
        FROM zones z
        WHERE z.name = TRIM(b.location)
          AND z.org_unit_id IS NULL
          AND b.location IS NOT NULL
          AND TRIM(b.location) <> ''
          AND b.zone_id IS NULL
        """
    )


def downgrade() -> None:
    op.drop_constraint('fk_beacon_zone', 'ble_beacons', type_='foreignkey')
    op.drop_column('ble_beacons', 'zone_id')
    op.drop_index('uq_zone_global_name', table_name='zones')
    op.drop_index('uq_zone_unit_name', table_name='zones')
    # `ble_beacons.location` was never cleared, so dropping zones loses no
    # placement information that was not already duplicated there.
    op.drop_table('zones')
