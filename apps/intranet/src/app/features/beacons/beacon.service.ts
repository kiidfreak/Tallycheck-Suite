import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { API_URL } from '@omni/auth';
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

@Injectable({ providedIn: 'root' })
export class BeaconService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = inject(API_URL);

  getBeacons(): Observable<{ data: BleBeacon[] }> {
    return this.http.get<{ data: BleBeacon[] }>(`${this.apiUrl}/beacons`);
  }

  createBeacon(beacon: BleBeacon): Observable<{ data: BleBeacon }> {
    return this.http.post<{ data: BleBeacon }>(`${this.apiUrl}/beacons`, beacon);
  }

  updateBeacon(id: string, beacon: Partial<BleBeacon>): Observable<{ data: BleBeacon }> {
    return this.http.put<{ data: BleBeacon }>(`${this.apiUrl}/beacons/${id}`, beacon);
  }

  deleteBeacon(id: string): Observable<any> {
    return this.http.delete(`${this.apiUrl}/beacons/${id}`);
  }

  getAssignments(): Observable<{ data: BeaconAssignment[] }> {
    return this.http.get<{ data: BeaconAssignment[] }>(`${this.apiUrl}/beacons/assignments`);
  }

  assignBeacon(beaconId: string, departmentId: number): Observable<{ data: BeaconAssignment }> {
    return this.http.post<{ data: BeaconAssignment }>(`${this.apiUrl}/beacons/assignments`, {
      beacon_id: beaconId,
      department_id: departmentId
    });
  }

  unassignBeacon(assignmentId: string): Observable<any> {
    return this.http.delete(`${this.apiUrl}/beacons/assignments/${assignmentId}`);
  }
}
