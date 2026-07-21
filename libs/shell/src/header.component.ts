import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output, inject } from '@angular/core';
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
      <!-- Drawer toggle. CSS hides it above the tablet breakpoint, where the
           sidebar is always visible. -->
      <button
        class="icon-btn nav-toggle"
        type="button"
        [attr.aria-expanded]="navOpen"
        aria-controls="app-nav"
        [attr.aria-label]="navOpen ? 'Close navigation' : 'Open navigation'"
        (click)="menuToggle.emit()"
      >
        <omni-icon [name]="navOpen ? 'x' : 'menu'" [size]="20" />
      </button>

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
        <omni-icon name="log-out" [size]="16" />
        <span class="btn-label">Logout</span>
      </button>
    </header>
  `,
  styleUrl: './header.component.scss',
})
export class HeaderComponent {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  readonly user = this.auth.user;

  /** Drawer state, owned by the shell — drives the toggle icon and aria-expanded. */
  @Input() navOpen = false;
  @Output() menuToggle = new EventEmitter<void>();

  logout(): void {
    this.auth.logout();
    this.router.navigate(['/login']);
  }
}
