from typing import Any, Optional


class AttendanceSchema:
    @staticmethod
    def serialize(record: Any) -> Optional[dict[str, Any]]:
        if not record:
            return None
        
        worked_hours: Optional[float] = None
        if record.clock_out and record.clock_in:
            diff = record.clock_out - record.clock_in
            worked_hours = round(diff.total_seconds() / 3600.0, 2)
            
        return {
            "id": record.id,
            "employee_id": str(record.employee_id),
            "clock_in": record.clock_in.isoformat() + "Z" if record.clock_in else None,
            "clock_out": record.clock_out.isoformat() + "Z" if record.clock_out else None,
            "work_date": record.work_date.isoformat() if record.work_date else None,
            "worked_hours": worked_hours,
            "source": record.source,
            "status": record.status,
            "notes": record.notes,
            "edited_by": str(record.edited_by) if record.edited_by else None
        }


class AuditLogSchema:
    @staticmethod
    def serialize(log: Any) -> Optional[dict[str, Any]]:
        if not log:
            return None
            
        return {
            "id": log.id,
            "changed_by": str(log.changed_by),
            "record_changed": log.record_changed,
            "previous_clock_in": log.previous_clock_in.isoformat() + "Z" if log.previous_clock_in else None,
            "previous_clock_out": log.previous_clock_out.isoformat() + "Z" if log.previous_clock_out else None,
            "changed_at": log.changed_at.isoformat() + "Z" if log.changed_at else None,
            "reason_for_change": log.reason_for_change
        }
