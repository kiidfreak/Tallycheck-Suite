"""Platform gate + schema-name guard. Pure functions, no DB, no app context."""

from __future__ import annotations

import pytest

from helpers.platform_helper import is_platform_super_admin
from utils.tenant_middleware import SCHEMA_NAME_RE


class TestIsPlatformSuperAdmin:
    def test_via_permissions_claim(self):
        assert is_platform_super_admin({"permissions": ["super_admin", "read:x"]})

    def test_via_roles_claim(self):
        assert is_platform_super_admin({"https://adept.api/roles": ["super_admin"]})

    def test_either_claim_suffices(self):
        assert is_platform_super_admin({"permissions": [], "https://adept.api/roles": ["super_admin"]})

    @pytest.mark.parametrize("payload", [
        {},
        {"permissions": []},
        {"permissions": ["company_admin", "hr_admin"]},
        {"https://adept.api/roles": ["school_admin"]},
        {"permissions": None, "https://adept.api/roles": None},
        # A tenant admin is NOT a platform admin — the whole point of the gate.
        {"permissions": ["manage:settings"], "https://adept.api/roles": ["company_admin"]},
    ])
    def test_rejects_non_platform_tokens(self, payload):
        assert not is_platform_super_admin(payload)

    def test_does_not_touch_the_database(self):
        # No app context, no session — proves the gate is usable before a schema
        # is pinned, which is the reason it reads the token and not an Employee row.
        assert is_platform_super_admin({"permissions": ["super_admin"]}) is True


class TestSchemaNameGuard:
    @pytest.mark.parametrize("name", ["public", "tenant_acme", "tenant_org_0d0u"])
    def test_accepts_real_schema_names(self, name):
        assert SCHEMA_NAME_RE.fullmatch(name)

    @pytest.mark.parametrize("name", [
        'tenant"; DROP TABLE employees; --',
        "tenant acme",
        "Tenant_Acme",
        "",
        "tenant-acme",
    ])
    def test_rejects_injection_and_malformed(self, name):
        assert not SCHEMA_NAME_RE.fullmatch(name)
