/**
 * Hosted demo build — frontend only, no backend.
 *
 * `apiUrl` is deliberately empty: every request is answered by the demo
 * interceptor, so a bug that lets one through fails loudly instead of quietly
 * reaching a real environment.
 *
 * Override stays enabled here so a demo deployment can be pointed at a live
 * backend with ?demo=0 without a rebuild.
 */
export const environment = {
  production: true,
  apiUrl: '',
  demo: true,
  allowDemoOverride: true,
};
