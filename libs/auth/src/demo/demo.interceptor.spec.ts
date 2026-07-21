import { HttpRequest, HttpResponse, HttpHandlerFn } from '@angular/common/http';
import { firstValueFrom, of } from 'rxjs';
import { configure_demo_mode } from './demo-mode';
import { demoInterceptor } from './demo.interceptor';
import { DEMO_BEACONS, DEMO_BEACON_ASSIGNMENTS } from './demo-data';

/**
 * The demo interceptor routes by path prefix, so branch ORDER is load-bearing:
 * a general prefix placed before a specific one silently swallows it.
 *
 * That already shipped once — `/beacons/assignments` matched `startsWith('/beacons')`
 * and returned the beacon list, so the assignments column showed beacons.
 */

const passthrough: HttpHandlerFn = () =>
  of(new HttpResponse({ status: 204, body: null }));

async function call(url: string, method = 'GET'): Promise<unknown> {
  const req = new HttpRequest(method as 'GET', url, method === 'GET' ? null : {});
  const res = (await firstValueFrom(
    demoInterceptor(req as HttpRequest<unknown>, passthrough)
  )) as HttpResponse<{ data: unknown }>;
  return res.body?.data;
}

describe('demoInterceptor path routing', () => {
  beforeEach(() => configure_demo_mode(true, true));
  afterEach(() => configure_demo_mode(false, true));

  it('serves the beacon list for /beacons', async () => {
    await expect(call('/beacons')).resolves.toEqual(DEMO_BEACONS);
  });

  it('serves assignments for /beacons/assignments, NOT the beacon list', async () => {
    const data = await call('/beacons/assignments');
    expect(data).toEqual(DEMO_BEACON_ASSIGNMENTS);
    expect(data).not.toEqual(DEMO_BEACONS);
  });

  it('routes correctly when the url carries the full api prefix', async () => {
    // Real builds request absolute urls; the interceptor strips everything up to
    // and including /api/v2 before matching.
    await expect(
      call('https://api.tallycheck.co.ke/api/v2/beacons/assignments')
    ).resolves.toEqual(DEMO_BEACON_ASSIGNMENTS);
  });

  it('passes through when demo mode is off', async () => {
    configure_demo_mode(false, false);
    const req = new HttpRequest('GET', '/beacons');
    const res = (await firstValueFrom(
      demoInterceptor(req as HttpRequest<unknown>, passthrough)
    )) as HttpResponse<unknown>;
    expect(res.status).toBe(204);
  });

  it('wraps every demo body in the same envelope the server sends', async () => {
    // Callers apply unwrap() uniformly, so demo responses must be enveloped too.
    const req = new HttpRequest('GET', '/beacons');
    const res = (await firstValueFrom(
      demoInterceptor(req as HttpRequest<unknown>, passthrough)
    )) as HttpResponse<Record<string, unknown>>;
    expect(res.body).toEqual(
      expect.objectContaining({ message: expect.any(String), data: expect.anything() })
    );
  });
});
