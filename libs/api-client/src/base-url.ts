/**
 * Base URL for the generated tcheck client.
 *
 * The generated services embed `tcheckApiBase()` directly in their URL template
 * literals (orval `output.baseUrl.runtime`). That expression is evaluated inside
 * a service method, which is not an Angular injection context — so this cannot
 * be an InjectionToken and has to be plain module state, set once at bootstrap.
 * Same pattern as `configure_demo_mode`.
 *
 * This is what replaces the interceptor's hand-maintained URL allowlist. That
 * list had drifted to omit `/beacons`, `/safechild`, `/settings` and
 * `/organizations`; those endpoints only worked because their services happened
 * to build absolute URLs themselves. With the base URL baked into the generated
 * client, a missing prefix is no longer expressible.
 */

let tcheck_base = '';

/** Called once at bootstrap, before the app renders. */
export function configure_api_base(url: string): void {
  // Trailing slashes would produce `//beacons`, which some proxies treat as a
  // different path.
  tcheck_base = url.replace(/\/+$/, '');
}

/**
 * Prefix for every generated tcheck request.
 *
 * Returns '' in demo builds, so requests stay root-relative and are answered by
 * the demo interceptor. Anything that escapes it fails loudly against the dev
 * server rather than quietly reaching a real environment.
 */
export function tcheckApiBase(): string {
  return tcheck_base;
}
