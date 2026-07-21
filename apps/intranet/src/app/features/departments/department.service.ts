import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { API_URL } from '@omni/auth';
import { Envelope, unwrap } from '@omni/api-client';
import { Department } from '../../interfaces/departments.interface';

@Injectable({
  providedIn: 'root'
})
export class DepartmentService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = inject(API_URL);

  getDepartments(): Observable<Department[]> {
    // Previously this had to handle both a bare array and an enveloped body,
    // because authInterceptor unwrapped some responses and not others. Nothing
    // reshapes bodies in flight now, so the envelope is the only possibility.
    return this.http
      .get<Envelope<Department[]>>(`${this.apiUrl}/departments`)
      .pipe(unwrap(), map(departments => departments ?? []));
  }
}
