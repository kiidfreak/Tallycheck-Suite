from typing import Any, Optional


def prettify(slug: Optional[str]) -> Optional[str]:
    """Slug -> display text, e.g. 'software_development' -> 'Software Development'.

    Lossy: internal capitals do not survive the round trip ('ios_team' reads back
    as 'Ios Team'). That is why `display_name` exists — this is only the fallback
    for rows written before it did.
    """
    return slug.replace('_', ' ').title() if slug else None


class DepartmentSchema:
    @staticmethod
    def serialize(dept: Any) -> Optional[dict[str, Any]]:
        if not dept:
            return None
        return {
            "id": dept.id,
            # `name` stays the prettified slug so existing consumers are
            # unaffected; `display_name` wins when a real label was supplied.
            "name": getattr(dept, 'display_name', None) or prettify(dept.name),
            "slug": dept.name,
            "display_name": getattr(dept, 'display_name', None),
            "unit_type": getattr(dept, 'unit_type', 'department'),
            "manager_id": str(dept.manager_id) if dept.manager_id else None,
            "manager_name": f"{dept.manager.first_name} {dept.manager.last_name}" if dept.manager else None,
            "employee_count": len(dept.employees) if getattr(dept, 'employees', None) is not None else 0,
            "parent_department_id": dept.parent_department_id,
            "parent_department_name": (
                getattr(dept.parent_department, 'display_name', None)
                or prettify(dept.parent_department.name)
            ) if dept.parent_department else None,
            "child_count": len(dept.sub_departments) if getattr(dept, 'sub_departments', None) is not None else 0,
        }
