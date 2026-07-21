import uuid
from datetime import datetime, timezone, date, timedelta
from typing import Optional
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import synonym, Mapped, mapped_column, relationship
from utils.shift_data import *
from helpers.shift_calc_helper import *

db = SQLAlchemy()

class Organization(db.Model):
    __tablename__ = 'organizations'
    # The tuple form (CHECK constraints + the schema dict LAST) — SQLAlchemy
    # requires the options dict to be the final element.
    __table_args__ = (
        db.CheckConstraint(
            "org_type IN ('corporate','education','church','visitor')",
            name='ck_org_type',
        ),
        db.CheckConstraint(
            "status IN ('pending','provisioning','active','failed')",
            name='ck_org_status',
        ),
        {'schema': 'public'},
    )

    id: Mapped[str] = mapped_column(db.String(50), primary_key=True)  # Auth0 org_id or subdomain
    name: Mapped[str] = mapped_column(db.String(100), nullable=False)
    domain: Mapped[str] = mapped_column(db.String(100), unique=True, nullable=False)
    schema_name: Mapped[str] = mapped_column(db.String(50), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(db.Boolean, default=True, nullable=False)

    # Product / vertical. Drives which report shape a tenant renders (corporate,
    # academic, church-safechild, visitor-vcheck). 'visitor' is the vcheck seam.
    org_type: Mapped[str] = mapped_column(
        db.String(20), nullable=False, server_default='corporate'
    )
    # Provisioning lifecycle. A POST to /organizations writes a 'pending' row;
    # the out-of-band `flask provision-tenant` CLI creates the schema and flips
    # it to 'active'. Existing rows are already live.
    status: Mapped[str] = mapped_column(
        db.String(20), nullable=False, server_default='active'
    )

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
    """A node in the tenant's org tree.

    Despite the table name this holds every level of the hierarchy — regions,
    sites, divisions, departments, teams — discriminated by `unit_type`. Reusing
    this table rather than introducing `org_units` keeps `Employee.department_id`,
    `BeaconAssignment.department_id` and every existing report working untouched.

    The tree is an adjacency list (`parent_department_id`). Cycle and depth rules
    are enforced in the routes via helpers/org_tree_helper.py, not by a database
    trigger — a trigger would be another per-schema object for migrations/env.py
    to fan out across every tenant.
    """
    __tablename__ = 'departments'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)

    # Slug. Still the uniqueness key, so existing consumers are unaffected.
    # Uniqueness is scoped to the parent (see __table_args__): globally-unique
    # names break the moment two sites each want a "Reception".
    name: Mapped[str] = mapped_column(db.String, nullable=False)

    # Human-authored label. Nullable so no backfill is needed; the serializer
    # falls back to prettifying `name`. This exists because the slug round-trip
    # is lossy — "iOS Team" stores as "ios_team" and reads back as "Ios Team".
    display_name: Mapped[Optional[str]] = mapped_column(db.String(120), nullable=True)

    # Structural level, NOT a vertical noun. "site" covers campus/branch/depot/
    # store; the customer-facing word is a display concern mapped per org type in
    # the frontend. Kept as String + CHECK rather than a native Postgres ENUM,
    # because enum types are per-schema objects and every new value would need an
    # ALTER TYPE fanned out across every tenant schema.
    unit_type: Mapped[str] = mapped_column(
        db.String(20), nullable=False, server_default='department'
    )

    # Circular Foreign Key pointing back to Employee table
    manager_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), db.ForeignKey('employees.id', use_alter=True, name='fk_dept_manager'), nullable=True)

    # Self-referential FK for org nesting (e.g. "Nairobi Campus" → "Engineering").
    # ON DELETE SET NULL promotes children to roots rather than cascading an
    # entire campus away or hard-erroring. The routes refuse the delete outright
    # unless a reparent target is given; this is the safety net, not the path.
    parent_department_id: Mapped[Optional[int]] = mapped_column(
        db.Integer,
        db.ForeignKey('departments.id', name='fk_dept_parent', ondelete='SET NULL'),
        nullable=True,
    )

    manager: Mapped[Optional["Employee"]] = relationship('Employee', foreign_keys=[manager_id], post_update=True)
    parent_department: Mapped[Optional["Department"]] = relationship('Department', foreign_keys=[parent_department_id], remote_side='Department.id', backref='sub_departments')

    __table_args__ = (
        # Two partial indexes rather than one UNIQUE(parent_department_id, name):
        # Postgres treats NULLs as distinct, so a plain composite would leave
        # root-level names entirely unconstrained. NULLS NOT DISTINCT would be
        # tidier but is PG15+, and that dependency is not worth taking.
        db.Index(
            'uq_dept_parent_name',
            'parent_department_id',
            'name',
            unique=True,
            postgresql_where=db.text('parent_department_id IS NOT NULL'),
        ),
        db.Index(
            'uq_dept_root_name',
            'name',
            unique=True,
            postgresql_where=db.text('parent_department_id IS NULL'),
        ),
        db.CheckConstraint(
            "unit_type IN ('root','region','site','division','department','team')",
            name='ck_dept_unit_type',
        ),
    )

    def __repr__(self) -> str:
        return f"<Department {self.name} ({self.unit_type})>"

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

    # Manager-set clock-in cutoff for this employee, as an hour (0-23).
    # NULL means "use the tenant default" (OrgSettings.checkin_cutoff_hours_after_start
    # applied to this employee's shift start). Only managers/admins may set it —
    # employees cannot extend their own cutoff.
    checkin_cutoff_hour: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)

    avatar: Mapped[Optional[str]] = mapped_column(db.String, nullable=True)
    is_approved: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Foreign Keys
    # SET NULL so removing an org unit unassigns its employees rather than
    # failing the delete with a FK violation. The route still refuses to delete a
    # unit that has employees, so this is a safety net rather than the path.
    department_id = db.Column(
        db.Integer, db.ForeignKey('departments.id', ondelete='SET NULL'), nullable=True
    )
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


class Zone(db.Model):
    """A named place inside a tenant — a room, bay, gate, ward, yard.

    This is what turns beacon telemetry from a MAC address into something a
    customer recognises: "Loading Bay 3", not "AC:23:45:67:89:01". It replaces
    `BleBeacon.location`, which was unstructured free text.

    A zone optionally belongs to an org unit (`org_unit_id`), so "everything at
    Nairobi Campus" can span zones as well as people.
    """
    __tablename__ = 'zones'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(db.String(120), nullable=False)

    # Physical kind. Like Department.unit_type this is String + CHECK rather than
    # a native ENUM: enum types are per-schema objects, so each new value would
    # need an ALTER TYPE fanned out across every tenant schema.
    zone_type: Mapped[str] = mapped_column(
        db.String(30), nullable=False, server_default='general'
    )

    # Nullable so zones can exist before the org chart is built — the
    # location-backfill migration depends on that.
    org_unit_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey('departments.id', ondelete='SET NULL'), nullable=True
    )

    code: Mapped[Optional[str]] = mapped_column(db.String(50), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    capacity: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(db.Boolean, default=True, nullable=False)

    # ---- RESERVED: unused by design, do not remove ----------------------
    # Indoor mapping (floor plans, drawn polygons) is a later phase, but adding
    # columns then means a migration fanned across every tenant schema, whereas
    # nullable columns now cost nothing. When floor plans land they belong to a
    # *building*, not a zone — expect a `floor_plans` table (site_id,
    # floor_label, image_url, width_m, height_m) joined via `floor_label`.
    floor_label: Mapped[Optional[str]] = mapped_column(db.String(50), nullable=True)
    # GeoJSON polygon once a zone editor exists. JSON with a JSONB variant so the
    # model still loads outside Postgres.
    geometry: Mapped[Optional[dict]] = mapped_column(
        db.JSON().with_variant(JSONB, 'postgresql'), nullable=True
    )
    floor_plan_url: Mapped[Optional[str]] = mapped_column(db.String(512), nullable=True)
    # ---------------------------------------------------------------------

    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    org_unit: Mapped[Optional["Department"]] = relationship('Department', backref='zones')

    __table_args__ = (
        # Same partial-index pair as departments: names are unique within an org
        # unit, so two sites may each have a "Reception". A plain composite would
        # leave unassigned zones unconstrained, since Postgres treats NULLs as
        # distinct.
        db.Index(
            'uq_zone_unit_name',
            'org_unit_id',
            'name',
            unique=True,
            postgresql_where=db.text('org_unit_id IS NOT NULL'),
        ),
        db.Index(
            'uq_zone_global_name',
            'name',
            unique=True,
            postgresql_where=db.text('org_unit_id IS NULL'),
        ),
        db.CheckConstraint(
            "zone_type IN ('room','classroom','hall','entrance','gate',"
            "'loading_bay','storage','ward','yard','general')",
            name='ck_zone_type',
        ),
    )

    def __repr__(self) -> str:
        return f"<Zone {self.name} ({self.zone_type})>"


class BleBeacon(db.Model):
    __tablename__ = 'ble_beacons'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[Optional[str]] = mapped_column(db.String(100), nullable=True)
    mac_address: Mapped[str] = mapped_column(db.String(50), unique=True, nullable=False)
    uuid: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    major: Mapped[int] = mapped_column(db.Integer, default=1, nullable=False)
    minor: Mapped[int] = mapped_column(db.Integer, default=1, nullable=False)

    # Legacy free-text placement. Superseded by `zone_id`; kept as a display
    # fallback for rows the backfill could not match.
    location: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)

    # Where the beacon is physically mounted — one place, so a column rather than
    # a join table. Note this is a different relationship from BeaconAssignment:
    # that answers "who uses this" (genuinely many-to-many with departments),
    # this answers "where is it bolted". Folding zone_id into BeaconAssignment
    # would also have forced dropping and recreating its uq_beacon_dept
    # constraint.
    zone_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey('zones.id', ondelete='SET NULL'), nullable=True
    )

    description: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(db.Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    zone: Mapped[Optional["Zone"]] = relationship('Zone', backref='beacons')

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

    # Free-text label kept as the display name and as the backfill source for
    # class_id. Superseded by the class relationship -- read class_id when
    # scoping, group_name only for display.
    group_name: Mapped[str] = mapped_column(db.String(100), nullable=False)

    # Nullable so children imported before classes existed still load; those
    # rows are simply invisible to teacher-scoped roster queries until assigned.
    class_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey('sunday_school_classes.id', ondelete='SET NULL'), nullable=True
    )

    photo_url: Mapped[Optional[str]] = mapped_column(db.String(512), nullable=True)
    is_active: Mapped[bool] = mapped_column(db.Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    sunday_class: Mapped[Optional["SundaySchoolClass"]] = relationship(
        'SundaySchoolClass', backref=db.backref('children', lazy=True)
    )

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




class OrgSettings(db.Model):
    """Tenant-wide attendance defaults.

    Exactly one row per tenant schema (id == 1) — use OrgSettings.get() rather
    than querying directly, so a tenant that predates this table still resolves
    to sane defaults instead of None.

    These are DEFAULTS. Where an employee carries a manager-set override the
    override wins; see helpers/shift_calc_helper.py for the resolution order.
    """
    __tablename__ = 'org_settings'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, default=1)

    # --- Check-in window ---
    # Hours after shift start when clock-in closes. Applies to any employee
    # without a manager-set checkin_cutoff_hour override.
    checkin_cutoff_hours_after_start: Mapped[int] = mapped_column(
        db.Integer, default=5, server_default='5', nullable=False
    )

    # --- Reminders ---
    # Delivered by the reminder job runner (jobs/reminder_job.py), which is a
    # separate process — nothing here fires on its own.
    reminder_enabled: Mapped[bool] = mapped_column(
        db.Boolean, default=False, server_default='false', nullable=False
    )
    # How long before an employee's cutoff to nudge them to clock in.
    reminder_minutes_before_cutoff: Mapped[int] = mapped_column(
        db.Integer, default=30, server_default='30', nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), db.ForeignKey('employees.id', ondelete='SET NULL'), nullable=True
    )

    editor: Mapped[Optional["Employee"]] = relationship('Employee', foreign_keys=[updated_by])

    # Fallback used when the table has no row yet, so cutoff resolution never
    # depends on the row having been created first.
    DEFAULT_CUTOFF_HOURS_AFTER_START = 5

    @classmethod
    def get(cls) -> "OrgSettings":
        """Return this tenant's settings row, creating it on first access."""
        settings = cls.query.get(1)
        if settings is None:
            settings = cls(id=1)
            db.session.add(settings)
            db.session.commit()
        return settings

    def __repr__(self) -> str:
        return f"<OrgSettings cutoff=+{self.checkin_cutoff_hours_after_start}h reminders={self.reminder_enabled}>"


class SundaySchoolClass(db.Model):
    """A Sunday School class (age group). Children belong to one; teachers are
    assigned to one or more via ClassTeacher."""
    __tablename__ = 'sunday_school_classes'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(db.String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(db.Boolean, default=True, server_default='true', nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    def __repr__(self) -> str:
        return f"<SundaySchoolClass {self.name}>"


class ClassTeacher(db.Model):
    """Assigns a teacher (Employee) to a Sunday School class.

    Many-to-many on purpose: a class can be co-taught, and a teacher can cover
    more than one class. Scoping the roster to a teacher means going through
    this table -- a teacher sees only the children in classes they are assigned
    to, never the whole church roster.
    """
    __tablename__ = 'class_teachers'

    class_id: Mapped[int] = mapped_column(
        db.Integer, db.ForeignKey('sunday_school_classes.id', ondelete='CASCADE'), primary_key=True
    )
    teacher_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), db.ForeignKey('employees.id', ondelete='CASCADE'), primary_key=True
    )
    is_lead: Mapped[bool] = mapped_column(db.Boolean, default=False, server_default='false', nullable=False)
    assigned_at: Mapped[datetime] = mapped_column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    sunday_class: Mapped["SundaySchoolClass"] = relationship(
        'SundaySchoolClass', backref=db.backref('teacher_links', lazy=True, cascade="all, delete-orphan")
    )
    teacher: Mapped["Employee"] = relationship(
        'Employee', backref=db.backref('class_links', lazy=True, cascade="all, delete-orphan")
    )

    def __repr__(self) -> str:
        return f"<ClassTeacher class={self.class_id} teacher={self.teacher_id}>"
