import { InjectionToken } from '@angular/core';

/**
 * Base URLs, one per backend service.
 *
 * The services are deliberately not merged (different hosts, different auth,
 * colliding paths), so each gets its own token rather than a single API_URL that
 * would have to be rewritten per call.
 *
 * `@omni/auth` still exports `API_URL` for the tcheck backend; it and
 * TCHECK_API_URL point at the same value during the migration.
 */

/** Corporate attendance, SafeChild, beacons, settings — this repo's Flask API. */
export const TCHECK_API_URL = new InjectionToken<string>('TCHECK_API_URL');

/** Visitor management. Not yet wired — see docs/api/vcheck.openapi.yaml. */
export const VCHECK_API_URL = new InjectionToken<string>('VCHECK_API_URL');

/** Academic domain, owned by Tcheck-Backend (Node/Prisma). Not yet wired. */
export const ACADEMIC_API_URL = new InjectionToken<string>('ACADEMIC_API_URL');
