import uuid
from datetime import datetime, timezone, date, timedelta
from typing import Optional
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import synonym, Mapped, mapped_column, relationship
from utils.shift_data import *
from helpers.shift_calc_helper import *

db = SQLAlchemy()

class Organization(db.Model):
    __tablename__ = 'organizations'
    __table_args__ = {'schema': 'public'}

    id: Mapped[str] = mapped_column(db.String(50), primary_key=True)  # Auth0 org_id or subdomain
    name: Mapped[str] = mapped_column(db.String(100), nullable=False)
    domain: Mapped[str] = mapped_column(db.String(100), unique=True, nullable=False)
    schema_name: Mapped[str] = mapped_column(db.String(50), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(db.Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self) -> str:
        return f"<Organization {self.name} ({self.id})>"

# Join table for Roles and Modules
role_modules = db.Table('role_modules',
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
    db.Column('module_id', db.Integer, db.ForeignKey('modules.id', ondelete='CASCADE'), primary_key=True)
)

class Module(db.Model):
    __tablename__ = 'modules'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    module: Mapped[str] = mapped_column(db.String, unique=True, nullable=False)
    name = synonym('module')

    def __repr__(self) -> str:
        return f"<Module {self.module}>"

class Role(db.Model):
    __tablename__ = 'roles'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    role: Mapped[str] = mapped_column(db.String, unique=True, nullable=False)
    name = synonym('role')
    
    modules: Mapped[list[Module]] = relationship('Module', secondary=role_modules, backref=db.backref('roles', lazy=True))

    def __repr__(self) -> str:
        return f"<Role {self.role}>"

class JobTitle(db.Model):
    __tablename__ = 'job_titles'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    title: Mapped[str] = mapped_column(db.String, unique=True, nullable=False)

    def __repr__(self) -> str:
        return f"<JobTitle {self.title}>"

class AttendanceRecord(db.Model):
    __tablename__ = 'attendance_records'
    __table_args__ = (db.Index('idx_emp_work_date', 'employee_id', 'work_date'),)

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    employee_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), db.ForeignKey('employees.id', ondelete='CASCADE'), nullable=False, index=True)
    clock_in: Mapped[datetime] = mapped_column(db.DateTime, nullable=False)
    clock_out: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)
    work_date: Mapped[date] = mapped_column(db.Date, nullable=False, index=True)
    source: Mapped[str] = mapped_column(db.String(50), default='web', nullable=False)
    status: Mapped[str] = mapped_column(db.String(50), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    edited_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), db.ForeignKey('employees.id', ondelete='SET NULL'), nullable=True)

    employee: Mapped["Employee"] = relationship('Employee', foreign_keys=[employee_id], backref=db.backref('attendance_records', lazy=True, cascade="all, delete-orphan"))
    editor: Mapped[Optional["Employee"]] = relationship('Employee', foreign_keys=[edited_by])

    def __repr__(self) -> str:
        return f"<AttendanceRecord {self.employee_id} clocked in {self.clock_in}>"

class Department(db.Model):
    __tablename__ = 'departments'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(db.String, unique=True, nullable=False)
    
    # Circular Foreign Key pointing back to Employee table
    manager_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), db.ForeignKey('employees.id', use_alter=True, name='fk_dept_manager'), nullable=True)

    # Self-referential FK for department nesting (e.g. "Business Efficiency" → "Operations & Projects")
    parent_department_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('departments.id', name='fk_dept_parent'), nullable=True)

    manager: Mapped[Optional["Employee"]] = relationship('Employee', foreign_keys=[manager_id], post_update=True)
    parent_department: Mapped[Optional["Department"]] = relationship('Department', foreign_keys=[parent_department_id], remote_side='Department.id', backref='sub_departments')

    def __repr__(self) -> str:
        return f"<Department {self.name}>"

class Employee(db.Model):
    __tablename__ = 'employees'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    auth0_id: Mapped[str] = mapped_column(db.String, unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(db.String, unique=True, nullable=False, index=True)
    password_hash: Mapped[Optional[str]] = mapped_column(db.String, nullable=True)
    is_active: Mapped[bool] = mapped_column(db.Boolean, default=True, nullable=False)
    first_name: Mapped[str] = mapped_column(db.String, nullable=False)
    last_name: Mapped[str] = mapped_column(db.String, nullable=False)
    hire_date: Mapped[Optional[date]] = mapped_column(db.Date, nullable=True)
    is_internal: Mapped[bool] = mapped_column(db.Boolean, default=True, nullable=False)

    # --- Shift configuration ---
    shift_type: Mapped[ShiftType] = mapped_column(db.String, default=ShiftType.STD, server_default=ShiftType.STD.value, nullable=False)
    shift_hours: Mapped[ShiftHours] = mapped_column(db.String, default=ShiftHours.EARLY_MORN, server_default=ShiftHours.EARLY_MORN.value, nullable=False)

    # custom_shift_start / custom_shift_end: only set when shift_hours == 'custom'.
    # IMPORTANT: values MUST be stored in 24-hour HH:MM format (e.g. '14:00').
    # The frontend must use <input type="time"> which natively outputs 24h HH:MM.
    # A 12-hour format here would cause silently incorrect cutoff calculations.
    # This is because since a shift is 10 hours long we calculate the correct end time by
    # adding 10 to the start time e.g. 8am + 10hrs = 1800hrs which equals 6pm. Using 12 hours would
    # be damaging if anyone has afternoon shifts as now 3pm would end at 3+10 = 1300hrs which
    # equals 1pm instead of 1am. Basically, telling the difference between AM and PM if
    # we use 12 hour format is harder than life in Kenya. Long story short, 24 hour format only!
    custom_shift_start: Mapped[Optional[str]] = mapped_column(db.String(5), nullable=True)
    custom_shift_end: Mapped[Optional[str]] = mapped_column(db.String(5), nullable=True)

    # TO-DO: Delete this column
    # Legacy column — superseded by shift_type/shift_hours; kept for backward compat, remove in a future migration.
    standard_shift: Mapped[str] = mapped_column(db.String, default='morning', server_default='morning', nullable=False)

    avatar: Mapped[Optional[str]] = mapped_column(db.String, nullable=True)
    is_approved: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Foreign Keys
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    department = db.relationship('Department', foreign_keys=[department_id], backref='employees')
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=True)
    role = db.relationship('Role', backref='employees')
    job_title_id = db.Column(db.Integer, db.ForeignKey('job_titles.id'), nullable=True)
    job_title = db.relationship('JobTitle', backref='employees')
    is_manager = db.Column(db.Boolean, default=False, nullable=False)

    # Computed shift helpers (wired from helpers/shift_calc_helper.py)
    shift_start_hour = shift_start_hour
    shift_end_hour = shift_end_hour
    shift_cutoff_hour = shift_cutoff_hour
    shift_duration_hours = shift_duration_hours

    def __repr__(self):
        return f"<Employee {self.email} (Role ID: {self.role_id})>"


class AuditLog(db.Model):
    __tablename__ = 'audit_log'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    changed_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), db.ForeignKey('employees.id', ondelete='CASCADE'), nullable=False)
    record_changed: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('attendance_records.id', ondelete='CASCADE'), nullable=False)
    previous_clock_in: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)
    previous_clock_out: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)
    changed_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow, nullable=False)
    reason_for_change: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)

    employee: Mapped["Employee"] = relationship('Employee', backref='audit_logs')
    attendance_record: Mapped["AttendanceRecord"] = relationship('AttendanceRecord', backref='audit_logs')


class BleBeacon(db.Model):
    __tablename__ = 'ble_beacons'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[Optional[str]] = mapped_column(db.String(100), nullable=True)
    mac_address: Mapped[str] = mapped_column(db.String(50), unique=True, nullable=False)
    uuid: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    major: Mapped[int] = mapped_column(db.Integer, default=1, nullable=False)
    minor: Mapped[int] = mapped_column(db.Integer, default=1, nullable=False)
    location: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(db.Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self) -> str:
        return f"<BleBeacon {self.name or self.mac_address}>"


class BeaconAssignment(db.Model):
    __tablename__ = 'beacon_assignments'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    beacon_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), db.ForeignKey('ble_beacons.id', ondelete='CASCADE'), nullable=False)
    department_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('departments.id', ondelete='CASCADE'), nullable=True)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    beacon: Mapped["BleBeacon"] = relationship('BleBeacon', backref=db.backref('assignments', lazy=True, cascade="all, delete-orphan"))
    department: Mapped[Optional["Department"]] = relationship('Department', backref='beacon_assignments')

    __table_args__ = (
        db.UniqueConstraint('beacon_id', 'department_id', name='uq_beacon_dept'),
    )

    def __repr__(self) -> str:
        return f"<BeaconAssignment {self.beacon_id} to dept {self.department_id}>"


class Child(db.Model):
    __tablename__ = 'children'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    group_name: Mapped[str] = mapped_column(db.String(100), nullable=False)
    photo_url: Mapped[Optional[str]] = mapped_column(db.String(512), nullable=True)
    is_active: Mapped[bool] = mapped_column(db.Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self) -> str:
        return f"<Child {self.name}>"


class Guardian(db.Model):
    __tablename__ = 'guardians'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    phone: Mapped[str] = mapped_column(db.String(20), nullable=False)
    relation: Mapped[str] = mapped_column(db.String(50), nullable=False)
    photo_url: Mapped[Optional[str]] = mapped_column(db.String(512), nullable=True)
    is_active: Mapped[bool] = mapped_column(db.Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self) -> str:
        return f"<Guardian {self.name}>"


class ChildGuardian(db.Model):
    __tablename__ = 'child_guardians'

    child_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), db.ForeignKey('children.id', ondelete='CASCADE'), primary_key=True)
    guardian_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), db.ForeignKey('guardians.id', ondelete='CASCADE'), primary_key=True)
    is_primary: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)
    authorization_status: Mapped[str] = mapped_column(db.String(50), default='approved', nullable=False)

    child: Mapped["Child"] = relationship('Child', backref=db.backref('guardian_links', lazy=True, cascade="all, delete-orphan"))
    guardian: Mapped["Guardian"] = relationship('Guardian', backref=db.backref('child_links', lazy=True, cascade="all, delete-orphan"))

    def __repr__(self) -> str:
        return f"<ChildGuardian {self.child_id} - {self.guardian_id}>"


class PickupToken(db.Model):
    __tablename__ = 'pickup_tokens'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    child_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), db.ForeignKey('children.id', ondelete='CASCADE'), nullable=False)
    guardian_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), db.ForeignKey('guardians.id', ondelete='SET NULL'), nullable=True)
    token_type: Mapped[str] = mapped_column(db.String(10), nullable=False)  # 'QR' or 'PIN'
    qr_payload: Mapped[str] = mapped_column(db.String(255), unique=True, nullable=False)
    pin: Mapped[str] = mapped_column(db.String(4), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(db.DateTime, nullable=False)
    status: Mapped[str] = mapped_column(db.String(20), default='pending', nullable=False)  # 'pending', 'verified', 'expired'
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), db.ForeignKey('employees.id'), nullable=True)
    verified_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), db.ForeignKey('employees.id'), nullable=True)
    verified_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    child: Mapped["Child"] = relationship('Child')
    guardian: Mapped[Optional["Guardian"]] = relationship('Guardian')
    creator: Mapped[Optional["Employee"]] = relationship('Employee', foreign_keys=[created_by])
    verifier: Mapped[Optional["Employee"]] = relationship('Employee', foreign_keys=[verified_by])

    def __repr__(self) -> str:
        return f"<PickupToken {self.id} for {self.child_id}>"


