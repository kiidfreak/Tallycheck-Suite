from typing import Any, Callable, Optional, Tuple, cast
from flask import Blueprint, request, jsonify, Response
import os
import sys
import requests
from models import db, Employee, Role, Department
from utils.shift_data import *
from functools import wraps

from py_auth import verify_jwt
from py_errors import (
    UnauthorizedError,
    ForbiddenError,
    EmployeeNotFoundError,
    ValidationError,
    NotFoundError,
)
from py_success import SuccessResponse
from schemas import EmployeeSchema, RoleSchema, DepartmentSchema
from helpers.employees_helper import _validate_shift_fields
from utils.shift_data import *
from helpers.auth_helper import *

auth_bp: Blueprint = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['POST'])
@require_auth
def register() -> Tuple[Response, int]:
    """Receives Auth0 token, links or creates employee record."""
    payload: dict[str, Any] = request.user_payload  # type: ignore[attr-defined]
    auth0_id: str = payload.get('sub', '')
    
    # Extract data from the body if provided
    data: dict[str, Any] = request.json or {}
    email: Optional[str] = data.get('email') or payload.get('email')
    
    # --- HYBRID SUPER ADMIN BYPASS HELPER ---
    auth0_permissions: list[str] = payload.get('permissions', [])
    auth0_roles: list[str] = payload.get('https://adept.api/roles', [])
    is_super_admin: bool = "super_admin" in auth0_permissions or "super_admin" in auth0_roles
    # ----------------------------------------

    # Check if they are already fully registered
    existing_employee = Employee.query.filter_by(auth0_id=auth0_id).first()
    if existing_employee:
        return SuccessResponse(
            message="Employee already exists", 
            data=EmployeeSchema.serialize(existing_employee), 
            status_code=200
        ).write_response()

    # LAZY LINKING: Check if HR pre-created their profile
    if email and "@placeholder.com" not in email:
        hr_pre_approved_employee = Employee.query.filter_by(email=email).first()
        if hr_pre_approved_employee:
            hr_pre_approved_employee.auth0_id = auth0_id
            db.session.commit()
            return SuccessResponse(
                message="Account lazily linked to HR profile successfully",
                data=EmployeeSchema.serialize(hr_pre_approved_employee),
                status_code=200
            ).write_response()

    # Otherwise, they are a brand new unapproved user
    final_email: str = email or f"{auth0_id}@placeholder.com"
    
    assigned_role_id: Optional[int] = None
    is_approved_flag: bool = False
    
    # HYBRID SUPER ADMIN BYPASS
    if is_super_admin:
        super_admin_role = Role.query.filter_by(name='super_admin').first()
        if super_admin_role:
            assigned_role_id = super_admin_role.id
            is_approved_flag = True
    
    # Validate shift fields before creating the employee
    _validate_shift_fields(data)

    new_employee = Employee(
        auth0_id=auth0_id,
        email=final_email,
        first_name=data.get('first_name', 'Unknown'),
        last_name=data.get('last_name', 'Unknown'),
        shift_type=data.get('shift_type', ShiftType.STD.value),
        shift_hours=data.get('shift_hours', ShiftHours.EARLY_MORN.value),
        custom_shift_start=data.get('custom_shift_start'),
        custom_shift_end=data.get('custom_shift_end'),
        role_id=assigned_role_id,
        department_id=None,
        is_approved=is_approved_flag,
        is_active=is_approved_flag
    )
    
    db.session.add(new_employee)
    db.session.commit()
    
    return SuccessResponse(
        message="Employee successfully registered and awaiting approval",
        data=EmployeeSchema.serialize(new_employee),
        status_code=201
    ).write_response()

@auth_bp.route('/login', methods=['POST'])
@require_auth
def login() -> Tuple[Response, int]:
    """Looks up employee in database and checks Admin approval status."""
    payload: dict[str, Any] = request.user_payload  # type: ignore[attr-defined]
    auth0_id: str = payload.get('sub', '')
    
    employee = Employee.query.filter_by(auth0_id=auth0_id).first()
    if not employee:
        raise EmployeeNotFoundError(details="No account found. Please register first.")
        
    if not employee.is_approved:
        raise ForbiddenError(message="Your account is pending administrator approval.")

    return SuccessResponse(
        message="Login successful",
        data={
            "employee": EmployeeSchema.serialize(employee)
        },
        status_code=200
    ).write_response()

@auth_bp.route('/me', methods=['GET'])
@require_auth
def get_me() -> Tuple[Response, int]:
    """Returns current employee record + role."""
    payload: dict[str, Any] = request.user_payload  # type: ignore[attr-defined]
    auth0_id: str = payload.get('sub', '')
    
    employee = Employee.query.filter_by(auth0_id=auth0_id).first()
    if not employee:
        raise NotFoundError(message="No employee record found for this user.")
        
    return SuccessResponse(
        message="Success",
        data=EmployeeSchema.serialize(employee),
        status_code=200
    ).write_response()

# --- ADMIN ENDPOINTS ---

@auth_bp.route('/metadata', methods=['GET'])
@roles_required('super_admin', 'hr')
def get_metadata() -> Tuple[Response, int]:
    """Admin only: Fetch all roles and departments for dropdowns."""
    roles = Role.query.all()
    departments = Department.query.all()
    return SuccessResponse(
        message="Success",
        data={
            "roles": [RoleSchema.serialize(r) for r in roles],
            "departments": [DepartmentSchema.serialize(d) for d in departments]
        },
        status_code=200
    ).write_response()

@auth_bp.route('/users/pending', methods=['GET'])
@roles_required('super_admin', 'hr')
def get_pending_users() -> Tuple[Response, int]:
    """Admin only: Fetch all users awaiting approval."""
    pending = Employee.query.filter_by(is_approved=False).all()
    
    return SuccessResponse(
        message="Success",
        data=[EmployeeSchema.serialize(emp) for emp in pending],
        status_code=200
    ).write_response()

@auth_bp.route('/users/<uuid:user_id>/approve', methods=['POST'])
@roles_required('super_admin', 'hr')
def approve_user(user_id: str) -> Tuple[Response, int]:
    """Admin only: Approves a pending user and assigns their role/dept."""
    employee = db.session.get(Employee, user_id)
    if not employee:
        raise EmployeeNotFoundError()
        
    data: dict[str, Any] = request.json or {}
    role_id: Optional[int] = data.get('role_id')
    department_id: Optional[int] = data.get('department_id')
    is_internal: Optional[bool] = data.get('is_internal')

    if not role_id:
        raise ValidationError(details="role_id is required for approval.")
        
    role = Role.query.get(role_id)
    if not role:
        raise ValidationError(details="Role not found.")
        
    if role.name == 'super_admin':
        current_employee = Employee.query.filter_by(auth0_id=request.user_payload.get('sub')).first()  # type: ignore[attr-defined]
        if not current_employee or not current_employee.role or current_employee.role.name != 'super_admin':
            raise ForbiddenError(message="Only a super admin can approve another super admin.")

    employee.role_id = role_id
    if department_id:
        employee.department_id = department_id
    if is_internal is not None:
        employee.is_internal = is_internal
        
    employee.is_approved = True
    employee.is_active = True
    db.session.commit()
    
    return SuccessResponse(
        message=f"Employee {employee.first_name} successfully approved!",
        data={"message": f"Employee {employee.first_name} successfully approved!"},
        status_code=200
    ).write_response()


def seed_roles_and_departments() -> None:
    role_names: list[str] = ['staff', 'hr', 'manager', 'super_admin', 'call_centre_agent', 'call_centre_admin']
    for name in role_names:
        if not Role.query.filter_by(name=name).first():
            db.session.add(Role(role=name))
    
    """
    Adept has 5 departments, Sales (Antony), Marketing (Currently no manager), Operations & Projects (William), Finance (Francis), 
    HR (Kevina) and IT (Protus). All of them report to Mercy. Francis, Kevina and Protus are all contractors, not internal staff.

    Operations has 5 sub-departments: Contact center (Caroline), Business Efficiency (Kelvin), Cloud & Automation (Fuji), 
    S/ware Eng (Clinton) and AI (Teresia). All of them report to William.
    """
    dept_names: list[str] = ['sales', 'marketing', 'operations', 'finance', 'hr', 'it', 'contact_center', 
        'business_efficiency', 'software_development', 'cloud_and_automation', 'artificial_intelligence']
    for name in dept_names:
        if not Department.query.filter_by(name=name).first():
            db.session.add(Department(name=name))
    db.session.commit()


def sync_internal() -> Tuple[Response, int]:
    seed_roles_and_departments()
    
    payload: dict[str, Any] = request.user_payload  # type: ignore[attr-defined]
    sub: str = payload.get("sub", "")
    email: Optional[str] = payload.get("email")

    # --- HYBRID SUPER ADMIN BYPASS HELPER ---
    auth0_permissions: list[str] = payload.get('permissions', [])
    auth0_roles: list[str] = payload.get('https://adept.api/roles', [])
    is_super_admin: bool = "super_admin" in auth0_permissions or "super_admin" in auth0_roles
    # ----------------------------------------

    assigned_role_id: Optional[int] = None
    is_approved_flag: bool = False
    
    if is_super_admin:
        super_admin_role = Role.query.filter_by(name='super_admin').first()
        if super_admin_role:
            assigned_role_id = super_admin_role.id
            is_approved_flag = True

    employee = Employee.query.filter_by(auth0_id=sub).first()
    if employee is None:
        employee = Employee(
            auth0_id=sub,
            email=email or f"{sub}@unknown",
            first_name=payload.get("given_name", ""),
            last_name=payload.get("family_name", ""),
            avatar=payload.get("picture"),
            is_approved=is_approved_flag,
            role_id=assigned_role_id,
            is_active=is_approved_flag
        )
        db.session.add(employee)
    else:
        employee.email = email or employee.email
        employee.avatar = payload.get("picture", employee.avatar)
        if is_super_admin and not employee.is_approved:
            employee.is_approved = True
            employee.is_active = True
            if assigned_role_id:
                employee.role_id = assigned_role_id
        
    db.session.commit()
    return SuccessResponse(
        message="Success",
        data=EmployeeSchema.serialize(employee),
        status_code=200
    ).write_response()


@auth_bp.post("/sync")
@require_auth
def sync() -> Tuple[Response, int]:
    """Upsert the employee from the token's claims on first sign-in.

    New employees are created unapproved (`is_approved=False`) pending review.
    If the user has a super_admin role in auth0, they are automatically approved.
    """
    return sync_internal()
