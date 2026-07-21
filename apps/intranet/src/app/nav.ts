import { RoleKey, hasPermission } from '@omni/auth';
import { NavGroup, NavItem } from '@omni/shell';

/**
 * TallyCheck (tcheck) navigation.
 *
 * Lives in the app, not in @omni/shell: the shell is shared with vcheck and must
 * not know these routes. Provided to the shell via NAV_PROVIDER.
 *
 * Every id here must match a route id in app.routes.ts, otherwise the item
 * renders but navigates nowhere.
 */
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
    workspace.push({ id: 'organizations', label: 'Organization & Structure', icon: 'building-2' });
  } else if (can('view:departments')) {
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
  //
  // Staff and guardians see different labels for the same route. These branches
  // are mutually exclusive by permission: a teacher has safechild:drop_off, a
  // guardian has safechild:my_children, and no role has both. Staff wins if that
  // ever changes, so the list can never contain a duplicate id.
  if (can('safechild:drop_off') || can('safechild:view_roster') || can('safechild:my_children')) {
    const safeChildItems: NavItem[] = [];
    if (can('safechild:drop_off') || can('safechild:manage_children')) {
      safeChildItems.push({ id: 'safechild', label: 'Class Check-in', icon: 'shield-check' });
    } else if (can('safechild:my_children')) {
      safeChildItems.push({ id: 'safechild', label: 'My Children & Passes', icon: 'user-check' });
    }
    if (can('view:reports') || can('safechild:drop_off')) {
      safeChildItems.push({ id: 'safechild-reports', label: 'Attendance Reports', icon: 'chart-column' });
    }
    if (safeChildItems.length > 0) {
      groups.push({ label: 'Sunday School', items: safeChildItems });
    }
  }

  // ─── Administration (platform / IT) ───────────────────────────
  if (can('manage:users_roles') || can('manage:settings') || can('view:audit_log')) {
    const adminItems: NavItem[] = [];
    if (can('manage:users_roles')) {
      adminItems.push({ id: 'users-roles', label: 'Users & Roles', icon: 'user-cog' });
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
