from typing import Any, Optional, Tuple
from flask import Blueprint, request, Response
from sqlalchemy import or_, func
from models import db, Employee, Department, Role
from utils.shift_data import ShiftType, ShiftHours
from auth_routes import require_auth, roles_required
from py_errors import NotFoundError, ValidationError, EmailExistsError, ForbiddenError
from py_success import SuccessResponse
from schemas.employees import EmployeeSchema
from helpers.employees_helper import _validate_shift_fields

employee_bp: Blueprint = Blueprint('employees', __name__, url_prefix='/employees')

@employee_bp.route('', methods=['GET'])
@require_auth
@roles_required('hr', 'super_admin')
def list_employees() -> Tuple[Response, int]:
    page: int = request.args.get('page', 1, type=int)
    per_page: int = request.args.get('per_page', 20, type=int)
    
    query = Employee.query

    # Filters
    search: Optional[str] = request.args.get('search')
    if search:
        search_term: str = f"%{search}%"
        search_term_no_spaces: str = f"%{search.replace(' ', '')}%"
        query = query.filter(or_(
            Employee.first_name.ilike(search_term),
            Employee.last_name.ilike(search_term),
            Employee.email.ilike(search_term),
            func.concat(Employee.first_name, ' ', Employee.last_name).ilike(search_term),
            func.concat(Employee.first_name, Employee.last_name).ilike(search_term_no_spaces)
        ))

    department_id: Optional[str] = request.args.get('department_id')
    if department_id:
        query = query.filter_by(department_id=int(department_id))

    department_name: Optional[str] = request.args.get('department_name')
    if department_name:
        normalized_dept: str = f"%{department_name.replace(' ', '%').replace('-', '%')}%"
        query = query.join(Department).filter(Department.name.ilike(normalized_dept))

    is_active_arg: Optional[str] = request.args.get('is_active')
    if is_active_arg is not None:
        query = query.filter_by(is_active=is_active_arg.lower() == 'true')

    is_approved_arg: Optional[str] = request.args.get('is_approved')
    if is_approved_arg is not None:
        query = query.filter_by(is_approved=is_approved_arg.lower() == 'true')
    else:
        query = query.filter_by(is_approved=True)

    role_name: Optional[str] = request.args.get('role')
    if role_name:
        normalized_role: str = f"%{role_name.replace(' ', '%').replace('-', '%')}%"
        query = query.join(Role).filter(Role.name.ilike(normalized_role))

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    data: list[dict[str, Any]] = [EmployeeSchema.serialize(emp) for emp in pagination.items]  # type: ignore[misc]
    
    return SuccessResponse(
        message="Success",
        data={
            "data": data,
            "meta": {
                "page": pagination.page,
                "per_page": pagination.per_page,
                "total": pagination.total,
                "pages": pagination.pages
            }
        },
        status_code=200
    ).write_response()

@employee_bp.route('', methods=['POST'])
@require_auth
@roles_required('hr', 'super_admin')
def create_employee() -> Tuple[Response, int]:
    body: dict[str, Any] = request.get_json() or {}
    email: Optional[str] = body.get('email')
    first_name: Optional[str] = body.get('first_name')
    last_name: Optional[str] = body.get('last_name')
    
    if not email or not first_name or not last_name:
        raise ValidationError(details="email, first_name, and last_name are required.")

    if Employee.query.filter_by(email=email).first():
        raise EmailExistsError()

    auth0_id: str = body.get('auth0_id', f"auth0|{email}")

    _validate_shift_fields(body)

    new_emp = Employee(
        auth0_id=auth0_id,
        email=email,
        first_name=first_name,
        last_name=last_name,
        is_approved=body.get('is_approved', True),
        is_active=True,
        is_internal=body.get('is_internal', True),
        shift_type=body.get('shift_type', 'standard'),
        shift_hours=body.get('shift_hours', '7am-5pm'),
        custom_shift_start=body.get('custom_shift_start'),
        custom_shift_end=body.get('custom_shift_end'),
        hire_date=body.get('hire_date'),
    )

    role_id: Optional[int] = body.get('role_id')
    if role_id:
        role = Role.query.get(role_id)
        if not role:
            raise ValidationError(details="Role not found.")
            
        if role.name == 'super_admin':
            current_employee = Employee.query.filter_by(auth0_id=request.user_payload.get('sub')).first()  # type: ignore[attr-defined]
            if not current_employee or not current_employee.role or current_employee.role.name != 'super_admin':
                raise ForbiddenError(message="Only a super admin can create another super admin.")
                
        new_emp.role_id = role_id

    department_id: Optional[int] = body.get('department_id')
    if department_id:
        if not Department.query.get(department_id):
            raise ValidationError(details="Department not found.")
        new_emp.department_id = department_id

    db.session.add(new_emp)
    db.session.commit()

    return SuccessResponse(
        message="Employee created successfully",
        data=EmployeeSchema.serialize(new_emp),
        status_code=201
    ).write_response()

@employee_bp.route('/<uuid:id>', methods=['GET'])
@require_auth
@roles_required('hr', 'super_admin')
def get_employee(id: str) -> Tuple[Response, int]:
    emp = Employee.query.get(id)
    if not emp:
        raise NotFoundError(message="Employee not found.")
    return SuccessResponse(
        message="Success",
        data=EmployeeSchema.serialize(emp),
        status_code=200
    ).write_response()

@employee_bp.route('/<uuid:id>', methods=['PUT'])
@require_auth
@roles_required('hr', 'super_admin')
def update_employee(id: str) -> Tuple[Response, int]:
    emp = Employee.query.get(id)
    if not emp:
        raise NotFoundError(message="Employee not found.")

    body: dict[str, Any] = request.get_json() or {}

    if 'first_name' in body:
        emp.first_name = body['first_name']
    if 'last_name' in body:
        emp.last_name = body['last_name']
    if 'hire_date' in body:
        emp.hire_date = body['hire_date']
    if 'is_approved' in body:
        emp.is_approved = body['is_approved']
    if 'is_active' in body:
        emp.is_active = body['is_active']
    if 'is_internal' in body:
        emp.is_internal = body['is_internal']

    # Shift fields — validate together before applying any changes
    shift_keys = {'shift_type', 'shift_hours', 'custom_shift_start', 'custom_shift_end'}
    if shift_keys & set(body):
        _validate_shift_fields(body)
        if 'shift_type' in body:
            emp.shift_type = body['shift_type']
        if 'shift_hours' in body:
            emp.shift_hours = body['shift_hours']
            # Clear custom times when switching away from custom
            if body['shift_hours'] != 'custom':
                emp.custom_shift_start = None
                emp.custom_shift_end = None
        if 'custom_shift_start' in body:
            emp.custom_shift_start = body['custom_shift_start']
        if 'custom_shift_end' in body:
            emp.custom_shift_end = body['custom_shift_end']

    if 'role_id' in body:
        role_id: Optional[int] = body['role_id']
        if role_id is not None:
            role = Role.query.get(role_id)
            if not role:
                raise ValidationError(details="Role not found.")
                
            if role.name == 'super_admin':
                current_employee = Employee.query.filter_by(auth0_id=request.user_payload.get('sub')).first()  # type: ignore[attr-defined]
                if not current_employee or not current_employee.role or current_employee.role.name != 'super_admin':
                    raise ForbiddenError(message="Only a super admin can assign the super admin role.")
                    
            emp.role_id = role_id

    if 'department_id' in body:
        department_id: Optional[int] = body['department_id']
        if department_id is not None and not Department.query.get(department_id):
            raise ValidationError(details="Department not found.")
        emp.department_id = department_id

    db.session.commit()
    return SuccessResponse(
        message="Employee updated successfully",
        data=EmployeeSchema.serialize(emp),
        status_code=200
    ).write_response()

@employee_bp.route('/<uuid:id>/deactivate', methods=['POST'])
@require_auth
@roles_required('hr', 'super_admin')
def deactivate_employee(id: str) -> Tuple[Response, int]:
    emp = Employee.query.get(id)
    if not emp:
        raise NotFoundError(message="Employee not found.")
    
    emp.is_active = False
    db.session.commit()

    return SuccessResponse(
        message="Employee deactivated.",
        data=None,
        status_code=200
    ).write_response()

@employee_bp.route('/<uuid:id>/approve', methods=['POST'])
@require_auth
@roles_required('hr', 'super_admin')
def approve_employee(id: str) -> Tuple[Response, int]:
    emp = Employee.query.get(id)
    if not emp:
        raise NotFoundError(message="Employee not found.")
    
    emp.is_approved = True
    db.session.commit()

    return SuccessResponse(
        message="Employee approved.",
        data=None,
        status_code=200
    ).write_response()
