// @omni/api-client — the generated API surface, plus the small hand-written
// pieces that sit around it.
//
// This barrel is the ONLY public entry point. Nothing outside this library
// should import from './generated/...' directly: keeping the surface here is
// what makes swapping the generator a single-library change rather than a
// repo-wide rewrite.
//
// Regenerate with:  nx run api-client:generate
// Verify in CI with: nx run api-client:generate-check

// ── Hand-written ────────────────────────────────────────────────
export { configure_api_base, tcheckApiBase } from './base-url';
export { TCHECK_API_URL, VCHECK_API_URL, ACADEMIC_API_URL } from './tokens';
export { unwrap, unwrapPaged, isEnvelope } from './unwrap';
export type { Envelope, Paged, Meta } from './unwrap';

// ── Generated: tcheck corporate ─────────────────────────────────
// Injectable services, one per OpenAPI tag.
export { AttendanceService } from './generated/tcheck/attendance/attendance.service';
export { AuthService as AuthApiService } from './generated/tcheck/auth/auth.service';
export { BeaconsService } from './generated/tcheck/beacons/beacons.service';
export { HealthService } from './generated/tcheck/health/health.service';
export { HrAttendanceService } from './generated/tcheck/hr-attendance/hr-attendance.service';
export { HrDepartmentsService } from './generated/tcheck/hr-departments/hr-departments.service';
export { HrEmployeesService } from './generated/tcheck/hr-employees/hr-employees.service';
export { ReportsService } from './generated/tcheck/reports/reports.service';
export { SafeChildService as SafeChildApiService } from './generated/tcheck/safe-child/safe-child.service';
export { SettingsService } from './generated/tcheck/settings/settings.service';
export { ZonesService } from './generated/tcheck/zones/zones.service';
export { PlatformService } from './generated/tcheck/platform/platform.service';

// Models. Re-exported wholesale: they are the contract, and a curated subset
// would go stale every time the spec grows.
export * from './generated/tcheck/model';
