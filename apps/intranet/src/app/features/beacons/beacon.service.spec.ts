import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { API_URL } from '@omni/auth';
import { BeaconService } from './beacon.service';

const API = 'http://test.local/api/v2';

describe('BeaconService', () => {
  let service: BeaconService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: API_URL, useValue: API },
      ],
    });
    service = TestBed.inject(BeaconService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  /**
   * Regression: this screen was broken against a real backend.
   *
   * The component reads `res.data`, but `authInterceptor` used to strip the
   * envelope in flight, so `res.data` was `undefined` and the table rendered
   * empty. It only appeared to work because demo mode short-circuits before
   * that interceptor runs — which is exactly why nobody noticed.
   */
  it('returns the envelope intact so callers can read .data', async () => {
    const promise = firstValue<{ data: unknown }>(service.getBeacons());
    http.expectOne({ url: `${API}/beacons`, method: 'GET' }).flush({
      message: 'Success',
      data: [{ id: 'b1', mac_address: 'AC:23:45:67:89:01' }],
    });
    const res = await promise;
    expect(res.data).toEqual([{ id: 'b1', mac_address: 'AC:23:45:67:89:01' }]);
  });

  it('hits the assignments sub-path, not the beacon list', async () => {
    const promise = firstValue(service.getAssignments());
    // Distinct URL matters: the demo interceptor matches on `startsWith('/beacons')`,
    // so an assignments call that is not routed separately silently returns the
    // beacon list instead.
    http.expectOne({ url: `${API}/beacons/assignments`, method: 'GET' }).flush({
      message: 'Success',
      data: [],
    });
    await promise;
  });

  it('deletes by id', async () => {
    const promise = firstValue(service.deleteBeacon('b1'));
    http.expectOne({ url: `${API}/beacons/b1`, method: 'DELETE' }).flush({
      message: 'Deleted',
      data: { id: 'b1' },
    });
    await promise;
  });
});

function firstValue<T>(obs: { subscribe: (o: Record<string, unknown>) => unknown }): Promise<T> {
  return new Promise<T>((resolve, reject) => {
    obs.subscribe({ next: resolve, error: reject });
  });
}
