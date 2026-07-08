import { ChangeDetectionStrategy, Component, input, output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ButtonComponent, TimerComponent } from '@omni/ui';
import { LucideAngularModule } from 'lucide-angular';

/** Reusable clock-out form: elapsed timer, note input, and check-out button. */
@Component({
  selector: 'app-clock-out-form',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [FormsModule, ButtonComponent, LucideAngularModule, TimerComponent],
  template: `
    <div class="clock-out-form-inner">
      <div class="active-shift-display">
        <span class="pulse-dot"></span>
        <div class="elapsed-timer">
          <omni-timer [startTime]="startTime()" />
        </div>
      </div>

      <input
        type="text"
        [(ngModel)]="note"
        placeholder="Add a check-out note (optional)..."
        class="single-line-note"
        [disabled]="loading() || showConfirm()"
      />

      <div class="full-width-btn">
        @if (!showConfirm()) {
          <omni-button variant="danger" (click)="showConfirm.set(true)" [disabled]="loading()">
            <lucide-icon name="log-out" [size]="18" class="btn-icon"></lucide-icon> Check out now
          </omni-button>
        } @else {
          <div class="confirm-actions">
            <span class="confirm-text">Are you sure you want to end your shift?</span>
            <div class="confirm-buttons">
              <omni-button variant="secondary" (click)="showConfirm.set(false)" [disabled]="loading()">Cancel</omni-button>
              <omni-button variant="danger" (click)="submit()" [disabled]="loading()">Yes, end shift</omni-button>
            </div>
          </div>
        }
      </div>
    </div>
  `,
  styleUrl: './clock-out-form.component.scss'
})
export class ClockOutFormComponent {
  readonly loading = input(false);
  readonly startTime = input<string>('');


  readonly clock_out = output<string>();

  readonly showConfirm = signal(false);

  note = '';

  submit(): void {
    this.clock_out.emit(this.note);
    this.note = '';
    this.showConfirm.set(false);
  }
}
