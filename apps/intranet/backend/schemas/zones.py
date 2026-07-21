from typing import Any, Optional

from schemas.departments import prettify


class ZoneSchema:
    @staticmethod
    def serialize(zone: Any) -> Optional[dict[str, Any]]:
        if not zone:
            return None
        org_unit = getattr(zone, 'org_unit', None)
        return {
            "id": zone.id,
            "name": zone.name,
            "zone_type": zone.zone_type,
            "org_unit_id": zone.org_unit_id,
            "org_unit_name": (
                getattr(org_unit, 'display_name', None) or prettify(org_unit.name)
            ) if org_unit else None,
            "code": zone.code,
            "description": zone.description,
            "capacity": zone.capacity,
            "is_active": zone.is_active,
            "beacon_count": len(zone.beacons) if getattr(zone, 'beacons', None) is not None else 0,
            "created_at": zone.created_at.isoformat() if zone.created_at else None,
            "updated_at": zone.updated_at.isoformat() if zone.updated_at else None,
        }


class ZoneRefSchema:
    """Compact zone, for nesting inside a beacon.

    Deliberately omits counts and timestamps — a beacon list would otherwise
    trigger a per-row `beacons` load just to render a name.
    """

    @staticmethod
    def serialize(zone: Any) -> Optional[dict[str, Any]]:
        if not zone:
            return None
        return {
            "id": zone.id,
            "name": zone.name,
            "zone_type": zone.zone_type,
        }
