import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AttendanceService } from '../attendance/attendance.service';
import { AuthService } from '@omni/auth';
import { AttendanceRecord, AuditLog } from '../../interfaces/attendance.interface';
import {
  ButtonComponent,
  PillComponent,
  IconComponent,
  StatCardComponent
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
    StatCardComponent,
    ManualEntryFormComponent,
    EditRecordFormComponent
  ],
  templateUrl: './attendance-records.component.html',
  styleUrls: ['./attendance-records.component.scss']
})
export class AttendanceRecordsComponent implements OnInit {
  private readonly attendanceService = inject(AttendanceService);
  readonly auth = inject(AuthService);

  readonly records = signal<AttendanceRecord[]>([]);
  readonly loading = signal(false);

  // Academic Lecturer & HOD Signals
  readonly is_lecturer = computed(() => 
    this.auth.role() === 'lecturer' || this.auth.role() === 'school_admin'
  );

  readonly is_hod = computed(() => 
    this.auth.role() === 'department_manager' || this.auth.role() === 'school_admin'
  );

  readonly active_lecture_session = signal({
    course_code: 'ACS 301',
    course_title: 'Mobile Application Development',
    room: 'Science Lab 2 · Main Campus',
    scheduled_time: '08:00 AM - 11:00 AM',
    enrolled_students: 48,
    present_students: 42,
    qr_session_token: 'TC-ACS301-20260719-8942',
    is_qr_active: true
  });

  readonly my_lecture_courses = signal([
    { code: 'ACS 301', name: 'Mobile Application Development', students: 48, rate: '87.5%', room: 'Science Lab 2' },
    { code: 'ICS 311', name: 'Data Structures & Algorithms', students: 54, rate: '92.6%', room: 'LT 1 Hall' },
    { code: 'PHY 101', name: 'Physics for Engineers', students: 62, rate: '90.3%', room: 'Auditorium A' }
  ]);

  readonly show_qr_modal = signal(false);
  openQRModal() { this.show_qr_modal.set(true); }
  closeQRModal() { this.show_qr_modal.set(false); }

  // Filters
  startDate = signal('');
  endDate = signal('');
  statusFilter = signal('all');

  // Computed summary metrics
  readonly total_hours = computed(() => {
    return this.filtered_records().reduce((acc, r) => acc + (r.worked_hours || 0), 0).toFixed(1);
  });

  readonly active_days = computed(() => {
    return this.filtered_records().filter(r => r.status === 'closed' || r.status === 'open').length;
  });

  readonly on_time_rate = computed(() => {
    const total = this.filtered_records().length;
    if (!total) return '100%';
    const onTime = this.filtered_records().filter(r => r.status === 'closed' || r.status === 'open').length;
    return `${Math.round((onTime / total) * 100)}%`;
  });

  readonly filtered_records = computed(() => {
    let list = this.records();
    if (this.startDate()) {
      list = list.filter(r => r.work_date >= this.startDate());
    }
    if (this.endDate()) {
      list = list.filter(r => r.work_date <= this.endDate());
    }
    if (this.statusFilter() !== 'all') {
      list = list.filter(r => r.status === this.statusFilter());
    }
    return list;
  });

  // Active Shift State
  readonly active_shift = signal<{ clock_in: string; location: string } | null>(null);

  clockInTeacherShift(location = 'Ezra Building - Sunday School'): void {
    this.active_shift.set({
      clock_in: new Date().toISOString(),
      location
    });
  }

  clockOutTeacherShift(): void {
    this.active_shift.set(null);
  }

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

  exportCSV() {
    const data = this.filtered_records();
    if (!data.length) return;

    const headers = ['ID', 'Work Date', 'Clock In', 'Clock Out', 'Worked Hours', 'Status', 'Source', 'Notes'];
    const rows = data.map(r => [
      r.id,
      r.work_date,
      r.clock_in,
      r.clock_out || '',
      r.worked_hours || 0,
      r.status,
      r.source,
      `"${r.notes || ''}"`
    ]);

    const csvContent = [headers.join(','), ...rows.map(row => row.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `my_attendance_timesheet_${new Date().toISOString().slice(0, 10)}.csv`;
    link.click();
    URL.revokeObjectURL(url);
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


