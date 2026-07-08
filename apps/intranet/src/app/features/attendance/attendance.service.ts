import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { environment } from '../../../environments/environment';
import { AttendanceRecord, PaginatedAttendance, AuditLog, ClockOutResponse, AttendanceManualRequest, AttendanceCorrectionRequest } from '../../interfaces/attendance.interface'


@Injectable({ providedIn: 'root' })
export class AttendanceService {
  private readonly http = inject(HttpClient);

  clock_in(notes?: string, source = 'web'): Observable<AttendanceRecord> {
    return this.http.post<{ record: AttendanceRecord }>(`${environment.apiUrl}/attendance/clock-in`, { notes, source })
      .pipe(map(res => res.record));
  }

  clock_out(notes?: string): Observable<ClockOutResponse> {
    return this.http.post<ClockOutResponse>(`${environment.apiUrl}/attendance/clock-out`, { notes });
  }

  get_stats(): Observable<{ hours_this_week: number, team_present: number, team_total: number, streak: number }> {
    return this.http.get<{ hours_this_week: number, team_present: number, team_total: number, streak: number }>(`${environment.apiUrl}/attendance/stats`);
  }

  get_history(params: {
    date_from?: string;
    date_to?: string;
    page?: number;
    per_page?: number;
  } = {}): Observable<PaginatedAttendance> {
    let http_params = new HttpParams();
    if (params.date_from) {
      http_params = http_params.set('date_from', params.date_from);
    }
    if (params.date_to) {
      http_params = http_params.set('date_to', params.date_to);
    }
    if (params.page) {
      http_params = http_params.set('page', params.page.toString());
    }
    if (params.per_page) {
      http_params = http_params.set('per_page', params.per_page.toString());
    }

    return this.http.get<PaginatedAttendance>(`${environment.apiUrl}/attendance/me`, { params: http_params });
  }

  get_all_attendance(params: {
    page?: number;
    per_page?: number;
    employee_id?: string;
    date?: string;
  } = {}): Observable<{ data: AttendanceRecord[]; meta: { page: number; per_page: number; total: number; pages: number } }> {
    let http_params = new HttpParams();
    if (params.page) http_params = http_params.set('page', params.page.toString());
    if (params.per_page) http_params = http_params.set('per_page', params.per_page.toString());
    if (params.employee_id) http_params = http_params.set('employee_id', params.employee_id);
    if (params.date) http_params = http_params.set('date', params.date);

    return this.http.get<{ data: AttendanceRecord[]; meta: { page: number; per_page: number; total: number; pages: number } }>(`${environment.apiUrl}/attendance`, { params: http_params });
  }

  manual_entry(payload: AttendanceManualRequest): Observable<{ data: AttendanceRecord }> {
    return this.http.post<{ data: AttendanceRecord }>(`${environment.apiUrl}/attendance`, payload);
  }

  edit_record(id: number, payload: AttendanceCorrectionRequest): Observable<{ data: AttendanceRecord }> {
    return this.http.put<{ data: AttendanceRecord }>(`${environment.apiUrl}/attendance/${id}`, payload);
  }

  get_audit_trail(id: number): Observable<{ data: AuditLog[] }> {
    return this.http.get<{ data: AuditLog[] }>(`${environment.apiUrl}/attendance/${id}/audit`);
  }
}
