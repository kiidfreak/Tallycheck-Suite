import { Component, EventEmitter, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ButtonComponent, IconComponent } from '@omni/ui';
import { AttendanceManualRequest } from '../../../../interfaces/attendance.interface';

@Component({
  selector: 'app-manual-entry-form',
  standalone: true,
  imports: [CommonModule, FormsModule, ButtonComponent, IconComponent],
  templateUrl: './manual-entry-form.component.html',
  styleUrls: []
})
export class ManualEntryFormComponent {
  @Output() closeForm = new EventEmitter<void>();
  @Output() submitForm = new EventEmitter<AttendanceManualRequest>();

  form = {
    employee_id: '',
    work_date: '',
    clock_in: '',
    clock_out: '',
    reason: ''
  };
  
  error = '';

  onSubmit() {
    this.error = '';
    
    if (!this.form.employee_id || !this.form.work_date || !this.form.clock_in || !this.form.reason) {
      this.error = 'Please fill out all required fields, including the reason.';
      return;
    }

    const payload: AttendanceManualRequest = {
      employee_id: this.form.employee_id,
      work_date: this.form.work_date,
      clock_in: new Date(`${this.form.work_date}T${this.form.clock_in}`).toISOString(),
      clock_out: this.form.clock_out ? new Date(`${this.form.work_date}T${this.form.clock_out}`).toISOString() : null,
      reason: this.form.reason
    };

    this.submitForm.emit(payload);
  }

  onClose() {
    this.closeForm.emit();
  }
}
