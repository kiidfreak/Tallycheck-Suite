"""Tenant resolution and schema-name validation.

`set_tenant_schema` decides which Postgres schema a request reads and writes.
A bug here leaks one tenant's data into another's session, so it is the highest
consequence module in the backend.

These tests deliberately avoid the `app`/`client` fixtures in conftest.py: those
require Postgres (Organization is bound to the `public` schema, which SQLite
cannot create), so they only run under docker compose. Tenant *resolution* and
schema-name *validation* are pure functions of the request and the org row, so
they are covered here in a form that runs anywhere.
"""

import jwt
import pytest
from flask import Flask

from utils.tenant_middleware import SCHEMA_NAME_RE, get_tenant_from_request


@pytest.fixture
def flask_app():
    return Flask(__name__)


def bearer(payload: dict) -> dict:
    token = jwt.encode(payload, "irrelevant-test-secret", algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}


class TestSchemaNameValidation:
    """The name is interpolated into `SET search_path`, so the allowlist is the
    only thing standing between a bad row and arbitrary SQL."""

    @pytest.mark.parametrize("name", [
        "public",
        "tenant_org_0d0uiobbi91ziw0v",
        "tenant_acme",
        "tenant_123",
    ])
    def test_accepts_generated_schema_names(self, name):
        assert SCHEMA_NAME_RE.fullmatch(name)

    @pytest.mark.parametrize("name", [
        'tenant"; DROP TABLE employees; --',
        "tenant acme",
        "tenant-acme",
        "Tenant_Acme",       # uppercase is never generated; reject rather than fold
        "tenant.acme",
        "",
        "tenant\nacme",      # fullmatch, not match — a trailing newline must not pass
    ])
    def test_rejects_anything_else(self, name):
        assert not SCHEMA_NAME_RE.fullmatch(name)

    def test_rejects_underscore_bearing_injection(self):
        """Regression: the previous guard was

            if not name.isalnum() and '_' not in name

        For "drop_table" the first clause is True but the second is False, so the
        whole condition is False and the name passed validation. Any injection
        payload containing an underscore slipped through.
        """
        payload = 'x_x"; DROP TABLE employees; --'
        assert not payload.isalnum() and "_" in payload  # old guard passed this
        assert not SCHEMA_NAME_RE.fullmatch(payload)     # new guard does not


class TestTenantResolution:
    def test_prefers_standard_auth0_org_claim(self, flask_app):
        headers = bearer({"org_id": "org_ABC", "https://tallycheck.co.ke/org_id": "org_OTHER"})
        with flask_app.test_request_context("/", headers=headers):
            assert get_tenant_from_request() == ("org_ABC", "jwt_org_id")

    def test_falls_back_to_custom_claim(self, flask_app):
        headers = bearer({"https://tallycheck.co.ke/org_id": "org_CUSTOM"})
        with flask_app.test_request_context("/", headers=headers):
            assert get_tenant_from_request() == ("org_CUSTOM", "jwt_custom_org")

    def test_jwt_outranks_header(self, flask_app):
        headers = {**bearer({"org_id": "org_FROM_JWT"}), "X-Tenant-Subdomain": "acme"}
        with flask_app.test_request_context("/", headers=headers):
            assert get_tenant_from_request() == ("org_FROM_JWT", "jwt_org_id")

    def test_header_used_when_no_token(self, flask_app):
        with flask_app.test_request_context("/", headers={"X-Tenant-Subdomain": "acme"}):
            assert get_tenant_from_request() == ("acme", "header")

    def test_malformed_token_falls_through_to_header(self, flask_app):
        headers = {"Authorization": "Bearer not-a-jwt", "X-Tenant-Subdomain": "acme"}
        with flask_app.test_request_context("/", headers=headers):
            assert get_tenant_from_request() == ("acme", "header")

    @pytest.mark.parametrize("host", [
        "acme.tallycheck.co.ke",
        "acme.tallycheck.co.ke:443",   # port must not become part of the label
        "ACME.TallyCheck.co.ke",       # hosts are case-insensitive
    ])
    def test_hostname_subdomain(self, flask_app, host):
        with flask_app.test_request_context("/", headers={"Host": host}):
            assert get_tenant_from_request() == ("acme", "hostname")

    @pytest.mark.parametrize("host", [
        "www.tallycheck.co.ke",
        "api.tallycheck.co.ke",
        "app.tallycheck.co.ke",
        "localhost:8001",
        "127.0.0.1:8001",
        "some-other-domain.com",
        "acme.tallycheck.co.ke.evil.com",   # suffix must anchor, not merely appear
        "deep.nested.tallycheck.co.ke",     # multi-label prefix is not a tenant
    ])
    def test_reserved_and_unrelated_hosts_resolve_no_tenant(self, flask_app, host):
        with flask_app.test_request_context("/", headers={"Host": host}):
            assert get_tenant_from_request() == (None, None)

    def test_apex_domain_is_not_a_tenant(self, flask_app):
        """Regression: the old `len(parts) > 2` check treated the apex domain as
        a subdomain, because "tallycheck.co.ke" is three labels. Every request to
        the bare domain resolved as a tenant named "tallycheck" — harmless only
        for as long as no org claimed that subdomain.
        """
        with flask_app.test_request_context("/", headers={"Host": "tallycheck.co.ke"}):
            assert get_tenant_from_request() == (None, None)

    def test_no_signal_at_all(self, flask_app):
        with flask_app.test_request_context("/"):
            assert get_tenant_from_request() == (None, None)

    def test_signature_is_not_verified_at_this_stage(self, flask_app):
        """Tenant resolution runs before auth. It reads the org claim from an
        unverified token by design; `roles_required` verifies separately. This
        test pins that intent so the unverified decode is not mistaken for a bug.
        """
        headers = {"Authorization": "Bearer " + jwt.encode({"org_id": "org_X"}, "wrong-key", algorithm="HS256")}
        with flask_app.test_request_context("/", headers=headers):
            assert get_tenant_from_request() == ("org_X", "jwt_org_id")
