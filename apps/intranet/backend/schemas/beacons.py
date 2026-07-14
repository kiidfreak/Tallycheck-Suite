from typing import Any, Optional

class BleBeaconSchema:
    @staticmethod
    def serialize(beacon: Any) -> Optional[dict[str, Any]]:
        if not beacon:
            return None
        return {
            "id": str(beacon.id),
            "name": beacon.name,
            "mac_address": beacon.mac_address,
            "uuid": beacon.uuid,
            "major": beacon.major,
            "minor": beacon.minor,
            "location": beacon.location,
            "description": beacon.description,
            "is_active": beacon.is_active,
            "created_at": beacon.created_at.isoformat() if beacon.created_at else None,
            "updated_at": beacon.updated_at.isoformat() if beacon.updated_at else None
        }

class BeaconAssignmentSchema:
    @staticmethod
    def serialize(assignment: Any) -> Optional[dict[str, Any]]:
        if not assignment:
            return None
        return {
            "id": str(assignment.id),
            "beacon_id": str(assignment.beacon_id),
            "beacon_name": assignment.beacon.name if assignment.beacon else None,
            "beacon_mac": assignment.beacon.mac_address if assignment.beacon else None,
            "department_id": assignment.department_id,
            "department_name": assignment.department.name.replace('_', ' ').title() if assignment.department else None,
            "created_at": assignment.created_at.isoformat() if assignment.created_at else None
        }
