export const environment = {
  production: false,
  apiUrl: 'http://127.0.0.1:8001/api/v2',
  /** Serve canned data instead of calling the API. */
  demo: false,
  /** Allow ?demo=1 / localStorage to override `demo`. Dev only — never in prod. */
  allowDemoOverride: true,
};
