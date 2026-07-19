from typing import Any, Optional, Tuple
from flask import Blueprint, request, Response
from models import db, Department, Employee
from auth_routes import require_auth, roles_required, ADMIN_ROLES
from py_errors import NotFoundError, DepartmentHasEmployeesError, ValidationError
from py_success import SuccessResponse
from schemas.departments import DepartmentSchema

department_bp: Blueprint = Blueprint('departments', __name__, url_prefix='/departments')

@department_bp.route('', methods=['GET'])
@require_auth
def list_departments() -> Tuple[Response, int]:
    departments = Department.query.all()
    return SuccessResponse(
        message="Success",
        data=[DepartmentSchema.serialize(d) for d in departments],
        status_code=200
    ).write_response()

@department_bp.route('', methods=['POST'])
@require_auth
@roles_required(*ADMIN_ROLES)
def create_department() -> Tuple[Response, int]:
    body: Optional[dict[str, Any]] = request.get_json()
    if not body or 'name' not in body or not str(body['name']).strip():
        raise ValidationError(details="Department name is required.")
        
    name: str = str(body['name']).strip().lower().replace(' ', '_')
    manager_id: Optional[str] = body.get('manager_id')
    parent_department_id: Optional[int] = body.get('parent_department_id')

    if Department.query.filter_by(name=name).first():
        raise ValidationError(details="A department with this name already exists.")

    new_dept = Department(name=name)

    if manager_id:
        manager = Employee.query.get(manager_id)
        if not manager:
            raise ValidationError(details="Manager not found.")
        new_dept.manager_id = manager.id
        # Automatically promote the employee to manager
        manager.is_manager = True

    if parent_department_id is not None:
        parent = Department.query.get(parent_department_id)
        if not parent:
            raise ValidationError(details="Parent department not found.")
        new_dept.parent_department_id = parent.id

    db.session.add(new_dept)
    db.session.commit()

    return SuccessResponse(
        message="Department created successfully",
        data=DepartmentSchema.serialize(new_dept),
        status_code=201
    ).write_response()

@department_bp.route('/<int:id>', methods=['PUT'])
@require_auth
@roles_required(*ADMIN_ROLES)
def update_department(id: int) -> Tuple[Response, int]:
    dept = Department.query.get(id)
    if not dept:
        raise NotFoundError(message="Department not found.")

    body: dict[str, Any] = request.get_json() or {}
    
    if 'name' in body:
        name: str = str(body['name']).strip().lower().replace(' ', '_')
        existing = Department.query.filter_by(name=name).first()
        if existing and existing.id != id:
            raise ValidationError(details="A department with this name already exists.")
        dept.name = name

    if 'manager_id' in body:
        new_manager_id: Optional[str] = body['manager_id']
        old_manager_id = dept.manager_id
        
        if new_manager_id is None:
            dept.manager_id = None
        else:
            new_manager = Employee.query.get(new_manager_id)
            if not new_manager:
                raise ValidationError(details="Manager not found.")
            dept.manager_id = new_manager.id
            # Automatically promote the new employee to manager
            new_manager.is_manager = True
            
        # Clean up the old manager's flag if they were replaced or removed
        if old_manager_id and str(old_manager_id) != str(new_manager_id):
            old_manager = Employee.query.get(old_manager_id)
            if old_manager:
                # Check if they still manage any other departments
                still_manages = Department.query.filter(Department.manager_id == old_manager.id, Department.id != dept.id).count()
                if still_manages == 0:
                    old_manager.is_manager = False

    if 'parent_department_id' in body:
        parent_id: Optional[int] = body['parent_department_id']
        if parent_id is None:
            dept.parent_department_id = None
        else:
            if parent_id == id:
                raise ValidationError(details="A department cannot be its own parent.")
            parent = Department.query.get(parent_id)
            if not parent:
                raise ValidationError(details="Parent department not found.")
            dept.parent_department_id = parent.id

    db.session.commit()

    return SuccessResponse(
        message="Department updated successfully",
        data=DepartmentSchema.serialize(dept),
        status_code=200
    ).write_response()

@department_bp.route('/<int:id>', methods=['DELETE'])
@require_auth
@roles_required(*ADMIN_ROLES)
def delete_department(id: int) -> Tuple[Response, int]:
    dept = Department.query.get(id)
    if not dept:
        raise NotFoundError(message="Department not found.")

    if Employee.query.filter_by(department_id=id).first():
        raise DepartmentHasEmployeesError()

    db.session.delete(dept)
    db.session.commit()

    return SuccessResponse(
        message="Department deleted successfully",
        data=None,
        status_code=204
    ).write_response()
