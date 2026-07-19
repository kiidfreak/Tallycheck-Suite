from typing import Tuple
import uuid
from flask import Blueprint, request, Response
from models import db, BleBeacon, BeaconAssignment, Department
from helpers.auth_helper import require_auth, roles_required, ADMIN_ROLES
from py_errors import ValidationError, NotFoundError
from py_success import SuccessResponse
from schemas import BleBeaconSchema, BeaconAssignmentSchema

beacon_bp = Blueprint('beacons', __name__, url_prefix='/beacons')

@beacon_bp.route('', methods=['GET'])
@require_auth
def get_beacons() -> Tuple[Response, int]:
    """Retrieve all BLE beacons for the active organization context."""
    beacons = BleBeacon.query.order_by(BleBeacon.name).all()
    serialized = [BleBeaconSchema.serialize(b) for b in beacons]
    return SuccessResponse(
        message="Beacons retrieved successfully",
        data=serialized,
        status_code=200
    ).write_response()

@beacon_bp.route('', methods=['POST'])
@roles_required(*ADMIN_ROLES)
def create_beacon() -> Tuple[Response, int]:
    """Create a new BLE beacon."""
    data = request.json or {}
    name = data.get('name')
    mac_address = data.get('mac_address')
    uuid_val = data.get('uuid')
    major = data.get('major', 1)
    minor = data.get('minor', 1)
    location = data.get('location')
    description = data.get('description')
    is_active = data.get('is_active', True)

    if not mac_address:
        raise ValidationError(details="MAC address is required")

    # Check unique MAC address
    existing = BleBeacon.query.filter_by(mac_address=mac_address).first()
    if existing:
        raise ValidationError(details=f"Beacon with MAC address {mac_address} already exists")

    new_beacon = BleBeacon(
        name=name,
        mac_address=mac_address,
        uuid=uuid_val,
        major=major,
        minor=minor,
        location=location,
        description=description,
        is_active=is_active
    )

    db.session.add(new_beacon)
    db.session.commit()

    return SuccessResponse(
        message="Beacon created successfully",
        data=BleBeaconSchema.serialize(new_beacon),
        status_code=201
    ).write_response()

@beacon_bp.route('/<uuid:beacon_id>', methods=['PUT'])
@roles_required(*ADMIN_ROLES)
def update_beacon(beacon_id: uuid.UUID) -> Tuple[Response, int]:
    """Update an existing BLE beacon."""
    beacon = BleBeacon.query.get(beacon_id)
    if not beacon:
        raise NotFoundError(message="Beacon not found")

    data = request.json or {}
    mac_address = data.get('mac_address')

    if mac_address and mac_address != beacon.mac_address:
        # Check uniqueness
        existing = BleBeacon.query.filter_by(mac_address=mac_address).first()
        if existing:
            raise ValidationError(details=f"Beacon with MAC address {mac_address} already exists")
        beacon.mac_address = mac_address

    if 'name' in data:
        beacon.name = data['name']
    if 'uuid' in data:
        beacon.uuid = data['uuid']
    if 'major' in data:
        beacon.major = data['major']
    if 'minor' in data:
        beacon.minor = data['minor']
    if 'location' in data:
        beacon.location = data['location']
    if 'description' in data:
        beacon.description = data['description']
    if 'is_active' in data:
        beacon.is_active = data['is_active']

    db.session.commit()

    return SuccessResponse(
        message="Beacon updated successfully",
        data=BleBeaconSchema.serialize(beacon),
        status_code=200
    ).write_response()

@beacon_bp.route('/<uuid:beacon_id>', methods=['DELETE'])
@roles_required(*ADMIN_ROLES)
def delete_beacon(beacon_id: uuid.UUID) -> Tuple[Response, int]:
    """Delete a BLE beacon."""
    beacon = BleBeacon.query.get(beacon_id)
    if not beacon:
        raise NotFoundError(message="Beacon not found")

    db.session.delete(beacon)
    db.session.commit()

    return SuccessResponse(
        message="Beacon deleted successfully",
        data={"id": str(beacon_id)},
        status_code=200
    ).write_response()

# --- ASSIGNMENT ENDPOINTS ---

@beacon_bp.route('/assignments', methods=['GET'])
@require_auth
def get_assignments() -> Tuple[Response, int]:
    """Retrieve all beacon-to-department assignments."""
    assignments = BeaconAssignment.query.all()
    serialized = [BeaconAssignmentSchema.serialize(a) for a in assignments]
    return SuccessResponse(
        message="Assignments retrieved successfully",
        data=serialized,
        status_code=200
    ).write_response()

@beacon_bp.route('/assignments', methods=['POST'])
@roles_required(*ADMIN_ROLES)
def create_assignment() -> Tuple[Response, int]:
    """Assign a beacon to a department."""
    data = request.json or {}
    beacon_id_str = data.get('beacon_id')
    department_id = data.get('department_id')

    if not beacon_id_str or not department_id:
        raise ValidationError(details="beacon_id and department_id are required")

    # Validate beacon exists
    try:
        beacon_id = uuid.UUID(beacon_id_str)
    except ValueError:
        raise ValidationError(details="Invalid beacon_id format")

    beacon = BleBeacon.query.get(beacon_id)
    if not beacon:
        raise NotFoundError(message="Beacon not found")

    # Validate department exists
    dept = Department.query.get(department_id)
    if not dept:
        raise NotFoundError(message="Department not found")

    # Check for existing assignment
    existing = BeaconAssignment.query.filter_by(beacon_id=beacon_id, department_id=department_id).first()
    if existing:
        raise ValidationError(details="Beacon is already assigned to this department")

    assignment = BeaconAssignment(beacon_id=beacon_id, department_id=department_id)
    db.session.add(assignment)
    db.session.commit()

    return SuccessResponse(
        message="Beacon assigned successfully",
        data=BeaconAssignmentSchema.serialize(assignment),
        status_code=201
    ).write_response()

@beacon_bp.route('/assignments/<uuid:assignment_id>', methods=['DELETE'])
@roles_required(*ADMIN_ROLES)
def delete_assignment(assignment_id: uuid.UUID) -> Tuple[Response, int]:
    """Remove a beacon-to-department assignment."""
    assignment = BeaconAssignment.query.get(assignment_id)
    if not assignment:
        raise NotFoundError(message="Assignment not found")

    db.session.delete(assignment)
    db.session.commit()

    return SuccessResponse(
        message="Beacon assignment removed successfully",
        data={"id": str(assignment_id)},
        status_code=200
    ).write_response()
