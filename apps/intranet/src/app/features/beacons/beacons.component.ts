import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { API_URL, AuthService } from '@omni/auth';
import { ButtonComponent, IconComponent, ToastService } from '@omni/ui';
import { BeaconService, BleBeacon, BeaconAssignment } from './beacon.service';

interface Department {
  id: number;
  name: string;
}

@Component({
  selector: 'app-beacons',
  standalone: true,
  imports: [CommonModule, FormsModule, ButtonComponent, IconComponent],
  templateUrl: './beacons.component.html',
  styleUrls: ['./beacons.component.scss']
})
export class BeaconsComponent implements OnInit {
  private readonly beaconService = inject(BeaconService);
  private readonly http = inject(HttpClient);
  private readonly apiUrl = inject(API_URL);
  readonly auth = inject(AuthService);
  private readonly toastService = inject(ToastService);

  readonly beacons = signal<BleBeacon[]>([]);
  readonly assignments = signal<BeaconAssignment[]>([]);
  readonly departments = signal<Department[]>([]);
  readonly loading = signal(false);

  // Form states
  readonly isBeaconDrawerOpen = signal(false);
  readonly isAssignDialogOpen = signal(false);
  readonly editingBeacon = signal<BleBeacon | null>(null);
  readonly activeBeaconForAssignment = signal<BleBeacon | null>(null);
  
  readonly formName = signal('');
  readonly formMac = signal('');
  readonly formUuid = signal('');
  readonly formMajor = signal(1);
  readonly formMinor = signal(1);
  readonly formLocation = signal('');
  readonly formDescription = signal('');
  readonly formIsActive = signal(true);
  
  readonly formDeptId = signal<number | null>(null);

  ngOnInit() {
    this.loadBeacons();
    this.loadAssignments();
    this.loadDepartments();
  }

  loadBeacons() {
    this.loading.set(true);
    this.beaconService.getBeacons().subscribe({
      next: (res) => {
        this.beacons.set(res.data);
        this.loading.set(false);
      },
      error: () => this.loading.set(false)
    });
  }

  loadAssignments() {
    this.beaconService.getAssignments().subscribe({
      next: (res) => {
        this.assignments.set(res.data);
      }
    });
  }

  loadDepartments() {
    this.http.get<Department[]>(`${this.apiUrl}/departments`).subscribe({
      next: (res: any) => {
        this.departments.set(res.data || res);
      }
    });
  }

  openBeaconDrawer(beacon?: BleBeacon) {
    if (beacon) {
      this.editingBeacon.set(beacon);
      this.formName.set(beacon.name || '');
      this.formMac.set(beacon.mac_address);
      this.formUuid.set(beacon.uuid || '');
      this.formMajor.set(beacon.major);
      this.formMinor.set(beacon.minor);
      this.formLocation.set(beacon.location || '');
      this.formDescription.set(beacon.description || '');
      this.formIsActive.set(beacon.is_active);
    } else {
      this.editingBeacon.set(null);
      this.formName.set('');
      this.formMac.set('');
      this.formUuid.set('');
      this.formMajor.set(1);
      this.formMinor.set(1);
      this.formLocation.set('');
      this.formDescription.set('');
      this.formIsActive.set(true);
    }
    this.isBeaconDrawerOpen.set(true);
  }

  closeBeaconDrawer() {
    this.isBeaconDrawerOpen.set(false);
    this.editingBeacon.set(null);
  }

  saveBeacon() {
    if (!this.formMac()) {
      this.toastService.show('MAC Address is required', 'error');
      return;
    }

    const payload: BleBeacon = {
      name: this.formName(),
      mac_address: this.formMac(),
      uuid: this.formUuid() || undefined,
      major: this.formMajor(),
      minor: this.formMinor(),
      location: this.formLocation(),
      description: this.formDescription(),
      is_active: this.formIsActive()
    };

    const edit = this.editingBeacon();
    if (edit && edit.id) {
      this.beaconService.updateBeacon(edit.id, payload).subscribe({
        next: () => {
          this.toastService.show('Beacon updated successfully', 'success');
          this.closeBeaconDrawer();
          this.loadBeacons();
        },
        error: (err) => this.toastService.show(err.error?.message || 'Failed to update beacon', 'error')
      });
    } else {
      this.beaconService.createBeacon(payload).subscribe({
        next: () => {
          this.toastService.show('Beacon created successfully', 'success');
          this.closeBeaconDrawer();
          this.loadBeacons();
        },
        error: (err) => this.toastService.show(err.error?.message || 'Failed to create beacon', 'error')
      });
    }
  }

  deleteBeacon(id: string) {
    if (!confirm('Are you sure you want to delete this beacon? All assignments will be removed.')) return;

    this.beaconService.deleteBeacon(id).subscribe({
      next: () => {
        this.toastService.show('Beacon deleted successfully', 'success');
        this.loadBeacons();
        this.loadAssignments();
      },
      error: () => this.toastService.show('Failed to delete beacon', 'error')
    });
  }

  openAssignDialog(beacon: BleBeacon) {
    this.activeBeaconForAssignment.set(beacon);
    this.formDeptId.set(null);
    this.isAssignDialogOpen.set(true);
  }

  closeAssignDialog() {
    this.isAssignDialogOpen.set(false);
    this.activeBeaconForAssignment.set(null);
  }

  submitAssignment() {
    const beacon = this.activeBeaconForAssignment();
    const deptId = this.formDeptId();

    if (!beacon || !beacon.id || !deptId) {
      this.toastService.show('Please select a department', 'error');
      return;
    }

    this.beaconService.assignBeacon(beacon.id, deptId).subscribe({
      next: () => {
        this.toastService.show('Beacon assigned successfully', 'success');
        this.closeAssignDialog();
        this.loadAssignments();
      },
      error: (err) => this.toastService.show(err.error?.message || 'Failed to assign beacon', 'error')
    });
  }

  removeAssignment(assignmentId: string) {
    if (!confirm('Are you sure you want to remove this assignment?')) return;

    this.beaconService.unassignBeacon(assignmentId).subscribe({
      next: () => {
        this.toastService.show('Assignment removed successfully', 'success');
        this.loadAssignments();
      },
      error: () => this.toastService.show('Failed to remove assignment', 'error')
    });
  }

  getBeaconAssignments(beaconId: string): BeaconAssignment[] {
    return this.assignments().filter(a => a.beacon_id === beaconId);
  }
}
