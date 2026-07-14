from .employees import EmployeeSchema
from .attendance import AttendanceSchema, AuditLogSchema
from .roles import RoleSchema
from .departments import DepartmentSchema
from .beacons import BleBeaconSchema, BeaconAssignmentSchema

__all__ = [
    "EmployeeSchema",
    "AttendanceSchema",
    "RoleSchema",
    "DepartmentSchema",
    "AuditLogSchema",
    "BleBeaconSchema",
    "BeaconAssignmentSchema",
]
