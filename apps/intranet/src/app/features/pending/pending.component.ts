import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { AuthService } from '@omni/auth';
import { IconComponent } from '@omni/ui';

@Component({
  selector: 'app-pending',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [IconComponent],
  templateUrl: './pending.component.html',
  styleUrl: './pending.component.scss',
})
export class PendingComponent {
  private readonly auth = inject(AuthService);
  
  refresh() {
    this.auth.fetch_db_profile(); // Trigger a reload to check if they got approved
  }
}
