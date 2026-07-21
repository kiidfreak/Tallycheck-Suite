import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { API_URL } from '@omni/auth';
import { DepartmentService } from './department.service';

const API = 'http://test.local/api/v2';

describe('DepartmentService', () => {
  let service: DepartmentService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: API_URL, useValue: API },
      ],
    });
    service = TestBed.inject(DepartmentService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('requests the absolute API url, not a root-relative path', async () => {
    // A relative path would hit the dev server. This is the class of bug the
    // interceptor's hand-maintained URL allowlist used to cause whenever a new
    // endpoint was added and the list was not updated.
    const promise = firstValue(service.getDepartments());
    http.expectOne({ url: `${API}/departments`, method: 'GET' }).flush({
      message: 'Success',
      data: [],
    });
    await promise;
  });

  it('unwraps the envelope', async () => {
    const promise = firstValue(service.getDepartments());
    http.expectOne(`${API}/departments`).flush({
      message: 'Success',
      data: [{ id: 1, name: 'engineering' }],
    });
    await expect(promise).resolves.toEqual([{ id: 1, name: 'engineering' }]);
  });

  it('yields an empty array when data is null', async () => {
    const promise = firstValue(service.getDepartments());
    http.expectOne(`${API}/departments`).flush({ message: 'Success', data: null });
    await expect(promise).resolves.toEqual([]);
  });
});

function firstValue<T>(obs: { subscribe: (o: Record<string, unknown>) => unknown }): Promise<T> {
  return new Promise<T>((resolve, reject) => {
    obs.subscribe({ next: resolve, error: reject });
  });
}
