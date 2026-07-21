import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { Envelope, unwrap, unwrapPaged } from '@omni/api-client';
import { environment } from '../../../environments/environment';
import { AttendanceRecord, PaginatedAttendance, AuditLog, ClockOutResponse, AttendanceManualRequest, AttendanceCorrectionRequest } from '../../interfaces/attendance.interface'

/**
 * Attendance API.
 *
 * Every response is unwrapped explicitly here. Previously `authInterceptor`
 * reshaped bodies in flight — stripping the envelope, and for paginated
 * responses spreading `meta` alongside a `records` alias. That was invisible to
 * the type system, so the declared return types described a shape no server ever
 * sent. `PaginatedAttendance` is still that flattened shape, kept so callers do
 * not change; the flattening now happens here, where it can be read and tested.
 */
@Injectable({ providedIn: 'root' })
export class AttendanceService {
  private readonly http = inject(HttpClient);

  clock_in(notes?: string, source = 'web'): Observable<AttendanceRecord> {
    return this.http
      .post<Envelope<{ record: AttendanceRecord }>>(`${environment.apiUrl}/attendance/clock-in`, { notes, source })
      .pipe(unwrap(), map(data => data.record));
  }

  clock_out(notes?: string): Observable<ClockOutResponse> {
    return this.http
      .post<Envelope<ClockOutResponse>>(`${environment.apiUrl}/attendance/clock-out`, { notes })
      .pipe(unwrap());
  }

  get_stats(): Observable<{ hours_this_week: number, team_present: number, team_total: number, streak: number }> {
    return this.http
      .get<Envelope<{ hours_this_week: number, team_present: number, team_total: number, streak: number }>>(
        `${environment.apiUrl}/attendance/stats`
      )
      .pipe(unwrap());
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

    return this.http
      .get<Envelope<AttendanceRecord[]>>(`${environment.apiUrl}/attendance/me`, { params: http_params })
      .pipe(
        unwrapPaged(),
        map(({ items, meta }) => ({
          records: items ?? [],
          total: meta.total ?? 0,
          page: meta.page ?? 1,
          pages: meta.pages ?? 0,
          per_page: meta.per_page ?? 0,
        }))
      );
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

    return this.http
      .get<Envelope<AttendanceRecord[]>>(`${environment.apiUrl}/attendance`, { params: http_params })
      .pipe(
        unwrapPaged(),
        map(({ items, meta }) => ({
          data: items ?? [],
          meta: {
            page: meta.page ?? 1,
            per_page: meta.per_page ?? 0,
            total: meta.total ?? 0,
            pages: meta.pages ?? 0,
          },
        }))
      );
  }

  manual_entry(payload: AttendanceManualRequest): Observable<{ data: AttendanceRecord }> {
    return this.http
      .post<Envelope<AttendanceRecord>>(`${environment.apiUrl}/attendance`, payload)
      .pipe(unwrap(), map(data => ({ data })));
  }

  edit_record(id: number, payload: AttendanceCorrectionRequest): Observable<{ data: AttendanceRecord }> {
    return this.http
      .put<Envelope<AttendanceRecord>>(`${environment.apiUrl}/attendance/${id}`, payload)
      .pipe(unwrap(), map(data => ({ data })));
  }

  get_audit_trail(id: number): Observable<{ data: AuditLog[] }> {
    return this.http
      .get<Envelope<AuditLog[]>>(`${environment.apiUrl}/attendance/${id}/audit`)
      .pipe(unwrap(), map(data => ({ data: data ?? [] })));
  }
}
