import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AttendanceService } from '../attendance/attendance.service';
import { AttendanceRecord, AuditLog } from '../../interfaces/attendance.interface';
import {
  ButtonComponent,
  PillComponent,
  IconComponent
} from '@omni/ui';
import { ManualEntryFormComponent } from './components/manual-entry-form/manual-entry-form.component';
import { EditRecordFormComponent } from './components/edit-record-form/edit-record-form.component';
import { AttendanceManualRequest, AttendanceCorrectionRequest } from '../../interfaces/attendance.interface';

@Component({
  selector: 'app-attendance-records',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    ButtonComponent,
    PillComponent,
    IconComponent,
    ManualEntryFormComponent,
    EditRecordFormComponent
  ],
  templateUrl: './attendance-records.component.html',
  styleUrls: ['./attendance-records.component.scss']
})
export class AttendanceRecordsComponent implements OnInit {
  private readonly attendanceService = inject(AttendanceService);

  readonly records = signal<AttendanceRecord[]>([]);
  readonly loading = signal(false);

  // Form states
  readonly isManualEntryOpen = signal(false);

  readonly isEditOpen = signal(false);
  readonly editingRecord = signal<AttendanceRecord | null>(null);

  readonly isAuditOpen = signal(false);
  readonly auditTrail = signal<AuditLog[]>([]);

  ngOnInit() {
    this.loadRecords();
  }

  loadRecords() {
    this.loading.set(true);
    this.attendanceService.get_all_attendance().subscribe({
      next: (res) => {
        this.records.set(res.data);
        this.loading.set(false);
      },
      error: () => this.loading.set(false)
    });
  }

  // Manual Entry
  openManualEntry() {
    this.isManualEntryOpen.set(true);
  }
  closeManualEntry() { this.isManualEntryOpen.set(false); }
  
  submitManualEntry(payload: AttendanceManualRequest) {
    this.attendanceService.manual_entry(payload).subscribe(() => {
      this.closeManualEntry();
      this.loadRecords();
    });
  }

  // Edit Record
  openEdit(record: AttendanceRecord) {
    this.editingRecord.set(record);
    this.isEditOpen.set(true);
  }
  closeEdit() { this.isEditOpen.set(false); }
  
  submitEdit(payload: AttendanceCorrectionRequest) {
    const rec = this.editingRecord();
    if (!rec) return;
    
    this.attendanceService.edit_record(rec.id, payload).subscribe(() => {
      this.closeEdit();
      this.loadRecords();
    });
  }

  // Audit Trail
  openAudit(record: AttendanceRecord) {
    this.attendanceService.get_audit_trail(record.id).subscribe((res) => {
      this.auditTrail.set(res.data);
      this.isAuditOpen.set(true);
    });
  }
  closeAudit() { this.isAuditOpen.set(false); }
}


