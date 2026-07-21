"""tenant_scope cross-schema switching + session hygiene — against real Postgres.

This covers the single highest-risk claim in the platform work: that switching
into a tenant schema to read its data ALWAYS restores search_path to public
afterward, even when the body raises. A leak here would bleed one tenant's schema
into the next request on a pooled connection.

conftest's `app` fixture is SQLite-only (Organization is bound to public, which
SQLite cannot create), so these skip unless a Postgres URL is provided:

    PLATFORM_TEST_DATABASE_URL=postgresql://... pytest tests/test_tenant_scope_db.py

The dev docker Postgres (port 5434) satisfies this.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

PG_URL = os.environ.get("PLATFORM_TEST_DATABASE_URL") or os.environ.get("DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not PG_URL or not PG_URL.startswith("postgresql"),
    reason="needs a Postgres URL in PLATFORM_TEST_DATABASE_URL / DATABASE_URL",
)

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND.parents[2] / "libs"))


@pytest.fixture(scope="module")
def app_ctx():
    os.environ.setdefault("DATABASE_URL", PG_URL or "")
    from __init__ import create_app
    from models import db

    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": PG_URL})
    with app.app_context():
        # A throwaway schema with one table + row to prove the switch reads it.
        db.session.execute(db.text('DROP SCHEMA IF EXISTS scope_probe CASCADE'))
        db.session.execute(db.text('CREATE SCHEMA scope_probe'))
        db.session.execute(db.text('CREATE TABLE scope_probe.marker (n integer)'))
        db.session.execute(db.text('INSERT INTO scope_probe.marker (n) VALUES (42)'))
        db.session.execute(db.text('SET search_path TO public'))
        db.session.commit()
        yield app, db
        db.session.execute(db.text('DROP SCHEMA IF EXISTS scope_probe CASCADE'))
        db.session.commit()


def current_search_path(db) -> str:
    return db.session.execute(db.text("SHOW search_path")).scalar()


class TestTenantScope:
    def test_body_sees_the_target_schema(self, app_ctx):
        _, db = app_ctx
        from helpers.platform_helper import tenant_scope

        with tenant_scope("scope_probe"):
            # Unqualified — resolves via the switched search_path.
            n = db.session.execute(db.text("SELECT n FROM marker")).scalar()
        assert n == 42

    def test_restores_public_after_a_clean_run(self, app_ctx):
        _, db = app_ctx
        from helpers.platform_helper import tenant_scope

        with tenant_scope("scope_probe"):
            pass
        assert "scope_probe" not in current_search_path(db)
        assert "public" in current_search_path(db)

    def test_restores_public_even_when_the_body_raises(self, app_ctx):
        _, db = app_ctx
        from helpers.platform_helper import tenant_scope

        with pytest.raises(RuntimeError):
            with tenant_scope("scope_probe"):
                raise RuntimeError("boom")
        # The whole point: an exception path must not leave the connection pinned
        # to the tenant schema.
        assert "scope_probe" not in current_search_path(db)
        assert "public" in current_search_path(db)

    def test_rejects_a_malformed_schema_name_before_switching(self, app_ctx):
        _, db = app_ctx
        from helpers.platform_helper import tenant_scope

        with pytest.raises(ValueError):
            with tenant_scope('evil"; DROP TABLE x; --'):
                pass
        assert "public" in current_search_path(db)
