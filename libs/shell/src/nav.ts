import { RoleKey } from '@omni/auth';

export interface NavItem {
  id: string; // route id, e.g. 'home', 'my-calls'
  label: string;
  icon: string; // lucide name
  badge?: number;
  expandable?: boolean; // Communication group
}

export interface NavGroup {
  label: string;
  items: NavItem[];
}

export const COMM_SUBITEMS: NavItem[] = [
  { id: 'communication', label: 'Announcements', icon: 'megaphone' },
  { id: 'communication/chat', label: 'Chat', icon: 'message-circle' },
  { id: 'communication/email', label: 'Email', icon: 'mail' },
];

/** Role-aware navigation — trimmed to the TallyCheck attendance/HR surface. */
export function navForRole(role: RoleKey): NavGroup[] {
  const workspace: NavItem[] = [
    { id: 'home', label: 'Home', icon: 'house' },
    { id: 'departments', label: 'Departments', icon: 'building' },
  ];

  const groups: NavGroup[] = [{ label: 'Workspace', items: workspace }];

  if (role === 'hr') {
    groups.push({
      label: 'HR',
      items: [
        { id: 'team', label: 'Attendance', icon: 'user-check' },
        { id: 'employees', label: 'Employees', icon: 'users' },
      ],
    });
  }

  if (role === 'manager' || role === 'super_admin') {
    groups.push({
      label: 'Manager',
      items: [
        { id: 'team', label: 'Team Attendance', icon: 'users' },
      ],
    });
  }

  if (role === 'super_admin') {
    groups.push({
      label: 'Admin',
      items: [
        { id: 'employees', label: 'Users & Roles', icon: 'user-cog' },
      ],
    });
  }

  return groups;
}

export const ROLE_OPTIONS: { value: RoleKey; label: string }[] = [
  { value: 'staff', label: 'Staff' },
  { value: 'hr', label: 'HR' },
  { value: 'manager', label: 'Manager' },
  { value: 'super_admin', label: 'Super Admin' },
];
