import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { DashboardStats, TimelineResponse } from '../../interfaces/team.interface';
import { PendingUser } from '../../interfaces/users.interface';

@Injectable({ providedIn: 'root' })
export class TeamService {
  private readonly http = inject(HttpClient);

  get_dashboard_stats(): Observable<DashboardStats> {
    return this.http.get<DashboardStats>(`${environment.apiUrl}/reports/dashboard`);
  }

  get_timeline(date?: string): Observable<TimelineResponse> {
    const params: Record<string, string> = {};
    if (date) {
      params['date'] = date;
    }
    return this.http.get<TimelineResponse>(`${environment.apiUrl}/reports/attendance/timeline`, { params });
  }

  get_pending_users(): Observable<PendingUser[]> {
    return this.http.get<PendingUser[]>(`${environment.apiUrl}/auth/users/pending`);
  }

  approve_user(userId: string): Observable<void> {
    return this.http.post<void>(`${environment.apiUrl}/auth/users/${userId}/approve`, {
      role_id: 1, // Default to staff (role ID 1)
      department_id: null,
      is_internal: true
    });
  }

  reject_user(userId: string): Observable<void> {
    return this.http.post<void>(`${environment.apiUrl}/employees/${userId}/deactivate`, {});
  }
}
