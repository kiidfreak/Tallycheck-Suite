import { ChangeDetectionStrategy, Component, input, output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ButtonComponent, IconComponent } from '@omni/ui';
import { LucideAngularModule } from 'lucide-angular';

export interface ClockInSubmit {
  location: string;
  note: string;
}

/** Reusable clock-in form: shift selector, BLE beacon telemetry, location selector, note, and submit button. */
@Component({
  selector: 'app-clock-in-form',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [FormsModule, ButtonComponent, IconComponent, LucideAngularModule],
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

      @if (selected_location() === 'Office') {
        <div class="beacon-status-box">
          <div class="beacon-header">
            <span class="beacon-dot pulse"></span>
            <strong class="beacon-title">BLE Active</strong>
          </div>
          @if (nearby_beacon(); as beacon) {
            <div class="beacon-info">
              <span class="beacon-name">
                <omni-icon name="bluetooth" [size]="14" class="text-primary"></omni-icon>
                {{ beacon.name }}
              </span>
              <span class="beacon-meta">{{ beacon.location }} · {{ beacon.rssi }}</span>
            </div>
          } @else {
            <div class="beacon-searching">
              <span>Scanning for nearby Bluetooth beacons...</span>
            </div>
          }
        </div>
      }

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

  readonly nearby_beacon = signal<{ name: string; location: string; rssi: string } | null>({
    name: 'Canine Section 2 Beacon (UUID: AA:BB:CC:01)',
    location: 'Dog Block · Main Area',
    rssi: '-58 dBm (In-Range Verified)'
  });

  note = '';

  submit(): void {
    const locNote = this.selected_location() === 'Office' && this.nearby_beacon()
      ? `[BLE: ${this.nearby_beacon()?.name}] ${this.note}`.trim()
      : this.note;

    this.clock_in.emit({
      location: this.selected_location(),
      note: locNote
    });
    this.note = '';
  }
}
