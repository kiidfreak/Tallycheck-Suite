from datetime import datetime, timedelta

def get_team_presence(employee, db, Employee, AttendanceRecord):
    """Returns tuple of (team_present, team_total) for the given employee's department."""
    if not employee.department_id:
        return 0, 0

    team_total = Employee.query.filter_by(department_id=employee.department_id, is_active=True).count()
    today = datetime.utcnow().date()
    team_present = db.session.query(AttendanceRecord.employee_id).join(Employee, AttendanceRecord.employee_id == Employee.id).filter(
        Employee.department_id == employee.department_id,
        AttendanceRecord.work_date == today,
        AttendanceRecord.status.in_(['open', 'closed', 'corrected'])
    ).distinct().count()
    return team_present, team_total

def get_attendance_streak(employee, db, AttendanceRecord):
    """Returns the current attendance streak in days for the given employee (skipping weekends)."""
    date_rows = db.session.query(AttendanceRecord.work_date)\
        .filter(AttendanceRecord.employee_id == employee.id, AttendanceRecord.work_date.isnot(None))\
        .distinct()\
        .order_by(AttendanceRecord.work_date.desc())\
        .all()
    unique_dates = [row[0] for row in date_rows]
    streak = 0
    if unique_dates:
        expected = datetime.utcnow().date()
        if unique_dates[0] < expected:
            expected = unique_dates[0]
        for d in unique_dates:
            if d == expected:
                streak += 1
                expected -= timedelta(days=1)
                while expected.weekday() >= 5:
                    expected -= timedelta(days=1)
            else:
                break
    return streak