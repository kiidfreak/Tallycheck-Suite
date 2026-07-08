from typing import Any, Optional


class DepartmentSchema:
    @staticmethod
    def serialize(dept: Any) -> Optional[dict[str, Any]]:
        if not dept:
            return None
        return {
            "id": dept.id,
            "name": dept.name.replace('_', ' ').title() if dept.name else None,
            "manager_id": str(dept.manager_id) if dept.manager_id else None,
            "manager_name": f"{dept.manager.first_name} {dept.manager.last_name}" if dept.manager else None,
            "employee_count": len(dept.employees) if getattr(dept, 'employees', None) is not None else 0,
            "parent_department_id": dept.parent_department_id,
            "parent_department_name": dept.parent_department.name.replace('_', ' ').title() if dept.parent_department else None,
        }
