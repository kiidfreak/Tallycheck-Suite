import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
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

  readonly subdomain = signal('');
  readonly resolvedOrgName = signal('');
  readonly resolving = signal(false);
  readonly resolveError = signal(false);

  onSubdomainChange(event: Event) {
    const val = (event.target as HTMLInputElement).value;
    this.subdomain.set(val);
    this.resolvedOrgName.set('');
    this.resolveError.set(false);
  }

  resolveSubdomain() {
    const sub = this.subdomain().trim();
    if (!sub) {
      this.resolvedOrgName.set('');
      this.resolveError.set(false);
      return;
    }

    this.resolving.set(true);
    this.resolveError.set(false);
    this.auth.getOrganizationBySubdomain(sub).subscribe({
      next: (res) => {
        this.resolvedOrgName.set(res.data.name);
        this.resolving.set(false);
      },
      error: () => {
        this.resolvedOrgName.set('');
        this.resolveError.set(true);
        this.resolving.set(false);
      }
    });
  }

  submit(): void {
    // Triggers the Auth0 Organization or general login Redirect
    this.auth.login(this.subdomain());
  }
}
