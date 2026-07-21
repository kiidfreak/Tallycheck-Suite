import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { API_URL } from '@omni/auth';
import { Envelope } from '@omni/api-client';
import { Observable } from 'rxjs';

export interface BleBeacon {
  id?: string;
  name: string;
  mac_address: string;
  uuid?: string;
  major: number;
  minor: number;
  location?: string;
  description?: string;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface BeaconAssignment {
  id?: string;
  beacon_id: string;
  beacon_name?: string;
  beacon_mac?: string;
  department_id: number;
  department_name?: string;
  created_at?: string;
}

/**
 * Beacon API.
 *
 * Returns the raw envelope rather than unwrapping, because callers already
 * read `res.data`. Note this screen was broken against a real backend until
 * `authInterceptor` stopped unwrapping bodies in flight: it stripped the
 * envelope, so `res.data` was undefined. It only ever worked in demo mode,
 * where demoInterceptor short-circuits before that interceptor runs.
 */
@Injectable({ providedIn: 'root' })
export class BeaconService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = inject(API_URL);

  getBeacons(): Observable<Envelope<BleBeacon[]>> {
    return this.http.get<Envelope<BleBeacon[]>>(`${this.apiUrl}/beacons`);
  }

  createBeacon(beacon: BleBeacon): Observable<Envelope<BleBeacon>> {
    return this.http.post<Envelope<BleBeacon>>(`${this.apiUrl}/beacons`, beacon);
  }

  updateBeacon(id: string, beacon: Partial<BleBeacon>): Observable<Envelope<BleBeacon>> {
    return this.http.put<Envelope<BleBeacon>>(`${this.apiUrl}/beacons/${id}`, beacon);
  }

  deleteBeacon(id: string): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/beacons/${id}`);
  }

  getAssignments(): Observable<Envelope<BeaconAssignment[]>> {
    return this.http.get<Envelope<BeaconAssignment[]>>(`${this.apiUrl}/beacons/assignments`);
  }

  assignBeacon(beaconId: string, departmentId: number): Observable<Envelope<BeaconAssignment>> {
    return this.http.post<Envelope<BeaconAssignment>>(`${this.apiUrl}/beacons/assignments`, {
      beacon_id: beaconId,
      department_id: departmentId
    });
  }

  unassignBeacon(assignmentId: string): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/beacons/assignments/${assignmentId}`);
  }
}
