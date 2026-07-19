import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { API_URL } from '@omni/auth';
import { Department } from '../../interfaces/departments.interface';

@Injectable({
  providedIn: 'root'
})
export class DepartmentService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = inject(API_URL);

  getDepartments(): Observable<Department[]> {
    return this.http.get<Department[] | { data?: Department[] }>(`${this.apiUrl}/departments`).pipe(
      map(res => {
        const responseData = res as { data?: Department[] };
        return responseData?.data || (res as Department[]) || [];
      })
    );
  }
}
