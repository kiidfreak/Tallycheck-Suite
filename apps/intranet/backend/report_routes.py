import csv
import io
from datetime import datetime, date, timedelta
from typing import Any, Optional, Tuple
from flask import Blueprint, request, Response
from sqlalchemy import func
from models import db, Employee, Department, AttendanceRecord
from auth_routes import require_auth, roles_required, ADMIN_ROLES
from py_errors import ValidationError, NotFoundError
from schemas.reports import ReportSchema
from helpers.report_queries import dashboard_kpis
from py_success import SuccessResponse

report_bp: Blueprint = Blueprint('reports', __name__, url_prefix='/reports')

# ==========================================================
# ENDPOINTS
# ==========================================================

@report_bp.route('/dashboard', methods=['GET'])
@require_auth
@roles_required(*ADMIN_ROLES)
def get_dashboard() -> tuple[Response, int]:
    """HR Dashboard KPIs for the current tenant.

    The query itself lives in helpers/report_queries.dashboard_kpis so the
    platform layer can run the identical logic against a switched schema.
    """
    return SuccessResponse(
        message="Dashboard data retrieved",
        data=dashboard_kpis(),
        status_code=200
    ).write_response()


@report_bp.route('/attendance/timeline', methods=['GET'])
@require_auth
@roles_required(*ADMIN_ROLES)
def get_timeline() -> Tuple[Response, int]:
    """Returns today's timeline for all employees."""
    date_str: Optional[str] = request.args.get('date')
    target_date: date
    if date_str:
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            raise ValidationError(details="date must be YYYY-MM-DD")
    else:
        target_date = date.today()

    # Filter out unassigned employees (super admins)
    employees: list[Employee] = Employee.query.filter(
        Employee.department_id.isnot(None)
    ).all()
    
    valid_emp_ids = [e.id for e in employees]
    records: list[AttendanceRecord] = AttendanceRecord.query.filter(
        AttendanceRecord.work_date == target_date,
        AttendanceRecord.employee_id.in_(valid_emp_ids)
    ).all() if valid_emp_ids else []

    # Group by employee
    records_by_emp: dict[Any, list[dict[str, Any]]] = {}
    for r in records:
        if r.employee_id not in records_by_emp:
            records_by_emp[r.employee_id] = []
        records_by_emp[r.employee_id].append({
            "clock_in": r.clock_in.isoformat() + "Z" if r.clock_in else None,
            "clock_out": r.clock_out.isoformat() + "Z" if r.clock_out else None,
            "status": r.status,
            "notes": r.notes
        })

    data: list[dict[str, Any]] = []
    for emp in employees:
        emp_records: list[dict[str, Any]] = records_by_emp.get(emp.id, [])
        data.append({
            "employee_id": str(emp.id),
            "first_name": emp.first_name,
            "last_name": emp.last_name,
            "initials": f"{emp.first_name[0]}{emp.last_name[0]}".upper() if emp.first_name and emp.last_name else "U",
            "department": emp.department.name if emp.department else "Unassigned",
            "records": emp_records
        })

    return SuccessResponse(
        message="Timeline retrieved",
        data={
            "data": data,
            "date": target_date.isoformat()
        },
        status_code=200
    ).write_response()


@report_bp.route('/attendance', methods=['GET'])
@require_auth
@roles_required(*ADMIN_ROLES)
def get_attendance_report() -> Response | Tuple[Response, int]:
    """Detailed employee attendance report with CSV export"""
    # 1. Parse Arguments
    date_from_str: Optional[str] = request.args.get('date_from')
    date_to_str: Optional[str] = request.args.get('date_to')
    department_id: Optional[int] = request.args.get('department_id', type=int)
    employee_id: Optional[str] = request.args.get('employee_id')
    export_format: str = request.args.get('format', 'json').lower()
    page: int = request.args.get('page', 1, type=int)
    per_page: int = request.args.get('per_page', 20, type=int)

    d_from: Optional[date] = None
    d_to: Optional[date] = None
    
    if date_from_str:
        try:
            d_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
        except ValueError:
            raise ValidationError(details="date_from must be YYYY-MM-DD")
            
    if date_to_str:
        try:
            d_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
        except ValueError:
            raise ValidationError(details="date_to must be YYYY-MM-DD")

    # Query Employees first so we don't miss absent employees
    emp_query = Employee.query.filter_by(is_active=True)
    if employee_id:
        emp_query = emp_query.filter_by(id=employee_id)
    if department_id:
        emp_query = emp_query.filter_by(department_id=department_id)
        
    employees: list[Employee] = emp_query.all()
    
    # Query Attendance Records
    att_query = AttendanceRecord.query
    if d_from:
        att_query = att_query.filter(AttendanceRecord.work_date >= d_from)
    if d_to:
        att_query = att_query.filter(AttendanceRecord.work_date <= d_to)
    if employee_id:
        att_query = att_query.filter_by(employee_id=employee_id)
    if department_id:
        att_query = att_query.join(Employee, AttendanceRecord.employee_id == Employee.id).filter(Employee.department_id == department_id)
        
    records: list[AttendanceRecord] = att_query.all()

    grouped: dict[Any, list[AttendanceRecord]] = {}
    for r in records:
        if r.employee_id not in grouped:
            grouped[r.employee_id] = []
        grouped[r.employee_id].append(r)

    # Aggregate
    serialized_data: list[dict[str, Any]] = []
    for emp in employees:
        emp_records: list[AttendanceRecord] = grouped.get(emp.id, [])
        serialized_data.append(ReportSchema.serialize_employee_attendance(emp, emp_records, d_from, d_to))

    #  Handle CSV Export
    if export_format == 'csv':
        output: io.StringIO = io.StringIO()
        if not serialized_data:
            return Response("No data available", mimetype="text/csv")
            
        writer: csv.DictWriter = csv.DictWriter(output, fieldnames=serialized_data[0].keys())
        writer.writeheader()
        writer.writerows(serialized_data)
        
        today_str: str = date.today().strftime('%Y-%m-%d')
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment; filename=attendance_report_{today_str}.csv"}
        )

    # Handle JSON Pagination
    start: int = (page - 1) * per_page
    end: int = start + per_page
    paginated_data: list[dict[str, Any]] = serialized_data[start:end]

    total_items: int = len(serialized_data)
    total_pages: int = (total_items + per_page - 1) // per_page

    return SuccessResponse(
        message="Attendance report generated",
        data=paginated_data,
        meta={
            "page": page,
            "per_page": per_page,
            "total": total_items,
            "pages": total_pages
        },
        status_code=200
    ).write_response()


@report_bp.route('/attendance/trends', methods=['GET'])
@require_auth
@roles_required(*ADMIN_ROLES)
def get_attendance_trends() -> Tuple[Response, int]:
    """Returns daily total hours worked for the trend chart."""
    date_from_str: Optional[str] = request.args.get('date_from')
    date_to_str: Optional[str] = request.args.get('date_to')
    
    department_id_str: Optional[str] = request.args.get('department_id')
    
    today = date.today()
    d_to = today
    d_from = today - timedelta(days=7)
    
    if date_from_str:
        try:
            d_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    if date_to_str:
        try:
            d_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
        except ValueError:
            pass
            
    att_query = AttendanceRecord.query.filter(
        AttendanceRecord.work_date >= d_from,
        AttendanceRecord.work_date <= d_to
    )
    
    if department_id_str:
        try:
            dept_id = int(department_id_str)
            att_query = att_query.join(Employee, AttendanceRecord.employee_id == Employee.id)\
                                 .filter(Employee.department_id == dept_id)
        except ValueError:
            pass
            
    records = att_query.all()
    
    # Group by work_date
    daily_hours: dict[date, float] = {}
    current = d_from
    while current <= d_to:
        daily_hours[current] = 0.0
        current += timedelta(days=1)
        
    for r in records:
        if r.clock_in and r.clock_out:
            duration = r.clock_out - r.clock_in
            hours = duration.total_seconds() / 3600.0
            if r.work_date in daily_hours:
                daily_hours[r.work_date] += hours
            
    data = [
        {
            "date": d.isoformat(),
            "total_hours": round(hours, 2)
        }
        for d, hours in sorted(daily_hours.items())
    ]
    
    return SuccessResponse(
        message="Trends retrieved",
        data=data,
        status_code=200
    ).write_response()


@report_bp.route('/attendance/departments', methods=['GET'])
@require_auth
@roles_required(*ADMIN_ROLES)
def get_department_report() -> Tuple[Response, int]:
    """Department level aggregations"""
    date_from_str: Optional[str] = request.args.get('date_from')
    date_to_str: Optional[str] = request.args.get('date_to')

    d_from: Optional[date] = None
    d_to: Optional[date] = None
    if date_from_str:
        try:
            d_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
        except ValueError:
            raise ValidationError(details="date_from must be YYYY-MM-DD")
    if date_to_str:
        try:
            d_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
        except ValueError:
            raise ValidationError(details="date_to must be YYYY-MM-DD")

    departments: list[Department] = Department.query.all()
    
    data: list[dict[str, Any]] = []
    for dept in departments:
        emp_ids: list[Any] = [e.id for e in dept.employees if e.is_active]
        if not emp_ids:
            data.append(ReportSchema.serialize_department_attendance(dept, [], d_from, d_to))
            continue
            
        query = AttendanceRecord.query.filter(AttendanceRecord.employee_id.in_(emp_ids))
        if d_from:
            query = query.filter(AttendanceRecord.work_date >= d_from)
        if d_to:
            query = query.filter(AttendanceRecord.work_date <= d_to)
            
        records: list[AttendanceRecord] = query.all()
        data.append(ReportSchema.serialize_department_attendance(dept, records, d_from, d_to))
        
    return SuccessResponse(
        message="Department reports generated",
        data=data,
        status_code=200
    ).write_response()


@report_bp.route('/attendance/departments/<int:id>', methods=['GET'])
@require_auth
@roles_required(*ADMIN_ROLES)
def get_single_department_report(id: int) -> Tuple[Response, int]:
    date_from_str: Optional[str] = request.args.get('date_from')
    date_to_str: Optional[str] = request.args.get('date_to')

    d_from: Optional[date] = None
    d_to: Optional[date] = None
    if date_from_str:
        try:
            d_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
        except ValueError:
            raise ValidationError(details="date_from must be YYYY-MM-DD")
    if date_to_str:
        try:
            d_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
        except ValueError:
            raise ValidationError(details="date_to must be YYYY-MM-DD")

    dept = Department.query.get(id)
    if not dept:
        raise NotFoundError(message="Department not found")
        
    emp_ids: list[Any] = [e.id for e in dept.employees if e.is_active]
    records: list[AttendanceRecord] = []
    if emp_ids:
        query = AttendanceRecord.query.filter(AttendanceRecord.employee_id.in_(emp_ids))
        if d_from:
            query = query.filter(AttendanceRecord.work_date >= d_from)
        if d_to:
            query = query.filter(AttendanceRecord.work_date <= d_to)
        records = query.all()
        
    return SuccessResponse(
        message="Department report generated",
        data=ReportSchema.serialize_department_attendance(dept, records, d_from, d_to),
        status_code=200
    ).write_response()
