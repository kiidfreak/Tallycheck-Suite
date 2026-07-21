"""Cross-tenant platform surface for super-admins.

These are the ONLY request handlers that read tenant schemas other than the one
the middleware pinned. Each explicitly switches schema via `tenant_scope` — the
same connection-hygiene pattern jobs/reminder_job.py uses — and every endpoint
is gated by `super_admin_required` (verified Auth0 claim, not a DB row: see
helpers/platform_helper.py).

Organization registry rows live in `public.organizations`, which is always on the
search_path, so listing orgs needs no scope switch; only reading a tenant's
attendance data does.
"""

from typing import Any, Tuple

from flask import Blueprint, Response

from models import db, Organization
from helpers.platform_helper import super_admin_required, tenant_scope
from helpers.report_queries import dashboard_kpis
from py_errors import NotFoundError
from py_success import SuccessResponse

platform_bp: Blueprint = Blueprint('platform', __name__, url_prefix='/platform')


def _active_orgs() -> list[Organization]:
    # Registry lives in public, which is always on the path.
    db.session.execute(db.text("SET search_path TO public"))
    return Organization.query.filter_by(is_active=True).order_by(Organization.name).all()


def _org_summary(org: Organization) -> dict[str, Any]:
    return {
        "id": org.id,
        "name": org.name,
        "domain": org.domain,
        "org_type": org.org_type,
        "status": org.status,
        "is_active": org.is_active,
    }


@platform_bp.route('/summary', methods=['GET'])
@super_admin_required
def platform_summary() -> Tuple[Response, int]:
    """Platform-wide totals plus a per-org breakdown.

    Iterates active tenants, running the SAME dashboard query used by each
    tenant's own /reports/dashboard against that tenant's schema. Per-org numbers
    go in `meta` so the aggregate stays the primary payload.
    """
    orgs = _active_orgs()

    per_org: list[dict[str, Any]] = []
    totals = {
        "total_headcount": 0,
        "present_today": 0,
        "currently_clocked_in": 0,
        "absent_today": 0,
        "pending_corrections": 0,
    }

    for org in orgs:
        try:
            with tenant_scope(org.schema_name):
                kpis = dashboard_kpis()
        except Exception:
            # One malformed tenant must not sink the whole platform view.
            # tenant_scope already restored search_path + rolled back.
            per_org.append({**_org_summary(org), "error": "unavailable"})
            continue

        per_org.append({**_org_summary(org), "kpis": kpis})
        for key in totals:
            totals[key] += kpis.get(key, 0)

    active_org_count = len(orgs)
    attendance_rate = 0.0
    if totals["total_headcount"] > 0:
        attendance_rate = round((totals["present_today"] / totals["total_headcount"]) * 100, 2)

    return SuccessResponse(
        message="Platform summary retrieved",
        data={
            **totals,
            "attendance_rate_today": attendance_rate,
            "active_organizations": active_org_count,
        },
        meta={"organizations": per_org},
        status_code=200,
    ).write_response()


@platform_bp.route('/organizations', methods=['GET'])
@super_admin_required
def platform_organizations() -> Tuple[Response, int]:
    """Every organization plus a cheap headline (today's present/headcount)."""
    db.session.execute(db.text("SET search_path TO public"))
    orgs = Organization.query.order_by(Organization.name).all()

    data: list[dict[str, Any]] = []
    for org in orgs:
        row = _org_summary(org)
        if org.is_active:
            try:
                with tenant_scope(org.schema_name):
                    kpis = dashboard_kpis()
                row["headcount"] = kpis["total_headcount"]
                row["present_today"] = kpis["present_today"]
            except Exception:
                row["headcount"] = None
                row["present_today"] = None
        data.append(row)

    return SuccessResponse(message="Organizations retrieved", data=data, status_code=200).write_response()


def _resolve_org(org_id: str) -> Organization:
    db.session.execute(db.text("SET search_path TO public"))
    org = db.session.get(Organization, org_id)
    if not org:
        raise NotFoundError(message="Organization not found.")
    return org


@platform_bp.route('/organizations/<org_id>/dashboard', methods=['GET'])
@super_admin_required
def platform_org_dashboard(org_id: str) -> Tuple[Response, int]:
    """One organization's dashboard, as its own admins would see it.

    Reuses the tenant dashboard query against the org's switched schema — no
    duplication, no middleware override.
    """
    org = _resolve_org(org_id)
    with tenant_scope(org.schema_name):
        kpis = dashboard_kpis()

    return SuccessResponse(
        message="Organization dashboard retrieved",
        data={"organization": _org_summary(org), "kpis": kpis},
        status_code=200,
    ).write_response()
