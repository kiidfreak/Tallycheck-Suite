/**
 * Canned API responses for demo mode.
 *
 * Shapes mirror the real backend exactly, including the SuccessResponse
 * envelope where the backend uses one, so components need no demo-specific
 * branching. If a payload shape changes on the server, change it here too.
 */

const today = () => new Date().toISOString().slice(0, 10);

function at(hour: number, minute = 0): string {
  const d = new Date();
  d.setHours(hour, minute, 0, 0);
  return d.toISOString();
}

function days_ago(n: number): string {
  const d = new Date();
  d.setDate(d.getDate() - n);
  return d.toISOString().slice(0, 10);
}

export const DEMO_ORGANIZATIONS = [
  {
    id: 'org_0D0uiOBBi91ZiW0v',
    name: 'Daystar University',
    domain: 'daystar',
    schema_name: 'tenant_org_0d0uiobbi91ziw0v',
    is_active: true,
    org_type: 'education',
    admin_email: 'anne@daystar.ac.ke',
    created_at: '2026-07-01'
  },
  {
    id: 'org_strathmore_su_2026',
    name: 'Strathmore University (SCES)',
    domain: 'strathmore',
    schema_name: 'tenant_strathmore',
    is_active: true,
    org_type: 'education',
    admin_email: 'cmkaburu@strathmore.edu',
    created_at: '2026-07-05'
  },
  {
    id: 'org_secureguard_2026',
    name: 'SecureGuard Security Systems',
    domain: 'secureguard',
    schema_name: 'tenant_secureguard',
    is_active: true,
    org_type: 'corporate',
    admin_email: 'ops@secureguard.co.ke',
    created_at: '2026-07-08'
  },
  {
    id: 'org_fem_karen_church_2026',
    name: 'FEM Church Karen (Sunday School)',
    domain: 'femkaren',
    schema_name: 'tenant_femkaren',
    is_active: true,
    org_type: 'education',
    admin_email: 'tr.alice@femkaren.org',
    created_at: '2026-07-12'
  },
  {
    id: 'org_acme_corp',
    name: 'Acme Corporate Enterprise',
    domain: 'acme',
    schema_name: 'tenant_acme',
    is_active: true,
    org_type: 'corporate',
    admin_email: 'david@acme.com',
    created_at: '2026-07-15'
  }
];

export const DEMO_DEPARTMENTS = [
  { id: 1, name: 'school_of_science_engineering_and_technology', manager_id: null, parent_department_id: null },
  { id: 2, name: 'school_of_communication_languages_and_performing_arts', manager_id: null, parent_department_id: null },
  { id: 3, name: 'school_of_business_and_economics', manager_id: null, parent_department_id: null },
  { id: 4, name: 'school_of_law', manager_id: null, parent_department_id: null },
  { id: 5, name: 'school_of_nursing', manager_id: null, parent_department_id: null },
  { id: 6, name: 'security_operations_and_patrols', manager_id: null, parent_department_id: null },
  { id: 7, name: 'fem_church_karen_children_ministry', manager_id: null, parent_department_id: null },
];

export const DEMO_ROLES = [
  { id: 1, name: 'staff', role: 'staff' },
  { id: 2, name: 'company_admin', role: 'company_admin' },
  { id: 3, name: 'hr_admin', role: 'hr_admin' },
  { id: 4, name: 'department_manager', role: 'department_manager' },
  { id: 5, name: 'school_admin', role: 'school_admin' },
  { id: 6, name: 'lecturer', role: 'lecturer' },
  { id: 7, name: 'teacher', role: 'teacher' },
  { id: 8, name: 'guardian', role: 'guardian' },
  { id: 9, name: 'super_admin', role: 'super_admin' },
  { id: 10, name: 'it_admin', role: 'it_admin' },
];

export const DEMO_EMPLOYEES = [
  { id: 'e1', first_name: 'Anne', last_name: 'Kamau', email: 'anne@daystar.ac.ke', role_name: 'school_admin', department_name: 'school_of_science_engineering_and_technology', is_active: true, is_approved: true, is_manager: true, shift_hours: '7am-5pm', shift_type: 'standard' },
  { id: 'e2', first_name: 'Caroline', last_name: 'Kaburu', email: 'cmkaburu@strathmore.edu', role_name: 'school_admin', department_name: 'school_of_science_engineering_and_technology', is_active: true, is_approved: true, is_manager: true, shift_hours: '8am-5pm', shift_type: 'standard' },
  { id: 'e3', first_name: 'Tr. Alice', last_name: 'Wambui', email: 'tr.alice@femkaren.org', role_name: 'teacher', department_name: 'fem_church_karen_children_ministry', is_active: true, is_approved: true, is_manager: false, shift_hours: '7am-5pm', shift_type: 'standard' },
  { id: 'e4', first_name: 'Kelvin', last_name: 'Omondi', email: 'kelvin@secureguard.co.ke', role_name: 'department_manager', department_name: 'security_operations_and_patrols', is_active: true, is_approved: true, is_manager: true, shift_hours: '7am-5pm', shift_type: 'standard' },
  { id: 'e5', first_name: 'Albert', last_name: 'Einstein', email: 'albert@daystar.ac.ke', role_name: 'lecturer', department_name: 'school_of_science_engineering_and_technology', is_active: true, is_approved: true, is_manager: false, shift_hours: '7am-5pm', shift_type: 'standard' },
  { id: 'e6', first_name: 'Marie', last_name: 'Curie', email: 'marie@daystar.ac.ke', role_name: 'lecturer', department_name: 'school_of_nursing', is_active: true, is_approved: true, is_manager: false, shift_hours: '7am-5pm', shift_type: 'standard' },
  { id: 'e7', first_name: 'Adam', last_name: 'Smith', email: 'adam@daystar.ac.ke', role_name: 'staff', department_name: 'school_of_business_and_economics', is_active: true, is_approved: true, is_manager: false, shift_hours: '9am-7pm', shift_type: 'standard' },
];

export const DEMO_ATTENDANCE_RECORDS = [
  { id: 101, employee_id: 'e1', clock_in: at(8, 2), clock_out: at(17, 5), work_date: today(), status: 'closed', source: 'web', worked_hours: 9.05, notes: null },
  { id: 102, employee_id: 'e1', clock_in: `${days_ago(1)}T08:14:00Z`, clock_out: `${days_ago(1)}T17:20:00Z`, work_date: days_ago(1), status: 'closed', source: 'web', worked_hours: 9.1, notes: null },
  { id: 103, employee_id: 'e1', clock_in: `${days_ago(2)}T07:58:00Z`, clock_out: `${days_ago(2)}T16:47:00Z`, work_date: days_ago(2), status: 'closed', source: 'mobile', worked_hours: 8.8, notes: null },
  { id: 104, employee_id: 'e1', clock_in: `${days_ago(3)}T08:31:00Z`, clock_out: `${days_ago(3)}T17:02:00Z`, work_date: days_ago(3), status: 'closed', source: 'web', worked_hours: 8.5, notes: null },
  { id: 105, employee_id: 'e1', clock_in: `${days_ago(4)}T08:05:00Z`, clock_out: `${days_ago(4)}T17:11:00Z`, work_date: days_ago(4), status: 'closed', source: 'web', worked_hours: 9.1, notes: null },
];

export const DEMO_ATTENDANCE_STATS = {
  hours_this_week: 34.5,
  team_total: 12,
  team_present: 9,
  streak: 5,
};

const GUARDIANS = {
  grace: { id: 'g1', name: 'Grace Wanjiru', phone: '+254712345601', relation: 'Mother', is_primary: true, photo_url: null },
  peter: { id: 'g2', name: 'Peter Wanjiru', phone: '+254712345602', relation: 'Father', is_primary: false, photo_url: null },
  mercy: { id: 'g3', name: 'Mercy Otieno', phone: '+254712345603', relation: 'Mother', is_primary: true, photo_url: null },
  joseph: { id: 'g4', name: 'Joseph Kimani', phone: '+254712345604', relation: 'Father', is_primary: true, photo_url: null },
  sarah: { id: 'g5', name: 'Sarah Achieng', phone: '+254712345606', relation: 'Aunt', is_primary: true, photo_url: null },
  lucy: { id: 'g6', name: 'Lucy Njeri', phone: '+254712345608', relation: 'Mother', is_primary: true, photo_url: null },
  david: { id: 'g7', name: 'David Mwangi', phone: '+254712345610', relation: 'Father', is_primary: true, photo_url: null },
  ann: { id: 'g8', name: 'Ann Mutua', phone: '+254712345612', relation: 'Mother', is_primary: true, photo_url: null },
};

export const DEMO_CHILDREN = [
  // Class 1: Hekima (Wisdom - Ages 3-5)
  { id: 'c1', name: 'Amani Wanjiru', group_name: 'Hekima Class (3-5 yrs)', class_id: 1, class_name: 'Hekima Class (3-5 yrs)', photo_url: null, is_active: true, status: 'checked_in', check_in_time: at(9, 12), guardians: [GUARDIANS.grace, GUARDIANS.peter] },
  { id: 'c2', name: 'Baraka Otieno', group_name: 'Hekima Class (3-5 yrs)', class_id: 1, class_name: 'Hekima Class (3-5 yrs)', photo_url: null, is_active: true, status: 'absent', check_in_time: null, guardians: [GUARDIANS.mercy] },
  
  // Class 2: Imani (Faith - Ages 6-8)
  { id: 'c3', name: 'Zawadi Kimani', group_name: 'Imani Class (6-8 yrs)', class_id: 2, class_name: 'Imani Class (6-8 yrs)', photo_url: null, is_active: true, status: 'checked_in', check_in_time: at(9, 5), guardians: [GUARDIANS.joseph] },
  { id: 'c4', name: 'Neema Achieng', group_name: 'Imani Class (6-8 yrs)', class_id: 2, class_name: 'Imani Class (6-8 yrs)', photo_url: null, is_active: true, status: 'absent', check_in_time: null, guardians: [GUARDIANS.sarah] },

  // Class 3: Busara (Prudence - Ages 9-11)
  { id: 'c5', name: 'Tumaini Njeri', group_name: 'Busara Class (9-11 yrs)', class_id: 3, class_name: 'Busara Class (9-11 yrs)', photo_url: null, is_active: true, status: 'checked_in', check_in_time: at(9, 22), guardians: [GUARDIANS.lucy] },
  { id: 'c6', name: 'Jabari Mwangi', group_name: 'Busara Class (9-11 yrs)', class_id: 3, class_name: 'Busara Class (9-11 yrs)', photo_url: null, is_active: true, status: 'absent', check_in_time: null, guardians: [GUARDIANS.david] },

  // Class 4: Upendo (Love - Ages 12-14)
  { id: 'c7', name: 'Faraja Mutua', group_name: 'Upendo Class (12-14 yrs)', class_id: 4, class_name: 'Upendo Class (12-14 yrs)', photo_url: null, is_active: true, status: 'checked_in', check_in_time: at(9, 30), guardians: [GUARDIANS.ann] },
];

export const DEMO_MY_CLASSES = [
  { id: 1, name: 'Hekima Class (3-5 yrs)', description: 'Kiswahili Hekima - Ages 3 to 5', child_count: 2 },
  { id: 2, name: 'Imani Class (6-8 yrs)', description: 'Kiswahili Imani - Ages 6 to 8', child_count: 2 },
  { id: 3, name: 'Busara Class (9-11 yrs)', description: 'Kiswahili Busara - Ages 9 to 11', child_count: 2 },
  { id: 4, name: 'Upendo Class (12-14 yrs)', description: 'Kiswahili Upendo - Ages 12 to 14', child_count: 1 },
];

export const DEMO_CLASS_HISTORY = [
  { id: 't1', child_id: 'c1', child_name: 'Amani Wanjiru', class_name: 'Hekima Class (3-5 yrs)', guardian_name: 'Grace Wanjiru', dropped_off_at: at(9, 12), picked_up_at: null, status: 'pending' },
  { id: 't2', child_id: 'c2', child_name: 'Baraka Otieno', class_name: 'Hekima Class (3-5 yrs)', guardian_name: 'Mercy Otieno', dropped_off_at: `${days_ago(7)}T09:03:00Z`, picked_up_at: `${days_ago(7)}T12:10:00Z`, status: 'verified' },
  { id: 't3', child_id: 'c3', child_name: 'Zawadi Kimani', class_name: 'Imani Class (6-8 yrs)', guardian_name: 'Joseph Kimani', dropped_off_at: `${days_ago(14)}T09:15:00Z`, picked_up_at: `${days_ago(14)}T12:05:00Z`, status: 'verified' },
];

export const DEMO_BEACONS = [
  { id: 'b1', name: 'Science Lab 2', mac_address: 'AA:BB:CC:DD:EE:01', uuid: 'f7826da6-4fa2-4e98-8024-bc5b71e0893e', major: 1, minor: 1, location: 'Science Block', description: 'Lab 2 entrance', is_active: true },
  { id: 'b2', name: 'Lecture Hall 4', mac_address: 'AA:BB:CC:DD:EE:02', uuid: 'f7826da6-4fa2-4e98-8024-bc5b71e0893e', major: 1, minor: 2, location: 'Main Block', description: 'Hall 4', is_active: true },
  { id: 'b3', name: 'Church Hall', mac_address: 'AA:BB:CC:DD:EE:03', uuid: 'f7826da6-4fa2-4e98-8024-bc5b71e0893e', major: 2, minor: 1, location: 'Daystar Church', description: 'Sunday School wing', is_active: true },
  { id: 'b4', name: 'Security Main Gate', mac_address: 'AA:BB:CC:DD:EE:04', uuid: 'f7826da6-4fa2-4e98-8024-bc5b71e0893e', major: 3, minor: 1, location: 'Main Gate Barrier', description: 'Security Patrol Checkpoint', is_active: true },
];

export const DEMO_DASHBOARD_METRICS = {
  total_employees: 7,
  present_today: 5,
  absent_today: 2,
  late_today: 1,
  average_hours: 8.7,
  pending_corrections: 0,
};

export const DEMO_ORG_SETTINGS = {
  checkin_cutoff_hours_after_start: 5,
  reminder_enabled: false,
  reminder_minutes_before_cutoff: 30,
  updated_at: at(6, 0),
  updated_by: null,
};

export const DEMO_ATTENDANCE_TREND = Array.from({ length: 14 }, (_, i) => ({
  date: days_ago(13 - i),
  present: 4 + ((i * 7) % 3),
  absent: 1 + (i % 2),
  late: i % 3 === 0 ? 1 : 0,
}));

export const DEMO_DEPARTMENT_REPORT = DEMO_DEPARTMENTS.slice(0, 6).map((d, i) => ({
  department_id: d.id,
  department_name: d.name,
  employee_count: 2 + ((i * 3) % 4),
  present: 1 + (i % 3),
  average_hours: 7.5 + ((i * 3) % 5) / 2,
  attendance_rate: 75 + ((i * 11) % 20),
}));
