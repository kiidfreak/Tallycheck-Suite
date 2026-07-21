"""Platform (cross-tenant) authorization and schema switching.

This is the ONLY sanctioned way for a request to read a tenant schema other than
the one the middleware pinned. It exists for platform super-admins operating
across every tenant (cross-org dashboards, per-org drill-down).

Two deliberate, security-sensitive decisions live here:

1. The super-admin gate trusts the **verified Auth0 claim**, not a database row.
   A cross-tenant actor has no dependable Employee row in whatever schema the JWT
   happened to pin — `roles_required` would raise EmployeeNotFoundError before it
   could even check the role. The Auth0 claim is issued independently of any
   schema, so it is the only source that works before a schema is chosen.
   Consequence: platform authority is governed by Auth0 RBAC, out-of-band. This
   is intentional and warrants security review.

2. `tenant_scope` resets the search_path in a `finally`. `SET search_path` is
   connection-scoped and sticky on pooled connections, so a missed reset would
   leak the next request into the wrong tenant. Mirrors jobs/reminder_job.py.
"""

from __future__ import annotations

from contextlib import contextmanager
from functools import wraps
from typing import Any, Callable, Iterator, TypeVar, cast

from flask import request

from models import db
from py_errors import ForbiddenError
from utils.tenant_middleware import SCHEMA_NAME_RE
from .auth_helper import require_auth

F = TypeVar('F', bound=Callable[..., Any])

# Auth0 surfaces the platform role in one of two places depending on how the
# token was minted. Mirrors the detection already used at auth_routes.py:75-77.
_PLATFORM_ROLE = 'super_admin'
_ROLES_CLAIM = 'https://adept.api/roles'


def is_platform_super_admin(payload: dict[str, Any]) -> bool:
    """True when the verified token carries the platform super-admin role.

    Reads only the token — never the database — so it is valid before any tenant
    schema has been resolved.
    """
    permissions = payload.get('permissions') or []
    roles = payload.get(_ROLES_CLAIM) or []
    return _PLATFORM_ROLE in permissions or _PLATFORM_ROLE in roles


def super_admin_required(f: F) -> F:
    """Gate a route to platform super-admins.

    Deliberately does NOT look up an Employee: see the module docstring. Use this
    (not roles_required) for anything under /platform that crosses tenants.
    """
    @wraps(f)
    @require_auth
    def decorated(*args: Any, **kwargs: Any) -> Any:
        payload: dict[str, Any] = request.user_payload  # type: ignore[attr-defined]
        if not is_platform_super_admin(payload):
            raise ForbiddenError(message="Platform administrator access required.")
        return f(*args, **kwargs)

    return cast(F, decorated)


@contextmanager
def tenant_scope(schema_name: str) -> Iterator[None]:
    """Run a block against one tenant schema, then hand the connection back clean.

    Validates the schema name against the same allowlist the middleware uses
    (the name is interpolated into a SET statement), switches the search_path,
    and on exit ALWAYS restores it to `public` and rolls back — so a half-finished
    read cannot bleed into the next use of a pooled connection.

    Caller is expected to have resolved `schema_name` from public.organizations,
    so an invalid name here is a programming error, not user input.
    """
    if not SCHEMA_NAME_RE.fullmatch(schema_name or ""):
        raise ValueError(f"Refusing to switch to malformed schema name: {schema_name!r}")

    try:
        db.session.execute(db.text(f'SET search_path TO "{schema_name}", public'))
        yield
    finally:
        # Reset before rollback: the reset is the load-bearing safety step, and it
        # must run even if the block raised.
        db.session.execute(db.text("SET search_path TO public"))
        db.session.rollback()
