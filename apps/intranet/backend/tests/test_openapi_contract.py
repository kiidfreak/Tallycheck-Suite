"""The spec is the source of truth. This test proves Flask still matches it.

Without this, `docs/api/*.openapi.yaml` drifts silently — which is exactly what
happened to the previous spec: it accumulated ten undocumented route groups and
described a role vocabulary the code had long since replaced.

Deliberately does NOT use the `app`/`client` fixtures from conftest.py: those
need Postgres (Organization is bound to the `public` schema, which SQLite cannot
create) and fail locally. Building the app directly with an in-memory SQLite URI
is enough to read `url_map`, because no request is ever issued.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml", reason="PyYAML is required for contract tests")

SPEC_PATH = Path(__file__).resolve().parents[4] / "docs" / "api" / "tcheck-corporate.openapi.yaml"

# Routes that exist for infrastructure, not as part of the public contract.
UNDOCUMENTED_BY_DESIGN = {
    ("GET", "/"),          # hello banner
    ("GET", "/health"),    # documented, but harmless either way
}

HTTP_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE"}


def _flask_operations() -> set[tuple[str, str]]:
    """(METHOD, path) for every real route, with Flask converters normalised.

    `/employees/<uuid:id>` -> `/employees/{id}` so it can be compared to OpenAPI.
    """
    import os
    import sys

    backend = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(backend))
    sys.path.insert(0, str(backend.parents[2] / "libs"))
    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

    from __init__ import create_app  # noqa: PLC0415

    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})

    ops: set[tuple[str, str]] = set()
    for rule in app.url_map.iter_rules():
        if rule.endpoint == "static":
            continue
        # <uuid:beacon_id> / <int:id> / <subdomain>  ->  {beacon_id} / {id} / {subdomain}
        path = re.sub(r"<(?:[^:<>]+:)?([^<>]+)>", r"{\1}", str(rule))
        for method in rule.methods or set():
            if method in HTTP_METHODS:
                ops.add((method, path))
    return ops


def _spec_operations() -> set[tuple[str, str]]:
    spec = yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8"))
    ops: set[tuple[str, str]] = set()
    for path, item in (spec.get("paths") or {}).items():
        if not isinstance(item, dict):
            continue
        for method in item:
            if method.upper() in HTTP_METHODS:
                ops.add((method.upper(), path))
    return ops


def test_spec_file_exists() -> None:
    assert SPEC_PATH.is_file(), f"spec not found at {SPEC_PATH}"


def test_every_route_is_documented() -> None:
    """Fails loudly when a route ships without a spec entry."""
    missing = sorted(_flask_operations() - _spec_operations() - UNDOCUMENTED_BY_DESIGN)
    assert not missing, "Routes missing from the OpenAPI spec:\n" + "\n".join(
        f"  {m:6} {p}" for m, p in missing
    )


def test_spec_documents_no_phantom_routes() -> None:
    """Fails when the spec promises an endpoint the server does not serve.

    This is the direction that burns integrators: `/organizations` was specced
    (as schemas) and consumed by the frontend while no handler existed, so the
    UI silently fell back to mock data.
    """
    phantom = sorted(_spec_operations() - _flask_operations())
    assert not phantom, "Spec documents routes the server does not serve:\n" + "\n".join(
        f"  {m:6} {p}" for m, p in phantom
    )


def test_roles_match_the_backend_vocabulary() -> None:
    """The spec's RoleKey enum must match the roles the backend actually accepts."""
    shared = SPEC_PATH.parent / "shared" / "primitives.yaml"
    doc = yaml.safe_load(shared.read_text(encoding="utf-8"))
    spec_roles = set(doc["components"]["schemas"]["RoleKey"]["enum"])

    seeds = (SPEC_PATH.parents[2] / "apps" / "intranet" / "backend" / "auth_routes.py").read_text(
        encoding="utf-8"
    )
    # seed_roles() lists the canonical roles the backend provisions per tenant.
    seeded = set(re.findall(r"[\"']([a-z_]+)[\"']", seeds.split("def seed_roles")[1][:800]))
    known = seeded & {
        "staff", "company_admin", "hr_admin", "department_manager", "school_admin",
        "lecturer", "teacher", "guardian", "super_admin", "it_admin",
    }
    assert known <= spec_roles, f"backend seeds roles absent from the spec: {sorted(known - spec_roles)}"
