import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { API_URL } from '@omni/auth';
import { Organization, CreateOrganizationPayload } from '../../interfaces/organizations.interface';

@Injectable({
  providedIn: 'root'
})
export class OrganizationService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = inject(API_URL);

  getOrganizations(): Observable<Organization[]> {
    return this.http.get<{ status: string; message: string; data: Organization[] }>(`${this.apiUrl}/organizations`).pipe(
      map(res => res.data || [])
    );
  }

  createOrganization(payload: CreateOrganizationPayload): Observable<Organization> {
    return this.http.post<{ status: string; message: string; data: Organization }>(`${this.apiUrl}/organizations`, payload).pipe(
      map(res => res.data)
    );
  }

  toggleOrganizationStatus(orgId: string, isActive: boolean): Observable<Organization> {
    return this.http.put<{ status: string; message: string; data: Organization }>(`${this.apiUrl}/organizations/${orgId}`, { is_active: isActive }).pipe(
      map(res => res.data)
    );
  }
}
