from typing import Any, Optional
from models import Role, Department

class EmployeeSchema:
    @staticmethod
    def serialize(emp: Any) -> Optional[dict[str, Any]]:
        if not emp:
            return None
        manager_name: Optional[str] = None
        if emp.is_manager:
            # e.g. Test Maduong manages Call Centre → Call Centre's parent is Operations → reports to Operations manager
            managed_dept = Department.query.filter_by(manager_id=emp.id).first()
            if managed_dept and managed_dept.parent_department:
                parent_mgr = managed_dept.parent_department.manager
                if parent_mgr and parent_mgr.id != emp.id:
                    manager_name = f"{parent_mgr.first_name} {parent_mgr.last_name}"
            # If the managed dept has no parent (e.g. Executive), manager_name stays None → top of chain
        else:
            # Regular employee reports to their own department's manager
            if emp.department and emp.department.manager:
                manager_name = f"{emp.department.manager.first_name} {emp.department.manager.last_name}"

        role_str = None
        if emp.role:
            role_str = emp.role.name
        elif emp.role_id:
            role_obj = Role.query.get(emp.role_id)
            role_str = role_obj.name if role_obj else None

        return {
            "id": str(emp.id),
            "email": emp.email,
            "first_name": emp.first_name,
            "last_name": emp.last_name,
            "role_id": emp.role_id,
            "role_name": role_str,
            "is_approved": emp.is_approved,
            "is_manager": emp.is_manager,
            "department_id": emp.department_id,
            "department_name": emp.department.name if emp.department else None,
            "manager_name": manager_name,
            "is_active": emp.is_active,
            "shift_type": emp.shift_type.value if hasattr(emp.shift_type, 'value') else emp.shift_type,
            "shift_hours": emp.shift_hours.value if hasattr(emp.shift_hours, 'value') else emp.shift_hours,
            "shift_duration_hours": emp.shift_duration_hours,
            "custom_shift_start": emp.custom_shift_start,
            "custom_shift_end": emp.custom_shift_end,
            "standard_shift": emp.standard_shift,
            "hire_date": emp.hire_date.isoformat() if emp.hire_date else None,
            "created_at": emp.created_at.isoformat() if emp.created_at else None
        }
