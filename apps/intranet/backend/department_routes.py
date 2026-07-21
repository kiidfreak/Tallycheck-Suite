from typing import Any, Optional, Tuple
from flask import Blueprint, request, Response
from sqlalchemy import literal, select
from models import db, Department, Employee
from auth_routes import require_auth, roles_required, ADMIN_ROLES
from py_errors import NotFoundError, DepartmentHasEmployeesError, ValidationError
from py_success import SuccessResponse
from schemas.departments import DepartmentSchema
from schemas.employees import EmployeeSchema
from helpers.org_tree_helper import (
    DEFAULT_UNIT_TYPE,
    MAX_DEPTH,
    UNIT_TYPES,
    assemble_tree,
    is_valid_unit_type,
    violates_depth_limit,
    would_create_cycle,
)

department_bp: Blueprint = Blueprint('departments', __name__, url_prefix='/departments')


def _slugify(raw: Any) -> str:
    return str(raw).strip().lower().replace(' ', '_')


def _edges() -> dict[int, Optional[int]]:
    """Whole tenant's parent map, as plain ints.

    One query. Org trees here are tens to low hundreds of nodes, so loading the
    edge set and validating in Python is cheaper and far easier to test than
    pushing cycle detection into SQL.
    """
    rows = db.session.execute(
        select(Department.id, Department.parent_department_id)
    ).all()
    return {row[0]: row[1] for row in rows}


def _validate_parent(node_id: Optional[int], parent_id: Optional[int]) -> None:
    """Reject a parent that does not exist, closes a cycle, or breaches depth."""
    if parent_id is None:
        return

    parent = db.session.get(Department, parent_id)
    if not parent:
        raise ValidationError(details="Parent department not found.")

    edges = _edges()
    if node_id is not None:
        if would_create_cycle(edges, node_id, parent_id):
            raise ValidationError(
                details="That parent is inside this unit's own subtree, which would create a loop."
            )
        if violates_depth_limit(edges, node_id, parent_id):
            raise ValidationError(
                details=f"That move would nest the org chart deeper than {MAX_DEPTH} levels."
            )
    else:
        # Creating a new leaf: depth is the parent's depth plus one.
        edges[-1] = parent_id
        if violates_depth_limit(edges, -1, parent_id):
            raise ValidationError(
                details=f"That parent is already {MAX_DEPTH} levels deep."
            )


def _assert_name_free(name: str, parent_id: Optional[int], exclude_id: Optional[int] = None) -> None:
    """Names are unique among siblings, not tenant-wide.

    Two sites may both have a "Reception"; one site may not have two.
    """
    query = Department.query.filter(
        Department.name == name,
        Department.parent_department_id.is_(None) if parent_id is None
        else Department.parent_department_id == parent_id,
    )
    if exclude_id is not None:
        query = query.filter(Department.id != exclude_id)
    if query.first():
        raise ValidationError(
            details="A unit with this name already exists under the same parent."
        )


def descendant_ids_subquery(root_id: int, max_depth: int = 20):
    """Subquery of `root_id` plus every descendant.

    The depth predicate is the cycle guard: a cyclic edge that reached the
    database some other way terminates at `max_depth` instead of recursing until
    the connection dies.
    """
    walk = (
        select(Department.id.label('id'), literal(0).label('depth'))
        .where(Department.id == root_id)
        .cte('descendants', recursive=True)
    )
    walk = walk.union_all(
        select(Department.id, (walk.c.depth + 1))
        .join(walk, Department.parent_department_id == walk.c.id)
        .where(walk.c.depth < max_depth)
    )
    return select(walk.c.id)


@department_bp.route('', methods=['GET'])
@require_auth
def list_departments() -> Tuple[Response, int]:
    departments = Department.query.all()
    return SuccessResponse(
        message="Success",
        data=[DepartmentSchema.serialize(d) for d in departments],
        status_code=200
    ).write_response()


@department_bp.route('/tree', methods=['GET'])
@require_auth
def department_tree() -> Tuple[Response, int]:
    """The org chart, nested.

    Assembled in Python rather than by recursive SQL: the whole tenant tree is
    small, one flat query plus an in-memory pass is faster than a recursive CTE
    that still has to be re-nested, and `assemble_tree` is unit-tested including
    the cyclic and orphaned cases.
    """
    departments = Department.query.all()
    rows = [DepartmentSchema.serialize(d) for d in departments]
    return SuccessResponse(
        message="Success",
        data=assemble_tree([r for r in rows if r]),
        status_code=200
    ).write_response()


@department_bp.route('/<int:id>/employees', methods=['GET'])
@require_auth
def department_employees(id: int) -> Tuple[Response, int]:
    """Everyone in this unit, and optionally everyone beneath it.

    `?include_descendants=true` is what makes the hierarchy useful — "show me
    everyone at Nairobi Campus" spans the sites, divisions and teams under it.
    """
    dept = db.session.get(Department, id)
    if not dept:
        raise NotFoundError(message="Department not found.")

    include_descendants = str(request.args.get('include_descendants', '')).lower() in ('1', 'true', 'yes')

    if include_descendants:
        # Subquery, not a materialised id list: same cost at this size and it
        # does not degrade as a tenant grows.
        employees = Employee.query.filter(
            Employee.department_id.in_(descendant_ids_subquery(id))
        ).all()
    else:
        employees = Employee.query.filter(Employee.department_id == id).all()

    return SuccessResponse(
        message="Success",
        data=[EmployeeSchema.serialize(e) for e in employees],
        status_code=200
    ).write_response()


@department_bp.route('', methods=['POST'])
@require_auth
@roles_required(*ADMIN_ROLES)
def create_department() -> Tuple[Response, int]:
    body: Optional[dict[str, Any]] = request.get_json()
    if not body or 'name' not in body or not str(body['name']).strip():
        raise ValidationError(details="Department name is required.")

    name: str = _slugify(body['name'])
    manager_id: Optional[str] = body.get('manager_id')
    parent_department_id: Optional[int] = body.get('parent_department_id')

    unit_type: str = body.get('unit_type') or DEFAULT_UNIT_TYPE
    if not is_valid_unit_type(unit_type):
        raise ValidationError(
            details=f"unit_type must be one of: {', '.join(UNIT_TYPES)}."
        )

    _assert_name_free(name, parent_department_id)
    # Previously only checked on update, so a cycle could be created at insert.
    _validate_parent(None, parent_department_id)

    new_dept = Department(name=name, unit_type=unit_type)

    display_name = body.get('display_name')
    if display_name is not None and str(display_name).strip():
        new_dept.display_name = str(display_name).strip()

    if manager_id:
        manager = db.session.get(Employee, manager_id)
        if not manager:
            raise ValidationError(details="Manager not found.")
        new_dept.manager_id = manager.id
        # Automatically promote the employee to manager
        manager.is_manager = True

    if parent_department_id is not None:
        new_dept.parent_department_id = parent_department_id

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
    dept = db.session.get(Department, id)
    if not dept:
        raise NotFoundError(message="Department not found.")

    body: dict[str, Any] = request.get_json() or {}

    # Resolve the prospective parent first: a rename and a move in the same
    # request must be validated against the parent the unit will end up under,
    # not the one it is leaving.
    target_parent = body['parent_department_id'] if 'parent_department_id' in body else dept.parent_department_id

    if 'parent_department_id' in body:
        _validate_parent(id, target_parent)

    if 'name' in body:
        name: str = _slugify(body['name'])
        _assert_name_free(name, target_parent, exclude_id=id)
        dept.name = name

    if 'display_name' in body:
        raw_display = body['display_name']
        dept.display_name = str(raw_display).strip() if raw_display and str(raw_display).strip() else None

    if 'unit_type' in body:
        unit_type = body['unit_type']
        if not is_valid_unit_type(unit_type):
            raise ValidationError(
                details=f"unit_type must be one of: {', '.join(UNIT_TYPES)}."
            )
        dept.unit_type = unit_type

    if 'manager_id' in body:
        new_manager_id: Optional[str] = body['manager_id']
        old_manager_id = dept.manager_id

        if new_manager_id is None:
            dept.manager_id = None
        else:
            new_manager = db.session.get(Employee, new_manager_id)
            if not new_manager:
                raise ValidationError(details="Manager not found.")
            dept.manager_id = new_manager.id
            # Automatically promote the new employee to manager
            new_manager.is_manager = True

        # Clean up the old manager's flag if they were replaced or removed
        if old_manager_id and str(old_manager_id) != str(new_manager_id):
            old_manager = db.session.get(Employee, old_manager_id)
            if old_manager:
                # Check if they still manage any other departments
                still_manages = Department.query.filter(Department.manager_id == old_manager.id, Department.id != dept.id).count()
                if still_manages == 0:
                    old_manager.is_manager = False

    if 'parent_department_id' in body:
        dept.parent_department_id = target_parent

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
    dept = db.session.get(Department, id)
    if not dept:
        raise NotFoundError(message="Department not found.")

    if Employee.query.filter_by(department_id=id).first():
        raise DepartmentHasEmployeesError()

    children = Department.query.filter_by(parent_department_id=id).all()
    if children:
        # Silently promoting a campus's children to roots loses the org chart,
        # so the caller has to say where they should go.
        raw_target = request.args.get('reparent_to')
        if raw_target is None:
            raise ValidationError(
                details=(
                    f"This unit has {len(children)} child unit(s). "
                    "Pass ?reparent_to=<id> to move them, or delete them first."
                )
            )
        if str(raw_target).lower() in ('null', 'root', ''):
            new_parent_id: Optional[int] = None
        else:
            try:
                new_parent_id = int(raw_target)
            except (TypeError, ValueError):
                raise ValidationError(details="reparent_to must be a department id, 'root', or omitted.")
            if new_parent_id == id:
                raise ValidationError(details="Cannot reparent children onto the unit being deleted.")
            if not db.session.get(Department, new_parent_id):
                raise ValidationError(details="Reparent target not found.")

        # Same transaction as the delete: a partial move would strand branches.
        for child in children:
            child.parent_department_id = new_parent_id

    db.session.delete(dept)
    db.session.commit()

    return SuccessResponse(
        message="Department deleted successfully",
        data={"id": id},
        status_code=200
    ).write_response()
