export const environment = {
  production: true,
  apiUrl: 'https://api.tallycheck.co.ke/api/v2',
  demo: false,
  /**
   * Locked. Production must never be switchable into demo mode — not by URL and
   * not by a stale localStorage flag left behind by an earlier demo build.
   */
  allowDemoOverride: false,
};
