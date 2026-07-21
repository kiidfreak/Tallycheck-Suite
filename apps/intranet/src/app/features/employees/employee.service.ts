import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { Envelope, unwrap } from '@omni/api-client';
import { environment } from '../../../environments/environment';
import { Employee, EmployeeListResponse, EmployeeFilters, CreateEmployeePayload, UpdateEmployeePayload } from '../../interfaces/employees.interface'

@Injectable({
  providedIn: 'root'
})
export class EmployeeService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = environment.apiUrl;

  getEmployees(filters: EmployeeFilters = {}): Observable<EmployeeListResponse> {
    let params = new HttpParams();
    
    if (filters.page) params = params.set('page', filters.page);
    if (filters.per_page) params = params.set('per_page', filters.per_page);
    if (filters.search) params = params.set('search', filters.search);
    if (filters.department_id) params = params.set('department_id', filters.department_id);
    if (filters.department_name) params = params.set('department_name', filters.department_name);
    if (filters.is_active !== undefined) params = params.set('is_active', filters.is_active);
    if (filters.is_approved !== undefined) params = params.set('is_approved', filters.is_approved);
    if (filters.role) params = params.set('role', filters.role);

    // EmployeeListResponse is `{data, meta}` — structurally the envelope.
    return this.http.get<EmployeeListResponse>(`${this.apiUrl}/employees`, { params });
  }

  getEmployee(id: string): Observable<Employee> {
    return this.http
      .get<Envelope<Employee>>(`${this.apiUrl}/employees/${id}`)
      .pipe(unwrap());
  }

  createEmployee(payload: CreateEmployeePayload): Observable<Employee> {
    return this.http
      .post<Envelope<Employee>>(`${this.apiUrl}/employees`, payload)
      .pipe(unwrap());
  }

  updateEmployee(id: string, payload: UpdateEmployeePayload): Observable<Employee> {
    return this.http
      .put<Envelope<Employee>>(`${this.apiUrl}/employees/${id}`, payload)
      .pipe(unwrap());
  }

  deactivateEmployee(id: string): Observable<{ message: string }> {
    return this.http.post<{ message: string }>(`${this.apiUrl}/employees/${id}/deactivate`, {});
  }
}
