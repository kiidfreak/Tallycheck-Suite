from typing import Any, Optional, Tuple

from flask import Blueprint, Response, request

from models import db, Zone, Department, BleBeacon
from auth_routes import require_auth, roles_required, ADMIN_ROLES
from py_errors import NotFoundError, ValidationError
from py_success import SuccessResponse
from schemas.zones import ZoneSchema
from helpers.zone_helper import (
    DEFAULT_ZONE_TYPE,
    ZONE_TYPES,
    is_valid_zone_type,
    validate_capacity,
    validate_code,
    validate_name,
)

zone_bp: Blueprint = Blueprint('zones', __name__, url_prefix='/zones')


def _assert_name_free(name: str, org_unit_id: Optional[int], exclude_id: Optional[int] = None) -> None:
    """Zone names are unique within an org unit, not tenant-wide."""
    query = Zone.query.filter(
        Zone.name == name,
        Zone.org_unit_id.is_(None) if org_unit_id is None else Zone.org_unit_id == org_unit_id,
    )
    if exclude_id is not None:
        query = query.filter(Zone.id != exclude_id)
    if query.first():
        raise ValidationError(
            details="A zone with this name already exists in the same org unit."
        )


def _resolve_org_unit(org_unit_id: Any) -> Optional[int]:
    if org_unit_id is None:
        return None
    if not db.session.get(Department, org_unit_id):
        raise ValidationError(details="Org unit not found.")
    return int(org_unit_id)


@zone_bp.route('', methods=['GET'])
@require_auth
def list_zones() -> Tuple[Response, int]:
    """Zones in this tenant, newest filters applied.

    Read access is intentionally broad: an employee needs to see zone names to
    make sense of their own attendance records. Writes are admin-only.
    """
    query = Zone.query

    org_unit_id = request.args.get('org_unit_id')
    if org_unit_id:
        try:
            query = query.filter(Zone.org_unit_id == int(org_unit_id))
        except (TypeError, ValueError):
            raise ValidationError(details="org_unit_id must be an integer.")

    zone_type = request.args.get('zone_type')
    if zone_type:
        if not is_valid_zone_type(zone_type):
            raise ValidationError(
                details=f"zone_type must be one of: {', '.join(ZONE_TYPES)}."
            )
        query = query.filter(Zone.zone_type == zone_type)

    is_active = request.args.get('is_active')
    if is_active is not None and is_active != '':
        query = query.filter(Zone.is_active.is_(str(is_active).lower() in ('1', 'true', 'yes')))

    zones = query.order_by(Zone.name).all()
    return SuccessResponse(
        message="Success",
        data=[ZoneSchema.serialize(z) for z in zones],
        status_code=200
    ).write_response()


@zone_bp.route('/<int:zone_id>', methods=['GET'])
@require_auth
def get_zone(zone_id: int) -> Tuple[Response, int]:
    zone = db.session.get(Zone, zone_id)
    if not zone:
        raise NotFoundError(message="Zone not found.")
    return SuccessResponse(
        message="Success",
        data=ZoneSchema.serialize(zone),
        status_code=200
    ).write_response()


@zone_bp.route('', methods=['POST'])
@require_auth
@roles_required(*ADMIN_ROLES)
def create_zone() -> Tuple[Response, int]:
    body: dict[str, Any] = request.get_json() or {}

    try:
        name = validate_name(body.get('name'))
        code = validate_code(body.get('code'))
        capacity = validate_capacity(body.get('capacity'))
    except ValueError as exc:
        raise ValidationError(details=str(exc))

    zone_type = body.get('zone_type') or DEFAULT_ZONE_TYPE
    if not is_valid_zone_type(zone_type):
        raise ValidationError(details=f"zone_type must be one of: {', '.join(ZONE_TYPES)}.")

    org_unit_id = _resolve_org_unit(body.get('org_unit_id'))
    _assert_name_free(name, org_unit_id)

    zone = Zone(
        name=name,
        zone_type=zone_type,
        org_unit_id=org_unit_id,
        code=code,
        description=body.get('description'),
        capacity=capacity,
        is_active=bool(body.get('is_active', True)),
    )
    db.session.add(zone)
    db.session.commit()

    return SuccessResponse(
        message="Zone created successfully",
        data=ZoneSchema.serialize(zone),
        status_code=201
    ).write_response()


@zone_bp.route('/<int:zone_id>', methods=['PUT'])
@require_auth
@roles_required(*ADMIN_ROLES)
def update_zone(zone_id: int) -> Tuple[Response, int]:
    zone = db.session.get(Zone, zone_id)
    if not zone:
        raise NotFoundError(message="Zone not found.")

    body: dict[str, Any] = request.get_json() or {}

    # Resolve the destination org unit first: a rename and a move in one request
    # must be checked against where the zone ends up, not where it started.
    target_unit = (
        _resolve_org_unit(body['org_unit_id']) if 'org_unit_id' in body else zone.org_unit_id
    )

    if 'name' in body:
        try:
            name = validate_name(body['name'])
        except ValueError as exc:
            raise ValidationError(details=str(exc))
        _assert_name_free(name, target_unit, exclude_id=zone_id)
        zone.name = name
    elif 'org_unit_id' in body and target_unit != zone.org_unit_id:
        # Moving without renaming can still collide at the destination.
        _assert_name_free(zone.name, target_unit, exclude_id=zone_id)

    if 'org_unit_id' in body:
        zone.org_unit_id = target_unit

    if 'zone_type' in body:
        if not is_valid_zone_type(body['zone_type']):
            raise ValidationError(details=f"zone_type must be one of: {', '.join(ZONE_TYPES)}.")
        zone.zone_type = body['zone_type']

    if 'code' in body:
        try:
            zone.code = validate_code(body['code'])
        except ValueError as exc:
            raise ValidationError(details=str(exc))

    if 'capacity' in body:
        try:
            zone.capacity = validate_capacity(body['capacity'])
        except ValueError as exc:
            raise ValidationError(details=str(exc))

    if 'description' in body:
        zone.description = body['description']

    if 'is_active' in body:
        zone.is_active = bool(body['is_active'])

    db.session.commit()

    return SuccessResponse(
        message="Zone updated successfully",
        data=ZoneSchema.serialize(zone),
        status_code=200
    ).write_response()


@zone_bp.route('/<int:zone_id>', methods=['DELETE'])
@require_auth
@roles_required(*ADMIN_ROLES)
def delete_zone(zone_id: int) -> Tuple[Response, int]:
    """Delete a zone.

    Refused while beacons are still mounted in it. The FK is ON DELETE SET NULL,
    so the database would happily orphan them — but silently un-placing hardware
    is exactly the kind of change an admin should have to make deliberately.
    """
    zone = db.session.get(Zone, zone_id)
    if not zone:
        raise NotFoundError(message="Zone not found.")

    mounted = BleBeacon.query.filter_by(zone_id=zone_id).count()
    if mounted:
        raise ValidationError(
            details=(
                f"{mounted} beacon(s) are still placed in this zone. "
                "Move them to another zone first."
            )
        )

    db.session.delete(zone)
    db.session.commit()

    return SuccessResponse(
        message="Zone deleted successfully",
        data={"id": zone_id},
        status_code=200
    ).write_response()
