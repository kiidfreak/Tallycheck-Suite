// Role model — ported from the ROLES map in the prototype's index.html
// and DEMO_ACCOUNTS in LoginView.jsx.

export type RoleKey = 'staff' | 'hr' | 'manager' | 'super_admin' | 'call_centre_agent' | 'call_centre_admin';

export interface UserProfile {
  first_name: string;
  name: string;
  role: string; // human-readable role/department line
  initials: string;
  tone: '' | 'success' | 'warning' | 'purple';
  standard_shift?: string;
  shift_type?: 'standard' | 'extended';
  shift_hours?: '7am-5pm' | '9am-7pm' | '7am-430pm' | '9am-630pm' | 'custom';
  shift_duration_hours?: number;
  custom_shift_start?: string;
  custom_shift_end?: string;
}

export const ROLES: Record<RoleKey, UserProfile> = {
  staff: { first_name: 'Staff', name: 'Staff User', role: 'Staff · Engineering', initials: 'ST', tone: 'success' },
  hr: { first_name: 'HR', name: 'HR User', role: 'HR · People Operations', initials: 'HR', tone: 'warning' },
  manager: { first_name: 'Manager', name: 'Manager User', role: 'Manager · Engineering', initials: 'MG', tone: '' },
  super_admin: { first_name: 'Admin', name: 'Super Admin', role: 'Super Admin · Executive', initials: 'AD', tone: 'success' },
  call_centre_agent: { first_name: 'Agent', name: 'CC Agent', role: 'Call Centre Agent', initials: 'AG', tone: 'success' },
  call_centre_admin: { first_name: 'CC', name: 'CC Admin', role: 'Call Centre Admin', initials: 'CA', tone: 'purple' },
};

export interface DemoAccount {
  email: string;
  role: RoleKey;
  label: string;
}

export const DEMO_ACCOUNTS: DemoAccount[] = [
  { email: 'clinton@adept.co.ke', role: 'staff', label: 'Staff' },
  { email: 'kelvin@adept.co.ke', role: 'hr', label: 'HR' },
  { email: 'william@adept.co.ke', role: 'manager', label: 'Manager' },
  { email: 'mary@adept.co.ke', role: 'super_admin', label: 'Super Admin' },
  { email: 'edwin@adept.co.ke', role: 'call_centre_agent', label: 'Agent' },
  { email: 'caroline@adept.co.ke', role: 'call_centre_admin', label: 'CC Admin' },
];

export const DEMO_PASSWORD = 'adept';

/** Which route ids each role may access — ported from the allow-list in index.html. */
const COMM = ['communication', 'communication/chat', 'communication/email'];
export const ROLE_ACCESS: Record<RoleKey, string[]> = {
  staff: ['home', ...COMM, 'ai', 'it', 'apps', 'departments'],
  hr: ['home', ...COMM, 'ai', 'it', 'apps', 'team', 'planning', 'reports', 'users', 'employees', 'departments', 'beacons', 'safechild'],
  manager: ['home', ...COMM, 'callcentre', 'ai', 'it', 'apps', 'team', 'planning', 'reports', 'departments', 'safechild'],
  super_admin: ['home', ...COMM, 'callcentre', 'ai', 'it', 'apps', 'team', 'planning', 'reports', 'users', 'employees', 'settings', 'audit', 'departments', 'beacons', 'safechild'],
  call_centre_agent: ['home', 'my-calls', 'my-qa', ...COMM, 'ai', 'it', 'apps', 'departments'],
  call_centre_admin: ['home', 'callcentre', ...COMM, 'ai', 'it', 'apps', 'agent-performance', 'qa-reports', 'forecasting', 'departments'],
};

export function canAccess(role: RoleKey, routeId: string): boolean {
  return (ROLE_ACCESS[role] ?? ROLE_ACCESS.staff).includes(routeId);
}
