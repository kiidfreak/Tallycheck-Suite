import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '@omni/auth';
import { IconComponent } from '@omni/ui';

/** Top bar — ported from Header.jsx. */
@Component({
  selector: 'omni-header',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [IconComponent],
  template: `
    <header class="header">
      <!-- Search temporarily hidden for UAT -->
      <!-- <div class="search">
        <omni-icon name="search" />
        <input placeholder="Search people, tickets, documents…" />
      </div> -->
      <div class="spacer"></div>
      <button class="icon-btn" title="Help"><omni-icon name="circle-help" [size]="18" /></button>
      <!-- Notifications temporarily hidden for UAT -->
      <!-- <button class="icon-btn" title="Notifications">
        <omni-icon name="bell" [size]="18" />
        <span class="ping"></span>
      </button> -->
      <div class="user-chip">
        <div class="avatar" [class]="user()?.tone">{{ user()?.initials }}</div>
        <div class="user-meta">
          <span class="name">{{ user()?.name }}</span>
          <span class="role">{{ user()?.role }}</span>
        </div>
      </div>
      <button class="btn btn-danger btn-sm" title="Logout" (click)="logout()">
        <omni-icon name="log-out" [size]="16" /> Logout
      </button>
    </header>
  `,
  styleUrl: './header.component.scss',
})
export class HeaderComponent {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  readonly user = this.auth.user;

  logout(): void {
    this.auth.logout();
    this.router.navigate(['/login']);
  }
}
