import { Route } from '@angular/router';
import { ShellComponent } from '@omni/shell';
import { authGuard, roleGuard } from '@omni/auth';
import { PlaceholderComponent } from './features/placeholder/placeholder.component';

/** A screen still served by the generic placeholder (id drives role-gating + data). */
const placeholder = (path: string, id: string, title: string, icon: string): Route => ({
  path,
  component: PlaceholderComponent,
  canActivate: [roleGuard],
  data: { id, title, icon },
});

/**
 * TallyCheck for Business — routes.
 * /login is public; everything else renders inside the authenticated shell.
 */
export const appRoutes: Route[] = [
  {
    path: 'login',
    loadComponent: () => import('./features/login/login.component').then((m) => m.LoginComponent),
  },
  {
    path: 'onboarding',
    loadComponent: () => import('./features/onboarding/onboarding.component').then((m) => m.OnboardingComponent),
    canActivate: [authGuard],
  },
  {
    path: 'pending',
    loadComponent: () => import('./features/pending/pending.component').then((m) => m.PendingComponent),
    canActivate: [authGuard],
  },
  {
    path: '',
    component: ShellComponent,
    canActivate: [authGuard],
    children: [
      {
        path: 'home',
        loadComponent: () => import('./features/home/home.component').then((m) => m.HomeComponent),
        canActivate: [roleGuard],
        data: { id: 'home' },
      },
      {
        path: 'team',
        loadComponent: () => import('./features/team/team.component').then((m) => m.TeamComponent),
        canActivate: [roleGuard],
        data: { id: 'team', title: 'Team Attendance', icon: 'users' },
      },
      {
        path: 'attendance-records',
        loadComponent: () =>
          import('./features/attendance-records/attendance-records.component').then((m) => m.AttendanceRecordsComponent),
        canActivate: [roleGuard],
        data: { id: 'attendance-records', title: 'All Attendance', icon: 'list' },
      },
      {
        path: 'employees',
        loadComponent: () => import('./features/employees/employees.component').then((m) => m.EmployeesComponent),
        canActivate: [roleGuard],
        data: { id: 'employees', title: 'Employees', icon: 'users' },
      },
      {
        path: 'departments',
        loadComponent: () => import('./features/departments/departments.component').then((m) => m.DepartmentsComponent),
        canActivate: [roleGuard],
        data: { id: 'departments', title: 'Departments', icon: 'building' },
      },
      {
        path: 'beacons',
        loadComponent: () => import('./features/beacons/beacons.component').then((m) => m.BeaconsComponent),
        canActivate: [roleGuard],
        data: { id: 'beacons', title: 'BLE Beacons', icon: 'bluetooth' },
      },
      {
        path: 'safechild',
        loadComponent: () => import('./features/safechild/safechild.component').then((m) => m.SafechildComponent),
        canActivate: [roleGuard],
        data: { id: 'safechild', title: 'SafeChild Sunday School', icon: 'shield' },
      },
      {
        path: 'reports',
        loadComponent: () => import('./features/reports/reports.component').then((m) => m.ReportsComponent),
        canActivate: [roleGuard],
        data: { id: 'reports', title: 'Overall Reports', icon: 'chart-column' },
      },
      {
        path: 'safechild-reports',
        loadComponent: () => import('./features/reports/reports.component').then((m) => m.ReportsComponent),
        canActivate: [roleGuard],
        data: { id: 'safechild-reports', title: 'Sunday School Child Attendance Reports', icon: 'chart-column', type: 'safechild' },
      },
      {
        path: 'users-roles',
        loadComponent: () => import('./features/employees/employees.component').then((m) => m.EmployeesComponent),
        canActivate: [roleGuard],
        data: { id: 'users-roles', title: 'Users & Roles', icon: 'user-cog' },
      },
      placeholder('settings', 'settings', 'Settings', 'settings'),
      placeholder('audit', 'audit', 'Audit Log', 'shield'),
      {
        path: 'organizations',
        loadComponent: () => import('./features/organizations/organizations.component').then((m) => m.OrganizationsComponent),
        canActivate: [roleGuard],
        data: { id: 'organizations', title: 'Multi-Tenant Organizations', icon: 'building-2' },
      },
      { path: '', pathMatch: 'full', redirectTo: 'home' },
    ],
  },
  { path: '**', redirectTo: '' },
];
