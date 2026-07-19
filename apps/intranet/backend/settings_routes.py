from typing import Any, Optional, Tuple
from datetime import datetime, timezone
from flask import Blueprint, request, Response
from models import db, OrgSettings, Employee
from auth_routes import require_auth, roles_required, ADMIN_ROLES, MANAGER_ROLES
from py_errors import ValidationError, EmployeeNotFoundError, NotFoundError
from py_success import SuccessResponse

settings_bp: Blueprint = Blueprint('settings', __name__, url_prefix='/settings')


def _serialize(s: OrgSettings) -> dict[str, Any]:
    return {
        "checkin_cutoff_hours_after_start": s.checkin_cutoff_hours_after_start,
        "reminder_enabled": s.reminder_enabled,
        "reminder_minutes_before_cutoff": s.reminder_minutes_before_cutoff,
        "updated_at": s.updated_at.isoformat() if s.updated_at else None,
        "updated_by": str(s.updated_by) if s.updated_by else None,
    }


def _current_employee() -> Employee:
    employee = Employee.query.filter_by(auth0_id=request.user_payload.get('sub')).first()  # type: ignore[attr-defined]
    if not employee:
        raise EmployeeNotFoundError()
    return employee


@settings_bp.route('', methods=['GET'])
@require_auth
def get_settings() -> Tuple[Response, int]:
    """Read the tenant's attendance defaults.

    Readable by any authenticated user: employees need the cutoff to know when
    their own clock-in window closes. Writes are admin-only (see update_settings).
    """
    return SuccessResponse(
        message="Success",
        data=_serialize(OrgSettings.get()),
        status_code=200
    ).write_response()


@settings_bp.route('', methods=['PUT'])
@roles_required(*ADMIN_ROLES)
def update_settings() -> Tuple[Response, int]:
    """Update the tenant's attendance defaults. Admins only."""
    body: dict[str, Any] = request.get_json() or {}
    settings = OrgSettings.get()

    if 'checkin_cutoff_hours_after_start' in body:
        raw = body['checkin_cutoff_hours_after_start']
        if not isinstance(raw, int) or isinstance(raw, bool):
            raise ValidationError(details="checkin_cutoff_hours_after_start must be an integer.")
        # A shift is 10h long; a cutoff at or past the end of the day means the
        # window never closes, and a non-positive one closes it before it opens.
        if not 1 <= raw <= 10:
            raise ValidationError(
                details="checkin_cutoff_hours_after_start must be between 1 and 10 hours after shift start."
            )
        settings.checkin_cutoff_hours_after_start = raw

    if 'reminder_enabled' in body:
        raw = body['reminder_enabled']
        if not isinstance(raw, bool):
            raise ValidationError(details="reminder_enabled must be a boolean.")
        settings.reminder_enabled = raw

    if 'reminder_minutes_before_cutoff' in body:
        raw = body['reminder_minutes_before_cutoff']
        if not isinstance(raw, int) or isinstance(raw, bool):
            raise ValidationError(details="reminder_minutes_before_cutoff must be an integer.")
        if not 5 <= raw <= 240:
            raise ValidationError(details="reminder_minutes_before_cutoff must be between 5 and 240.")
        settings.reminder_minutes_before_cutoff = raw

    settings.updated_at = datetime.now(timezone.utc)
    settings.updated_by = _current_employee().id
    db.session.commit()

    return SuccessResponse(
        message="Settings updated successfully",
        data=_serialize(settings),
        status_code=200
    ).write_response()


@settings_bp.route('/employees/<uuid:employee_id>/cutoff', methods=['PUT'])
@roles_required(*MANAGER_ROLES)
def set_employee_cutoff(employee_id: str) -> Tuple[Response, int]:
    """Set or clear one employee's clock-in cutoff override.

    Manager-set only — an employee cannot extend their own window. Send
    `{"checkin_cutoff_hour": null}` to drop the override and fall back to the
    tenant default.
    """
    employee = db.session.get(Employee, employee_id)
    if not employee:
        raise NotFoundError(message="Employee not found.")

    body: dict[str, Any] = request.get_json() or {}
    if 'checkin_cutoff_hour' not in body:
        raise ValidationError(details="checkin_cutoff_hour is required (send null to clear the override).")

    raw: Optional[Any] = body['checkin_cutoff_hour']
    if raw is None:
        employee.checkin_cutoff_hour = None
    else:
        if not isinstance(raw, int) or isinstance(raw, bool):
            raise ValidationError(details="checkin_cutoff_hour must be an integer hour (0-23) or null.")
        if not 0 <= raw <= 23:
            raise ValidationError(details="checkin_cutoff_hour must be between 0 and 23.")
        employee.checkin_cutoff_hour = raw

    db.session.commit()

    return SuccessResponse(
        message="Employee clock-in cutoff updated.",
        data={
            "employee_id": str(employee.id),
            "checkin_cutoff_hour": employee.checkin_cutoff_hour,
            "effective_cutoff_hour": employee.shift_cutoff_hour,
            "using_tenant_default": employee.checkin_cutoff_hour is None,
        },
        status_code=200
    ).write_response()
