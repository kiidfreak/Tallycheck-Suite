import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { API_URL } from '@omni/auth';
import { Envelope, unwrap } from '@omni/api-client';
import { Organization, CreateOrganizationPayload } from '../../interfaces/organizations.interface';

@Injectable({
  providedIn: 'root'
})
export class OrganizationService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = inject(API_URL);

  getOrganizations(): Observable<Organization[]> {
    return this.http.get<Envelope<Organization[]>>(`${this.apiUrl}/organizations`).pipe(
      unwrap(),
      map(orgs => orgs ?? [])
    );
  }

  createOrganization(payload: CreateOrganizationPayload): Observable<Organization> {
    return this.http.post<Envelope<Organization>>(`${this.apiUrl}/organizations`, payload).pipe(
      unwrap()
    );
  }

  toggleOrganizationStatus(orgId: string, isActive: boolean): Observable<Organization> {
    return this.http.put<Envelope<Organization>>(`${this.apiUrl}/organizations/${orgId}`, { is_active: isActive }).pipe(
      unwrap()
    );
  }
}
