import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ButtonComponent, IconComponent } from '@omni/ui';
import { AttendanceCorrectionRequest, AttendanceRecord } from '../../../../interfaces/attendance.interface';

@Component({
  selector: 'app-edit-record-form',
  standalone: true,
  imports: [CommonModule, FormsModule, ButtonComponent, IconComponent],
  templateUrl: './edit-record-form.component.html',
  styleUrls: []
})
export class EditRecordFormComponent implements OnInit {
  @Input({ required: true }) record!: AttendanceRecord;
  
  @Output() closeForm = new EventEmitter<void>();
  @Output() submitForm = new EventEmitter<AttendanceCorrectionRequest>();

  form = {
    clock_in: '',
    clock_out: '',
    reason: ''
  };
  
  error = '';

  ngOnInit() {
    const inDate = new Date(this.record.clock_in);
    const outDate = this.record.clock_out ? new Date(this.record.clock_out) : null;
    this.form = {
      clock_in: inDate.toISOString().substring(0, 16),
      clock_out: outDate ? outDate.toISOString().substring(0, 16) : '',
      reason: ''
    };
  }

  onSubmit() {
    this.error = '';
    
    if (!this.form.clock_in || !this.form.reason) {
      this.error = 'Please provide both the Check In time and a Reason for the edit.';
      return;
    }

    const payload: AttendanceCorrectionRequest = {
      clock_in: new Date(this.form.clock_in).toISOString(),
      clock_out: this.form.clock_out ? new Date(this.form.clock_out).toISOString() : null,
      reason: this.form.reason
    };

    this.submitForm.emit(payload);
  }

  onClose() {
    this.closeForm.emit();
  }
}
