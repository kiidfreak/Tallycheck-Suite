from flask import current_app
from datetime import datetime, timedelta
from typing import Any, Optional
from flask import Blueprint, jsonify, request, Response
from models import AttendanceRecord, Employee, AuditLog, db
from auth_routes import require_auth, roles_required
from py_errors import (
    EmployeeNotFoundError,
    ForbiddenError,
    AlreadyClockedInError,
    NotClockedInError,
    NotFoundError,
    ValidationError
)
from py_success import SuccessResponse
from schemas import AttendanceSchema, AuditLogSchema
from helpers.attendance_helper import get_team_presence, get_attendance_streak

attendance_bp = Blueprint("attendance", __name__, url_prefix='/attendance')

@attendance_bp.post("/clock-in")
@require_auth
def clock_in():
    """Check in: start an attendance record for the employee."""
    employee = Employee.query.filter_by(auth0_id=request.user_payload.get("sub")).first()  # type: ignore[attr-defined]
    if not employee:
        raise EmployeeNotFoundError()
    
    if not employee.is_approved:
        raise ForbiddenError(message="Your account is not approved yet.")

    # Cutoff check: refuse clock-in past the shift cutoff (skipped during tests)
    cutoff_hour = employee.shift_cutoff_hour
    if not current_app.config.get("TESTING") and datetime.now().hour >= cutoff_hour:
        raise ForbiddenError(message=f"Check-in Cutoff Passed: It is past the {cutoff_hour}00 hrs daily check-in cutoff. Please contact HR to log your hours manually for today.")

    # Check if there is an active open shift
    open_record = AttendanceRecord.query.filter_by(
        employee_id=employee.id,
        clock_out=None
    ).first()

    if open_record:
        raise AlreadyClockedInError()

    now: datetime = datetime.utcnow()
    data: dict[str, Any] = request.get_json(silent=True) or {}
    
    record = AttendanceRecord(
        employee_id=employee.id,
        clock_in=now,
        work_date=now.date(),
        source=data.get("source", "web"),
        status="open",
        notes=data.get("notes")
    )
    
    db.session.add(record)
    db.session.commit()

    return SuccessResponse(
        message="Checked in successfully.",
        data={"record": AttendanceSchema.serialize(record)},
        status_code=201
    ).write_response()


@attendance_bp.post("/clock-out")
@require_auth
def clock_out():
    """Check out: end the active open attendance record for the employee."""
    employee = Employee.query.filter_by(auth0_id=request.user_payload.get("sub")).first()  # type: ignore[attr-defined]
    if not employee:
        raise EmployeeNotFoundError()

    if not employee.is_approved:
        raise ForbiddenError(message="Your account is not approved yet.")

    open_record = AttendanceRecord.query.filter_by(
        employee_id=employee.id,
        clock_out=None
    ).first()

    if not open_record:
        raise NotClockedInError()

    now: datetime = datetime.utcnow()
    data: dict[str, Any] = request.get_json(silent=True) or {}
    
    diff = now - open_record.clock_in
    if diff < timedelta(minutes=5):
        db.session.delete(open_record)
        db.session.commit()
        return SuccessResponse(
            message="Attendance does not count. Shift too short.",
            data={"record": None, "cancelled": True},
            status_code=200
        ).write_response()
    
    open_record.clock_out = now
    open_record.status = "closed"
    if data.get("notes"):
        open_record.notes = (open_record.notes or "") + "\n" + str(data.get("notes"))
        open_record.notes = open_record.notes.strip()
        
    db.session.commit()
    
    serialized: Optional[dict[str, Any]] = AttendanceSchema.serialize(open_record)
    worked_hours: float = (serialized.get("worked_hours") or 0.0) if serialized else 0.0
    return SuccessResponse(
        message=f"Checked out. Worked {worked_hours} hours.",
        data={"record": serialized},
        status_code=200
    ).write_response()


@attendance_bp.get("/me")
@require_auth
def me():
    """Fetch paginated attendance history for the authenticated employee."""
    employee = Employee.query.filter_by(auth0_id=request.user_payload.get("sub")).first()  # type: ignore[attr-defined]
    if not employee:
        raise EmployeeNotFoundError()

    if not employee.is_approved:
        raise ForbiddenError(message="Your account is not approved yet.")

    page: int = request.args.get("page", 1, type=int)
    per_page: int = request.args.get("per_page", 10, type=int)
    date_from: Optional[str] = request.args.get("date_from")
    date_to: Optional[str] = request.args.get("date_to")

    query = AttendanceRecord.query.filter_by(employee_id=employee.id)

    if date_from:
        try:
            start = datetime.strptime(date_from, "%Y-%m-%d")
            query = query.filter(AttendanceRecord.clock_in >= start)
        except ValueError:
            raise ValidationError(details="date_from must be YYYY-MM-DD")

    if date_to:
        try:
            end = datetime.strptime(date_to, "%Y-%m-%d")
            end = end.replace(hour=23, minute=59, second=59)
            query = query.filter(AttendanceRecord.clock_in <= end)
        except ValueError:
            raise ValidationError(details="date_to must be YYYY-MM-DD")

    query = query.order_by(AttendanceRecord.clock_in.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return SuccessResponse(
        message="Success",
        data=[AttendanceSchema.serialize(r) for r in pagination.items],
        meta={
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages
        },
        status_code=200
    ).write_response()

@attendance_bp.get("/stats")
@require_auth
def get_stats() -> tuple[Response, int]:
    """Fetch attendance stats for the authenticated employee."""
    employee = Employee.query.filter_by(auth0_id=request.user_payload.get("sub")).first()  # type: ignore[attr-defined]
    if not employee:
        raise EmployeeNotFoundError()

    if not employee.is_approved:
        raise ForbiddenError(message="Your account is not approved yet.")

    now: datetime = datetime.utcnow()
    # Monday of the current week (UTC)
    start_of_week: datetime = now - timedelta(days=now.weekday())
    start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)

    # Query only required fields (clock_in, clock_out) starting from start_of_week
    records = AttendanceRecord.query.with_entities(
        AttendanceRecord.clock_in,
        AttendanceRecord.clock_out
    ).filter(
        AttendanceRecord.employee_id == employee.id,
        AttendanceRecord.clock_in >= start_of_week
    ).all()

    total_hours: float = 0.0
    for r in records:
        if r.clock_in:
            end_time = r.clock_out if r.clock_out else now
            diff = end_time - r.clock_in
            total_hours += diff.total_seconds() / 3600.0

    team_present, team_total = get_team_presence(employee, db, Employee, AttendanceRecord)
    streak = get_attendance_streak(employee, db, AttendanceRecord)

    return SuccessResponse(
        message="Success",
        data={
            "hours_this_week": round(total_hours, 1),
            "team_total": team_total,
            "team_present": team_present,
            "streak": streak
        },
        status_code=200
    ).write_response()

# ==========================================================
# HR & Manager Attendance Management
# ==========================================================

@attendance_bp.get("")
@roles_required('hr', 'super_admin', 'manager')
def query_attendance():
    """Query attendance records for HR and Managers (with department lock for managers)"""
    page: int = request.args.get("page", 1, type=int)
    per_page: int = request.args.get("per_page", 20, type=int)
    date_from_str: Optional[str] = request.args.get("date_from")
    date_to_str: Optional[str] = request.args.get("date_to")
    employee_id: Optional[str] = request.args.get("employee_id")
    department_id: Optional[int] = request.args.get("department_id", type=int)
    date_str: Optional[str] = request.args.get("date")

    # Enforce department scope if the user is a manager
    current_user = Employee.query.filter_by(auth0_id=request.user_payload.get("sub")).first()  # type: ignore[attr-defined]
    if not current_user:
        raise EmployeeNotFoundError()

    if current_user.role.name == 'manager':
        department_id = current_user.department_id

    query = AttendanceRecord.query

    if date_from_str:
        try:
            date_from = datetime.strptime(date_from_str, "%Y-%m-%d")
            query = query.filter(AttendanceRecord.clock_in >= date_from)
        except ValueError:
            raise ValidationError(details="date_from must be YYYY-MM-DD")

    if date_to_str:
        try:
            date_to = datetime.strptime(date_to_str, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
            query = query.filter(AttendanceRecord.clock_in <= date_to)
        except ValueError:
            raise ValidationError(details="date_to must be YYYY-MM-DD")

    if date_str:
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            query = query.filter(AttendanceRecord.work_date == target_date)
        except ValueError:
            raise ValidationError(details="date must be YYYY-MM-DD")

    if employee_id:
        query = query.filter_by(employee_id=employee_id)

    if department_id:
        query = query.join(Employee, AttendanceRecord.employee_id == Employee.id).filter(Employee.department_id == department_id)

    query = query.order_by(AttendanceRecord.clock_in.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return SuccessResponse(
        message="Success",
        data=[AttendanceSchema.serialize(r) for r in pagination.items],
        meta={
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages
        },
        status_code=200
    ).write_response()


@attendance_bp.post("")
@roles_required('hr', 'super_admin')
def create_attendance():
    """Manually create an attendance record (HR only)."""
    data: dict[str, Any] = request.get_json(silent=True) or {}

    employee_id: Optional[str] = data.get("employee_id")
    clock_in_str: Optional[str] = data.get("clock_in")
    clock_out_str: Optional[str] = data.get("clock_out")
    notes: Optional[str] = data.get("notes")
    source: str = data.get("source", "manual")

    if not employee_id or not clock_in_str:
        raise ValidationError(details="employee_id and clock_in are required.")

    employee = Employee.query.filter_by(id=employee_id).first()
    if not employee:
        raise EmployeeNotFoundError()

    try:
        clock_in: datetime = datetime.strptime(clock_in_str, "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        raise ValidationError(details="clock_in must be ISO format: YYYY-MM-DDTHH:MM:SS")

    clock_out: Optional[datetime] = None
    if clock_out_str:
        try:
            clock_out = datetime.strptime(clock_out_str, "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            raise ValidationError(details="clock_out must be ISO format: YYYY-MM-DDTHH:MM:SS")

    status: str = "corrected"

    record = AttendanceRecord(
        employee_id=employee.id,
        clock_in=clock_in,
        clock_out=clock_out,
        work_date=clock_in.date(),
        source=source,
        status=status,
        notes=notes
    )

    db.session.add(record)
    db.session.flush() # to populate record.id

    hr_employee = Employee.query.filter_by(auth0_id=request.user_payload.get("sub")).first()  # type: ignore[attr-defined]
    if hr_employee:
        record.edited_by = hr_employee.id
        audit_log = AuditLog(
            changed_by=hr_employee.id,
            record_changed=record.id,
            previous_clock_in=None,
            previous_clock_out=None,
            reason_for_change=f"Manual entry by HR ({hr_employee.email})"
        )
        db.session.add(audit_log)

    db.session.commit()

    return SuccessResponse(
        message="Attendance record created.",
        data={"record": AttendanceSchema.serialize(record)},
        status_code=201
    ).write_response()

@attendance_bp.put("/<int:id>")
@roles_required('hr', 'super_admin')
def update_attendance(id: int):
    """Edit an existing attendance record (HR only)."""
    record = AttendanceRecord.query.filter_by(id=id).first()
    if not record:
        raise NotFoundError(message="Attendance record not found.")

    data: dict[str, Any] = request.get_json(silent=True) or {}
    reason: Optional[str] = data.get("reason")

    if not reason:
        raise ValidationError(details="reason is required.")
    
    hr_employee = Employee.query.filter_by(auth0_id=request.user_payload.get("sub")).first()  # type: ignore[attr-defined]
    if not hr_employee:
        raise EmployeeNotFoundError()

    # Save previous values for audit log
    prev_clock_in = record.clock_in
    prev_clock_out = record.clock_out

    clock_in_str: Optional[str] = data.get("clock_in")
    clock_out_str: Optional[str] = data.get("clock_out")

    if clock_in_str:
        try:
            record.clock_in = datetime.strptime(clock_in_str, "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            raise ValidationError(details="clock_in must be ISO format: YYYY-MM-DDTHH:MM:SS")

    if clock_out_str:
        try:
            record.clock_out = datetime.strptime(clock_out_str, "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            raise ValidationError(details="clock_out must be ISO format: YYYY-MM-DDTHH:MM:SS")

    if "notes" in data:
        record.notes = data["notes"]
        
    record.status = "corrected"
    record.edited_by = hr_employee.id

    audit_log = AuditLog(
        changed_by=hr_employee.id,
        record_changed=record.id,
        previous_clock_in=prev_clock_in,
        previous_clock_out=prev_clock_out,
        reason_for_change=reason
    )
    db.session.add(audit_log)
    db.session.commit()

    return SuccessResponse(
        message="Attendance record updated.",
        data={"record": AttendanceSchema.serialize(record)},
        status_code=200
    ).write_response()

@attendance_bp.get("/<int:id>/audit")
@roles_required('hr', 'super_admin')
def get_audit_trail(record_id: str):
    """Return the audit trail for a specific attendance record."""
    record = AttendanceRecord.query.filter_by(id=record_id).first()
    if not record:
        raise NotFoundError(message="Attendance record not found.")

    logs = AuditLog.query.filter_by(record_changed=record_id).order_by(AuditLog.changed_at.desc()).all()

    return SuccessResponse(
        message="Audit trail retrieved.",
        data=[AuditLogSchema.serialize(log) for log in logs],
        status_code=200
    ).write_response()
