from typing import Any, Optional


class RoleSchema:
    @staticmethod
    def serialize(role: Any) -> Optional[dict[str, Any]]:
        if not role:
            return None
        return {
            "id": role.id,
            "role": role.role,
            "name": role.name.replace('_', ' ').title() if role.name else None
        }
