from datetime import date, timedelta
from typing import Any, Optional


class ReportSchema:

    @staticmethod
    def _get_working_days(d_from: date, d_to: date) -> int:
        """Calculate number of Monday-Friday days between two dates inclusive."""
        days: int = 0
        current: date = d_from
        while current <= d_to:
            if current.weekday() < 5:  # 0-4 are Monday-Friday
                days += 1
            current += timedelta(days=1)
        return max(1, days)

    @classmethod
    def serialize_employee_attendance(
        cls,
        emp: Any,
        att_records: list[Any],
        d_from: Optional[date] = None,
        d_to: Optional[date] = None
    ) -> dict[str, Any]:
        """
        Groups a list of AttendanceRecords for a single Employee and 
        returns a dictionary matching the ReportEmployeeAttendance schema.
        """
        total_days_present: int = 0
        total_hours_worked: float = 0.0
        late_days: int = 0
        
        clock_ins: list[Any] = []
        clock_outs: list[Any] = []
        
        for r in att_records:
            if r.status in ['closed', 'open', 'corrected']:
                total_days_present += 1
                
            if r.clock_in:
                clock_ins.append(r.clock_in)
                if r.clock_in.hour >= 8 and r.clock_in.minute > 0:
                    late_days += 1
                    
            if r.clock_in and r.clock_out:
                clock_outs.append(r.clock_out)
                duration = r.clock_out - r.clock_in
                total_hours_worked += duration.total_seconds() / 3600.0

        # Calculate averages
        avg_clock_in: Optional[str] = None
        if clock_ins:
            avg_minutes: float = sum([t.hour * 60 + t.minute for t in clock_ins]) / len(clock_ins)
            h: int = int(avg_minutes // 60)
            m: int = int(avg_minutes % 60)
            avg_clock_in = f"{h:02d}:{m:02d}"

        avg_clock_out: Optional[str] = None
        if clock_outs:
            avg_minutes = sum([t.hour * 60 + t.minute for t in clock_outs]) / len(clock_outs)
            h = int(avg_minutes // 60)
            m = int(avg_minutes % 60)
            avg_clock_out = f"{h:02d}:{m:02d}"
            
        # Calculate exact absences
        today: date = date.today()
        calc_from: date = d_from or today.replace(day=1)
        calc_to: date = d_to or today
        if calc_to < calc_from:
            calc_to = calc_from
            
        expected_days: int = cls._get_working_days(calc_from, calc_to)
        total_days_absent: int = max(0, expected_days - total_days_present)
        
        return {
            "employee_id": str(emp.id),
            "employee_name": f"{emp.first_name} {emp.last_name}",
            "department": emp.department.name if emp.department else "Unassigned",
            "total_days_present": total_days_present,
            "total_days_absent": total_days_absent,
            "total_hours_worked": round(total_hours_worked, 2),
            "avg_clock_in": avg_clock_in,
            "avg_clock_out": avg_clock_out,
            "late_days": late_days
        }

    @classmethod
    def serialize_department_attendance(
        cls,
        dept: Any,
        att_records: list[Any],
        d_from: Optional[date] = None,
        d_to: Optional[date] = None
    ) -> dict[str, Any]:
        """
        Matches ReportDepartmentAttendance schema:
        department_id, department_name, date_from, date_to, total_employees,
        avg_attendance_rate, total_hours_worked, employees (array)
        """
        total_employees: int = len(dept.employees)
        
        # Group records by employee so we can serialize each employee
        grouped: dict[Any, list[Any]] = {}
        for r in att_records:
            if r.employee_id not in grouped:
                grouped[r.employee_id] = []
            grouped[r.employee_id].append(r)

        employees_data: list[dict[str, Any]] = []
        dept_total_hours: float = 0.0
        dept_total_present_days: int = 0

        for emp in dept.employees:
            emp_records: list[Any] = grouped.get(emp.id, [])
            emp_data: dict[str, Any] = cls.serialize_employee_attendance(emp, emp_records, d_from, d_to)
            employees_data.append(emp_data)
            
            dept_total_hours += emp_data["total_hours_worked"]
            dept_total_present_days += emp_data["total_days_present"]

        # Calculate exact working days
        today: date = date.today()
        calc_from: date = d_from or today.replace(day=1)
        calc_to: date = d_to or today
        
        if calc_to < calc_from:
            calc_to = calc_from

        working_days: int = cls._get_working_days(calc_from, calc_to)

        avg_attendance_rate: float = 0.0
        if total_employees > 0:
            expected_days: int = total_employees * working_days
            avg_attendance_rate = round((dept_total_present_days / expected_days) * 100, 2)

        return {
            "department_id": dept.id,
            "department_name": dept.name,
            "date_from": calc_from.isoformat() if d_from else None,
            "date_to": calc_to.isoformat() if d_to else None,
            "total_employees": total_employees,
            "avg_attendance_rate": min(100.0, avg_attendance_rate), # Cap at 100%
            "total_hours_worked": round(dept_total_hours, 2),
            "employees": employees_data
        }
