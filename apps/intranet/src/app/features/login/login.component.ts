import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { AuthService } from '@omni/auth';
import { IconComponent } from '@omni/ui';

/** Authentication gate — Triggers Auth0 Redirect */
@Component({
  selector: 'app-login',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [IconComponent],
  templateUrl: './login.component.html',
  styleUrl: './login.component.scss',
})
export class LoginComponent {
  private readonly auth = inject(AuthService);
  readonly year = new Date().getFullYear();

  submit(): void {
    // Triggers the Auth0 login Redirect
    this.auth.login();
  }
}
