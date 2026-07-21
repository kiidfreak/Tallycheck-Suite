import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { API_URL } from '@omni/auth';
import { Envelope, unwrap } from '@omni/api-client';
import { 
  DashboardMetrics, 
  PaginatedReportAttendance, 
  ReportDepartmentAttendance,
  ReportTrendData
} from '../../interfaces/reports.interface';

@Injectable({
  providedIn: 'root'
})
export class ReportService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = inject(API_URL);

  /**
   * Fetches the top-level dashboard KPI metrics for the current day.
   */
  get_dashboard_metrics(): Observable<DashboardMetrics> {
    return this.http
      .get<Envelope<DashboardMetrics>>(`${this.apiUrl}/reports/dashboard`)
      .pipe(unwrap());
  }

  /**
   * Retrieves a paginated list of attendance records filtered by date range, department, and employee.
   */
  get_attendance_report(params: {
    date_from?: string;
    date_to?: string;
    department_id?: number | null;
    employee_id?: number | null;
    page?: number;
    per_page?: number;
  }): Observable<PaginatedReportAttendance> {
    let http_params = new HttpParams();
    if (params.date_from) http_params = http_params.set('date_from', params.date_from);
    if (params.date_to) http_params = http_params.set('date_to', params.date_to);
    if (params.department_id) http_params = http_params.set('department_id', params.department_id);
    if (params.employee_id) http_params = http_params.set('employee_id', params.employee_id);
    if (params.page) http_params = http_params.set('page', params.page);
    if (params.per_page) http_params = http_params.set('per_page', params.per_page);

    // PaginatedReportAttendance is `{data, meta}` — structurally the envelope,
    // so this needs no unwrapping.
    return this.http.get<PaginatedReportAttendance>(`${this.apiUrl}/reports/attendance`, { params: http_params });
  }

  /**
   * Aggregates attendance metrics per department over a specified date range.
   */
  get_department_attendance_report(params: {
    date_from?: string;
    date_to?: string;
  }): Observable<ReportDepartmentAttendance[]> {
    let http_params = new HttpParams();
    if (params.date_from) http_params = http_params.set('date_from', params.date_from);
    if (params.date_to) http_params = http_params.set('date_to', params.date_to);

    return this.http
      .get<Envelope<ReportDepartmentAttendance[]>>(`${this.apiUrl}/reports/attendance/departments`, { params: http_params })
      .pipe(unwrap());
  }

  /**
   * Aggregates daily worked hours over a specified date range.
   */
  get_attendance_trends(params: {
    date_from?: string;
    date_to?: string;
    department_id?: number | null;
  }): Observable<{data: ReportTrendData[]}> {
    let http_params = new HttpParams();
    if (params.date_from) http_params = http_params.set('date_from', params.date_from);
    if (params.date_to) http_params = http_params.set('date_to', params.date_to);
    if (params.department_id) http_params = http_params.set('department_id', params.department_id.toString());

    return this.http.get<{data: ReportTrendData[]}>(`${this.apiUrl}/reports/attendance/trends`, { params: http_params });
  }
}
