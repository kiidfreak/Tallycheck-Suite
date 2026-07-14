// Role model — TallyCheck Corporate + Education + Church/Sunday School.
// Supports permission-based gating via PERMISSION_MATRIX.

// ─── Role Keys ───────────────────────────────────────────────────────
export type RoleKey =
  | 'staff'                  // Regular employee / student
  | 'company_admin'          // Company-level admin
  | 'hr_admin'               // HR / People Ops
  | 'department_manager'     // Line manager / Head of Department
  | 'school_admin'           // University / School Admin
  | 'lecturer'               // University lecturer
  | 'teacher'                // Sunday School / Daycare teacher (SafeChild)
  | 'guardian'               // Parent / Authorized pickup person (SafeChild)
  | 'super_admin'            // Platform / Tenant super admin
  | 'it_admin';              // IT / System support

// ─── Role Configuration ─────────────────────────────────────────────
export type RoleCategory = 'corporate' | 'education' | 'community' | 'platform';

export interface RoleConfig {
  label: string;
  category: RoleCategory;
}

export const ROLES_CONFIG: Record<RoleKey, RoleConfig> = {
  staff:              { label: 'Company Staff',           category: 'corporate' },
  company_admin:      { label: 'Company Admin',           category: 'corporate' },
  hr_admin:           { label: 'HR Administrator',        category: 'corporate' },
  department_manager: { label: 'Department Manager',      category: 'corporate' },
  school_admin:       { label: 'School / University Admin', category: 'education' },
  lecturer:           { label: 'Lecturer',                category: 'education' },
  teacher:            { label: 'Sunday School Teacher',   category: 'community' },
  guardian:           { label: 'Parent / Guardian',       category: 'community' },
  super_admin:        { label: 'Platform Super Admin',    category: 'platform' },
  it_admin:           { label: 'IT Administrator',        category: 'platform' },
};

// ─── Role Options (for dropdowns, role assignment UIs) ───────────────
export const ROLE_OPTIONS: { value: RoleKey; label: string; category: string }[] = [
  { value: 'staff',              label: 'Company Staff',           category: 'Corporate' },
  { value: 'company_admin',      label: 'Company Admin',           category: 'Corporate' },
  { value: 'hr_admin',           label: 'HR Administrator',        category: 'Corporate' },
  { value: 'department_manager', label: 'Department Manager',      category: 'Corporate' },
  { value: 'school_admin',       label: 'School / University Admin', category: 'Education' },
  { value: 'lecturer',           label: 'Lecturer',                category: 'Education' },
  { value: 'teacher',            label: 'Sunday School Teacher',   category: 'Community' },
  { value: 'guardian',           label: 'Parent / Guardian',       category: 'Community' },
  { value: 'super_admin',       label: 'Platform Super Admin',    category: 'Platform' },
  { value: 'it_admin',           label: 'IT Administrator',        category: 'Platform' },
];

// ─── Permission Matrix ──────────────────────────────────────────────
// Granular action-based permissions. Use hasPermission(role, perm) in
// components, guards, and templates via auth.can('view:employees').
export type Permission =
  // Attendance
  | 'view:own_attendance'
  | 'view:team_attendance'
  | 'view:all_attendance'
  | 'clock:in_out'
  | 'edit:attendance'
  // Employees / Users
  | 'view:employees'
  | 'edit:employees'
  | 'approve:employees'
  // Departments
  | 'view:departments'
  | 'edit:departments'
  // Beacons
  | 'view:beacons'
  | 'manage:beacons'
  // Reports
  | 'view:reports'
  | 'export:reports'
  // SafeChild
  | 'safechild:view_roster'
  | 'safechild:drop_off'
  | 'safechild:pickup'
  | 'safechild:manage_children'
  // Administration
  | 'manage:users_roles'
  | 'manage:settings'
  | 'view:audit_log'
  // Provisioning (Super Admin only)
  | 'manage:organizations';

const PERMISSION_MATRIX: Record<RoleKey, Permission[]> = {
  staff: [
    'view:own_attendance', 'clock:in_out', 'view:departments',
  ],
  company_admin: [
    'view:own_attendance', 'view:all_attendance', 'clock:in_out', 'edit:attendance',
    'view:employees', 'edit:employees', 'approve:employees',
    'view:departments', 'edit:departments',
    'view:beacons', 'manage:beacons',
    'view:reports', 'export:reports',
    'manage:users_roles', 'manage:settings',
  ],
  hr_admin: [
    'view:own_attendance', 'view:all_attendance', 'clock:in_out', 'edit:attendance',
    'view:employees', 'edit:employees', 'approve:employees',
    'view:departments', 'edit:departments',
    'view:beacons', 'manage:beacons',
    'view:reports', 'export:reports',
    'safechild:view_roster', 'safechild:drop_off', 'safechild:pickup',
  ],
  department_manager: [
    'view:own_attendance', 'view:team_attendance', 'clock:in_out', 'edit:attendance',
    'view:employees',
    'view:departments',
    'view:reports',
    'safechild:view_roster', 'safechild:drop_off', 'safechild:pickup',
  ],
  school_admin: [
    'view:own_attendance', 'view:all_attendance', 'clock:in_out', 'edit:attendance',
    'view:employees', 'edit:employees', 'approve:employees',
    'view:departments', 'edit:departments',
    'view:reports', 'export:reports',
    'safechild:view_roster', 'safechild:drop_off', 'safechild:pickup', 'safechild:manage_children',
    'manage:users_roles', 'manage:settings',
  ],
  lecturer: [
    'view:own_attendance', 'clock:in_out',
    'view:departments',
    'view:reports',
  ],
  teacher: [
    'view:own_attendance', 'clock:in_out',
    'safechild:view_roster', 'safechild:drop_off', 'safechild:pickup', 'safechild:manage_children',
  ],
  guardian: [
    'safechild:view_roster', 'safechild:drop_off', 'safechild:pickup',
  ],
  super_admin: [
    // Super admin has ALL permissions
    'view:own_attendance', 'view:team_attendance', 'view:all_attendance',
    'clock:in_out', 'edit:attendance',
    'view:employees', 'edit:employees', 'approve:employees',
    'view:departments', 'edit:departments',
    'view:beacons', 'manage:beacons',
    'view:reports', 'export:reports',
    'safechild:view_roster', 'safechild:drop_off', 'safechild:pickup', 'safechild:manage_children',
    'manage:users_roles', 'manage:settings', 'view:audit_log',
    'manage:organizations',
  ],
  it_admin: [
    'view:beacons', 'manage:beacons',
    'manage:settings', 'view:audit_log',
    'manage:users_roles',
  ],
};

/** Check if a role has a specific permission. */
export function hasPermission(role: RoleKey, permission: Permission): boolean {
  return PERMISSION_MATRIX[role]?.includes(permission) ?? false;
}

// ─── User Profile (demo / display) ──────────────────────────────────
export interface UserProfile {
  first_name: string;
  name: string;
  role: string;           // Display label
  department?: string;
  initials: string;
  tone: 'success' | 'warning' | 'purple' | 'danger' | 'info' | '';
  avatar?: string;
  standard_shift?: string;
  shift_type?: 'standard' | 'extended' | 'flexible';
  shift_hours?: string;
  shift_duration_hours?: number;
  custom_shift_start?: string;
  custom_shift_end?: string;
}

export const ROLES: Record<RoleKey, UserProfile> = {
  staff: {
    first_name: 'John',
    name: 'John Doe',
    role: 'Software Engineer',
    department: 'Engineering',
    initials: 'JD',
    tone: 'success',
    shift_hours: '8am-5pm'
  },
  company_admin: {
    first_name: 'David',
    name: 'David Njoroge',
    role: 'Company Administrator',
    department: 'Executive',
    initials: 'DN',
    tone: 'warning'
  },
  hr_admin: {
    first_name: 'Mercy',
    name: 'Mercy Wambui',
    role: 'HR Manager',
    department: 'People Operations',
    initials: 'MW',
    tone: 'warning'
  },
  department_manager: {
    first_name: 'William',
    name: 'William Kamau',
    role: 'Engineering Manager',
    department: 'Engineering',
    initials: 'WK',
    tone: ''
  },
  school_admin: {
    first_name: 'Prof. Anne',
    name: 'Prof. Anne Maina',
    role: 'University Administrator',
    department: 'Academic Affairs',
    initials: 'AM',
    tone: 'info'
  },
  super_admin: {
    first_name: 'Admin',
    name: 'Super Admin',
    role: 'Platform Administrator',
    department: 'Executive',
    initials: 'SA',
    tone: 'success'
  },
  lecturer: {
    first_name: 'Dr. Jane',
    name: 'Dr. Jane Muthoni',
    role: 'Senior Lecturer',
    department: 'Computer Science',
    initials: 'JM',
    tone: 'info'
  },
  teacher: {
    first_name: 'Pastor',
    name: 'Pastor Esther Njeri',
    role: 'Sunday School Teacher',
    department: 'Children Ministry',
    initials: 'EN',
    tone: 'purple'
  },
  guardian: {
    first_name: 'Grace',
    name: 'Grace Wanjiku',
    role: 'Parent / Guardian',
    department: 'Daystar Church',
    initials: 'GW',
    tone: 'info'
  },
  it_admin: {
    first_name: 'Kelvin',
    name: 'Kelvin Omondi',
    role: 'IT Administrator',
    department: 'Technology',
    initials: 'KO',
    tone: 'warning'
  }
};

// ─── Demo Accounts ──────────────────────────────────────────────────
export interface DemoAccount {
  email: string;
  role: RoleKey;
  label: string;
}

export const DEMO_ACCOUNTS: DemoAccount[] = [
  { email: 'john@acme.tallycheck.co.ke',     role: 'staff',              label: 'Staff' },
  { email: 'david@acme.tallycheck.co.ke',    role: 'company_admin',      label: 'Company Admin' },
  { email: 'mercy@acme.tallycheck.co.ke',    role: 'hr_admin',           label: 'HR Admin' },
  { email: 'william@acme.tallycheck.co.ke',  role: 'department_manager', label: 'Dept Manager' },
  { email: 'anne@daystar.tallycheck.co.ke',   role: 'school_admin',       label: 'School Admin' },
  { email: 'admin@tallycheck.co.ke',          role: 'super_admin',        label: 'Super Admin' },
  { email: 'jane@daystar.tallycheck.co.ke',   role: 'lecturer',           label: 'Lecturer' },
  { email: 'esther@daystar.tallycheck.co.ke', role: 'teacher',            label: 'Teacher' },
  { email: 'grace@daystar.tallycheck.co.ke',  role: 'guardian',           label: 'Guardian' },
  { email: 'kelvin@acme.tallycheck.co.ke',    role: 'it_admin',           label: 'IT Admin' },
];

export const DEMO_PASSWORD = 'adept';

// ─── Route Access (legacy, kept for backward compat with roleGuard) ─
const COMM = ['communication', 'communication/chat', 'communication/email'];
export const ROLE_ACCESS: Record<RoleKey, string[]> = {
  staff:              ['home', ...COMM, 'departments', 'attendance'],
  company_admin:      ['*'],
  hr_admin:           ['home', ...COMM, 'team', 'planning', 'reports', 'users', 'employees', 'departments', 'beacons', 'safechild', 'attendance'],
  department_manager: ['home', ...COMM, 'team', 'planning', 'reports', 'departments', 'safechild', 'attendance'],
  school_admin:       ['*'],
  super_admin:        ['*'],
  lecturer:           ['home', 'attendance', 'departments', 'reports'],
  teacher:            ['home', 'safechild', 'children', 'attendance'],
  guardian:           ['home', 'safechild', 'my-children', 'pickup-history'],
  it_admin:           ['home', 'settings', 'audit', 'beacons'],
};

export function canAccess(role: RoleKey, routeId: string): boolean {
  const allowed = ROLE_ACCESS[role] ?? ROLE_ACCESS.staff;
  if (allowed.includes('*')) return true;
  return allowed.includes(routeId);
}
