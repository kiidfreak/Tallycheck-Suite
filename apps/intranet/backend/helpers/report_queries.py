"""Schema-agnostic report queries.

Every function here assumes the caller has already set the search_path to the
target tenant schema — it queries the unqualified ORM models and does no schema
switching of its own. That is what lets BOTH the tenant `/reports/*` handlers
(schema pinned by the middleware) and the platform `/platform/*` handlers
(schema switched via `tenant_scope`) share one implementation instead of two.

Keep these free of `request`, `g`, and Flask response objects — they are pure
data functions so the platform layer can call them in a loop across tenants.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from models import Employee, AttendanceRecord


def dashboard_kpis() -> dict[str, Any]:
    """Headline attendance KPIs for the CURRENTLY active tenant schema, today.

    Lifted verbatim from the old get_dashboard handler so behaviour is identical;
    the handler now just wraps this in an envelope.
    """
    today: date = date.today()

    total_headcount: int = Employee.query.filter(
        Employee.is_active.is_(True),
        Employee.department_id.isnot(None),
    ).count()

    today_records: list[AttendanceRecord] = (
        AttendanceRecord.query.join(Employee, AttendanceRecord.employee_id == Employee.id)
        .filter(
            AttendanceRecord.work_date == today,
            Employee.is_active.is_(True),
            Employee.department_id.isnot(None),
        )
        .all()
    )

    present_today: int = len({r.employee_id for r in today_records})
    currently_clocked_in: int = sum(1 for r in today_records if r.clock_out is None)
    absent_today: int = total_headcount - present_today if total_headcount > present_today else 0

    attendance_rate: float = 0.0
    if total_headcount > 0:
        attendance_rate = round((present_today / total_headcount) * 100, 2)

    late_arrivals: int = 0
    remote_today: int = 0
    for r in today_records:
        if r.clock_in and r.clock_in.hour >= 8 and r.clock_in.minute > 0:
            late_arrivals += 1
        if r.source == 'remote' or (r.notes and '[Remote]' in r.notes):
            remote_today += 1

    pending_corrections: int = Employee.query.filter_by(is_approved=False).count()

    return {
        "total_headcount": total_headcount,
        "present_today": present_today,
        "absent_today": absent_today,
        "currently_clocked_in": currently_clocked_in,
        "attendance_rate_today": attendance_rate,
        "late_arrivals": late_arrivals,
        "remote_today": remote_today,
        "pending_corrections": pending_corrections,
    }
