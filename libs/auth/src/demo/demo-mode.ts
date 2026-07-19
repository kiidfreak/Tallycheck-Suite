/**
 * Demo mode — lets the app run with no backend at all.
 *
 * Built for hosted demos (Vercel) where only the frontend is deployed. When on,
 * the Auth0 login round-trip is skipped and every API call is answered from
 * canned data, so the "View as" role switcher in the sidebar becomes the whole
 * story: pick a role, see that role's app.
 *
 * Resolution order:
 *   1. ?demo=1 / ?demo=0  in the URL  (wins, and is remembered)
 *   2. localStorage 'tc_demo'
 *   3. the build's environment.demo flag
 *
 * The query-param override exists so a demo build can be pointed at a real
 * backend (?demo=0) without a rebuild, and a local dev server can be put into
 * demo mode (?demo=1) to reproduce what the hosted demo shows.
 */

const STORAGE_KEY = 'tc_demo';

let build_default = true;

/** Called once at bootstrap with environment.demo. */
export function configure_demo_mode(enabled: boolean): void {
  build_default = enabled;
}

export function is_demo_mode(): boolean {
  if (typeof window === 'undefined') return build_default;

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
