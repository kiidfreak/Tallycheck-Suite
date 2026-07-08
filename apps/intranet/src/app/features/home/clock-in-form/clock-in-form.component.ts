import { ChangeDetectionStrategy, Component, input, output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ButtonComponent } from '@omni/ui';
import { LucideAngularModule } from 'lucide-angular';

export interface ClockInSubmit {
  location: string;
  note: string;
}

/** Reusable clock-in form: shift selector, location selector, note, and submit button. */
@Component({
  selector: 'app-clock-in-form',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [FormsModule, ButtonComponent, LucideAngularModule],
  template: `
    <div class="clock-in-form-inner">

      <div class="form-group">
        <span class="label-text">Location</span>
        <div class="toggle-group location-group">
          @for (l of locations; track l.id) {
            <button [class.active]="selected_location() === l.id" (click)="selected_location.set(l.id)">
              <lucide-icon [name]="l.icon" [size]="16"></lucide-icon>
              {{ l.id }}
            </button>
          }
        </div>
      </div>

      <input
        type="text"
        [(ngModel)]="note"
        placeholder="Add a note (optional) — e.g. on-site at client"
        class="single-line-note"
        [disabled]="loading()"
      />

      <div class="full-width-btn">
        <omni-button variant="primary" (click)="submit()" [disabled]="loading()">
          <lucide-icon name="log-in" [size]="18" class="btn-icon"></lucide-icon> Check in now
        </omni-button>
      </div>
    </div>
  `,
  styleUrl: './clock-in-form.component.scss'
})
export class ClockInFormComponent {
  readonly loading = input(false);
  readonly clock_in = output<ClockInSubmit>();
  readonly locations = [
    { id: 'Office', icon: 'building' },
    { id: 'Remote', icon: 'house' },
    { id: 'Field', icon: 'map-pin' }
  ];
  readonly selected_location = signal('Office');

  note = '';

  submit(): void {
    this.clock_in.emit({
      location: this.selected_location(),
      note: this.note
    });
    this.note = '';
  }
}
