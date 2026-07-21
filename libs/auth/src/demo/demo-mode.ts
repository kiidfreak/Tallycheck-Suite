/**
 * Demo mode — lets the app run with no backend at all.
 *
 * Built for hosted demos (Vercel) where only the frontend is deployed. When on,
 * the Auth0 login round-trip is skipped and every API call is answered from
 * canned data, so the "View as" role switcher in the sidebar becomes the whole
 * story: pick a role, see that role's app.
 *
 * Resolution order:
 *   1. the build's environment.allowDemoOverride flag — when false, the build's
 *      environment.demo value is final and steps 2-3 are skipped entirely
 *   2. ?demo=1 / ?demo=0  in the URL  (wins, and is remembered)
 *   3. localStorage 'tc_demo'
 *   4. the build's environment.demo flag
 *
 * The query-param override exists so a demo build can be pointed at a real
 * backend (?demo=0) without a rebuild, and a local dev server can be put into
 * demo mode (?demo=1) to reproduce what the hosted demo shows.
 *
 * Production builds set allowDemoOverride=false. Without that, a browser that
 * ever loaded ?demo=1 keeps the sticky localStorage flag forever — including a
 * prospect's laptop after a sales demo — and would silently see canned data on
 * the real app.
 */

const STORAGE_KEY = 'tc_demo';

let build_default = false;
let allow_override = true;

/** Called once at bootstrap with environment.demo / environment.allowDemoOverride. */
export function configure_demo_mode(enabled: boolean, allowOverride = true): void {
  build_default = enabled;
  allow_override = allowOverride;
}

export function is_demo_mode(): boolean {
  if (typeof window === 'undefined') return build_default;

  // Locked builds (production) ignore the URL and localStorage entirely.
  if (!allow_override) return build_default;

  try {
    const param = new URLSearchParams(window.location.search).get('demo');
    if (param === '1' || param === 'true') {
      window.localStorage.setItem(STORAGE_KEY, '1');
      return true;
    }
    if (param === '0' || param === 'false') {
      window.localStorage.setItem(STORAGE_KEY, '0');
      return false;
    }

    const stored = window.localStorage.getItem(STORAGE_KEY);
    if (stored === '1') return true;
    if (stored === '0') return false;
  } catch {
    // Private browsing can throw on localStorage; fall back to the build flag.
  }

  return build_default;
}
