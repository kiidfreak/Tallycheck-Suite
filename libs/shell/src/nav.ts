import { RoleKey, hasPermission } from '@omni/auth';

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

/** Permission-aware navigation — builds sidebar groups based on role permissions. */
export function navForRole(role: RoleKey): NavGroup[] {
  const can = (p: Parameters<typeof hasPermission>[1]) => hasPermission(role, p);
  const groups: NavGroup[] = [];

  // ─── Workspace (everyone) ─────────────────────────────────────
  const workspace: NavItem[] = [
    { id: 'home', label: 'Home', icon: 'house' },
  ];
  if (can('clock:in_out') && role !== 'super_admin' && role !== 'it_admin') {
    workspace.push({ id: 'attendance-records', label: 'My Attendance', icon: 'calendar' });
  }
  if (can('manage:organizations')) {
    workspace.push({ id: 'organizations', label: 'Organizations', icon: 'building-2' });
  }
  if (can('view:departments')) {
    workspace.push({ id: 'departments', label: 'Departments', icon: 'building' });
  }
  groups.push({ label: 'Workspace', items: workspace });

  // ─── HR & People (corporate admins, IT, managers) ──────────────
  if (can('view:employees') || can('edit:attendance') || can('manage:beacons') || can('view:reports')) {
    const hrItems: NavItem[] = [];
    if (can('view:all_attendance') || can('view:team_attendance')) {
      hrItems.push({ id: 'team', label: 'Attendance', icon: 'user-check' });
    }
    if (can('view:employees')) {
      hrItems.push({ id: 'employees', label: 'Employees', icon: 'users' });
    }
    if (can('manage:beacons')) {
      hrItems.push({ id: 'beacons', label: 'BLE Beacons', icon: 'bluetooth' });
    }
    if (can('view:reports')) {
      hrItems.push({ id: 'reports', label: 'Reports', icon: 'chart-column' });
    }
    if (hrItems.length > 0) {
      groups.push({ label: 'HR & People', items: hrItems });
    }
  }

  // ─── SafeChild (education + community) ────────────────────────
  if (can('safechild:drop_off') || can('safechild:view_roster') || can('safechild:my_children')) {
    const safeChildItems: NavItem[] = [];
    if (can('safechild:drop_off') || can('safechild:manage_children')) {
      safeChildItems.push({ id: 'safechild', label: 'Class Check-in', icon: 'shield-check' });
    }
    if (can('safechild:my_children')) {
      safeChildItems.push({ id: 'safechild', label: 'My Children & Passes', icon: 'user-check' });
    }
    if (can('view:reports') || can('safechild:drop_off')) {
      safeChildItems.push({ id: 'reports', label: 'Attendance Reports', icon: 'chart-column' });
    }
    if (safeChildItems.length > 0) {
      groups.push({
        label: 'Sunday School',
        items: safeChildItems,
      });
    }
  }

  // ─── Administration (platform / IT) ───────────────────────────
  if (can('manage:users_roles') || can('manage:settings') || can('view:audit_log')) {
    const adminItems: NavItem[] = [];
    if (can('manage:users_roles')) {
      adminItems.push({ id: 'employees', label: 'Users & Roles', icon: 'user-cog' });
    }
    if (can('manage:settings')) {
      adminItems.push({ id: 'settings', label: 'Settings', icon: 'settings' });
    }
    if (can('view:audit_log')) {
      adminItems.push({ id: 'audit', label: 'Audit Log', icon: 'shield-alert' });
    }
    if (adminItems.length > 0) {
      groups.push({ label: 'Administration', items: adminItems });
    }
  }

  return groups;
}
