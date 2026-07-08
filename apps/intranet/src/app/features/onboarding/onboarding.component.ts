import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { AuthService } from '@omni/auth';
import { IconComponent } from '@omni/ui';

@Component({
  selector: 'app-onboarding',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [FormsModule, IconComponent],
  templateUrl: './onboarding.component.html',
  styleUrl: './onboarding.component.scss',
})
export class OnboardingComponent {
  private readonly auth = inject(AuthService);
  
  first_name = '';
  last_name = '';
  shift_type = 'standard';
  shift_hours = '7am-5pm';
  custom_shift_start = '';
  custom_shift_end = '';
  
  readonly busy = signal(false);
  readonly error = signal('');

  onShiftTypeChange(): void {
    if (this.shift_type === 'extended') {
      this.shift_hours = '7am-430pm';
    } else {
      this.shift_hours = '7am-5pm';
    }
  }

  submit(): void {
    this.error.set('');

    if (!this.first_name || !this.last_name) {
      this.error.set('Please fill out all fields.');
      return;
    }

    if (this.shift_hours === 'custom') {
      if (!this.custom_shift_start || !this.custom_shift_end) {
        this.error.set('Please select custom start and end times.');
        return;
      }
      const [sh, sm] = this.custom_shift_start.split(':').map(Number);
      const [eh, em] = this.custom_shift_end.split(':').map(Number);
      if (isNaN(sh) || isNaN(sm) || isNaN(eh) || isNaN(em)) {
        this.error.set('Please select valid custom times.');
        return;
      }
      const diff = (eh * 60 + em) - (sh * 60 + sm);
      if (this.shift_type === 'extended' && diff !== 570) {
        this.error.set('Custom shift must be exactly 9 hours 30 minutes.');
        return;
      }
      if (this.shift_type === 'standard' && diff !== 600) {
        this.error.set('Custom shift must be exactly 10 hours.');
        return;
      }
    }

    this.busy.set(true);
    this.auth.register_user(
      this.first_name,
      this.last_name,
      this.shift_type,
      this.shift_hours,
      this.shift_hours === 'custom' ? this.custom_shift_start : undefined,
      this.shift_hours === 'custom' ? this.custom_shift_end : undefined
    ).subscribe({
      next: () => this.busy.set(false),
      error: (err) => {
        const detail = err?.error?.details || 'Failed to register. Please try again.';
        this.error.set(detail);
        this.busy.set(false);
      }
    });
  }
}
