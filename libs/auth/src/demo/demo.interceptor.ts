import { HttpInterceptorFn, HttpResponse } from '@angular/common/http';
import { of, delay } from 'rxjs';
import { is_demo_mode } from './demo-mode';
import {
  DEMO_ATTENDANCE_RECORDS,
  DEMO_ATTENDANCE_STATS,
  DEMO_ATTENDANCE_TREND,
  DEMO_BEACONS,
  DEMO_BEACON_ASSIGNMENTS,
  DEMO_CHILDREN,
  DEMO_CLASS_HISTORY,
  DEMO_DASHBOARD_METRICS,
  DEMO_DEPARTMENTS,
  DEMO_DEPARTMENT_REPORT,
  DEMO_EMPLOYEES,
  DEMO_MY_CLASSES,
  DEMO_ORGANIZATIONS,
  DEMO_ORG_SETTINGS,
  DEMO_ROLES,
} from './demo-data';

/** Backend SuccessResponse envelope, so components need no demo-specific branching. */
function envelope(data: unknown, message = 'Success') {
  return { status: 'success', message, data };
}

/**
 * Answers API calls from canned data when demo mode is on.
 *
 * Must be registered FIRST in the interceptor chain -- it short-circuits before
 * authInterceptor and Auth0's interceptor can try to attach a token, which is
 * what would otherwise force a login round-trip against a backend that is not
 * deployed.
 *
 * Writes (POST/PUT/DELETE) are acknowledged but not persisted: a demo reload
 * returns to the same starting state, which is what you want when several
 * people are clicking through the same URL.
 */
export const demoInterceptor: HttpInterceptorFn = (req, next) => {
  if (!is_demo_mode()) return next(req);

  const url = req.url.split('?')[0];
  const path = url.replace(/^.*\/api\/v2/, '') || url;
  const method = req.method.toUpperCase();

  const ok = (body: unknown) =>
    // Small delay so loading states are actually visible in a demo.
    of(new HttpResponse({ status: 200, body })).pipe(delay(180));

  // --- Auth ---
  if (path.startsWith('/auth/organization-by-subdomain')) {
    return ok(envelope({ id: 'org_demo', name: 'Daystar University', domain: 'daystar', schema_name: 'tenant_org_demo', is_active: true }));
  }
  if (path.startsWith('/auth/metadata')) {
    return ok(envelope({ roles: DEMO_ROLES, departments: DEMO_DEPARTMENTS }));
  }
  if (path.startsWith('/auth/users/pending')) return ok(envelope([]));
  if (path.startsWith('/auth/me') || path.startsWith('/auth/profile') || path.startsWith('/auth/sync') || path.startsWith('/auth/register')) {
    return ok(envelope(DEMO_EMPLOYEES[0]));
  }

  // --- Attendance ---
  if (path.startsWith('/attendance/stats')) return ok(envelope(DEMO_ATTENDANCE_STATS));
  if (path.startsWith('/attendance/me')) {
    return ok({
      status: 'success',
      message: 'Success',
      data: DEMO_ATTENDANCE_RECORDS,
      meta: { page: 1, per_page: 10, total: DEMO_ATTENDANCE_RECORDS.length, pages: 1 },
    });
  }
  if (path.startsWith('/attendance/clock-in')) {
    return ok(envelope({ record: { ...DEMO_ATTENDANCE_RECORDS[0], clock_out: null, status: 'open' } }, 'Checked in successfully.'));
  }
  if (path.startsWith('/attendance/clock-out')) {
    return ok(envelope({ record: DEMO_ATTENDANCE_RECORDS[0] }, 'Checked out. Worked 9.05 hours.'));
  }
  if (path.startsWith('/attendance')) return ok(envelope(DEMO_ATTENDANCE_RECORDS));

  // --- SafeChild ---
  if (path.startsWith('/safechild/my-classes')) return ok(envelope(DEMO_MY_CLASSES));
  if (path.startsWith('/safechild/class-history')) return ok(envelope(DEMO_CLASS_HISTORY));
  if (path.startsWith('/safechild/children')) return ok(envelope(DEMO_CHILDREN));
  if (path.startsWith('/safechild/drop-off')) {
    return ok(envelope({
      token_id: 'demo-token',
      child_name: 'Amani Wanjiru',
      pin: '4821',
      qr_payload: 'demo-token.demosignature',
      expires_at: new Date(Date.now() + 8 * 3600_000).toISOString(),
    }, 'Child drop-off logged successfully'));
  }
  if (path.startsWith('/safechild/pickup/verify')) {
    // 4821 is the PIN the demo drop-off hands out; anything else should fail,
    // so the error path is demonstrable too.
    const code = (req.body as { code?: string } | null)?.code;
    if (code === '4821' || (code && code.length > 10)) {
      return ok(envelope({ child_name: 'Amani Wanjiru', guardian_name: 'Grace Wanjiru', verified_at: new Date().toISOString() }, 'Pickup verified. Child released.'));
    }
    return of(new HttpResponse({
      status: 200,
      body: { status: 'error', error: 'not_found', message: 'Invalid or unrecognized verification PIN', details: null },
    })).pipe(delay(180));
  }

  // --- Directory ---
  if (path.startsWith('/organizations')) {
    return ok(envelope(DEMO_ORGANIZATIONS));
  }
  if (path.startsWith('/departments')) return ok(envelope(DEMO_DEPARTMENTS));
  if (path.startsWith('/employees')) return ok(envelope(DEMO_EMPLOYEES));
  // Order matters: '/beacons' is a prefix of '/beacons/assignments', so the
  // specific branch has to come first or it is never reached.
  if (path.startsWith('/beacons/assignments')) return ok(envelope(DEMO_BEACON_ASSIGNMENTS));
  if (path.startsWith('/beacons')) return ok(envelope(DEMO_BEACONS));
  if (path.startsWith('/settings')) return ok(envelope(DEMO_ORG_SETTINGS));

  // --- Reports ---
  if (path.includes('/reports/dashboard')) return ok(envelope(DEMO_DASHBOARD_METRICS));
  if (path.includes('/reports/department')) return ok(envelope(DEMO_DEPARTMENT_REPORT));
  if (path.includes('/reports/trend') || path.includes('/reports/attendance')) return ok(envelope(DEMO_ATTENDANCE_TREND));
  if (path.startsWith('/reports')) return ok(envelope(DEMO_DASHBOARD_METRICS));

  // Unmapped write: acknowledge so the UI's success path runs.
  if (method !== 'GET') return ok(envelope(null, 'Saved (demo mode - not persisted)'));

  // Unmapped read: empty rather than an error, so a screen renders empty
  // instead of throwing during a demo.
  return ok(envelope([]));
};
