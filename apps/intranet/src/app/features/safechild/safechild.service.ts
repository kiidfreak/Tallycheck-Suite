import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { API_URL } from '@omni/auth';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';

export interface Guardian {
  id: string;
  name: string;
  phone: string;
  relation: string;
  is_primary: boolean;
  photo_url?: string;
}

export interface Child {
  id: string;
  name: string;
  group_name: string;
  photo_url?: string;
  is_active: boolean;
  guardians: Guardian[];
  status?: 'checked_in' | 'absent' | 'released' | 'picked_up';
  check_in_time?: string;
}

export interface DropOffResponse {
  token_id: string;
  child_name: string;
  pin: string;
  qr_payload: string;
  expires_at: string;
}

export interface VerificationResponse {
  child_name: string;
  child_photo?: string;
  guardian_name: string;
  guardian_relation?: string;
  verified_at: string;
}

@Injectable({ providedIn: 'root' })
export class SafeChildService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = inject(API_URL);

  getChildren(): Observable<Child[]> {
    return this.http.get<any>(`${this.apiUrl}/safechild/children`).pipe(
      map(res => Array.isArray(res) ? res : res?.data || [])
    );
  }

  logDropOff(childId: string, guardianId?: string, employeeId?: string): Observable<DropOffResponse> {
    return this.http.post<any>(`${this.apiUrl}/safechild/drop-off`, {
      child_id: childId,
      guardian_id: guardianId || null,
      employee_id: employeeId || null
    }).pipe(
      map(res => res?.data || res)
    );
  }

  verifyPickup(code: string, verifierId?: string): Observable<VerificationResponse> {
    return this.http.post<any>(`${this.apiUrl}/safechild/pickup/verify`, {
      code,
      verifier_id: verifierId || null
    }).pipe(
      map(res => res?.data || res)
    );
  }
}
