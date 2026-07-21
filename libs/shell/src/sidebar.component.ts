import { ChangeDetectionStrategy, Component, computed, inject } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { AuthService, RoleKey, ROLE_OPTIONS, is_demo_mode } from '@omni/auth';
import { IconComponent } from '@omni/ui';
import { NAV_PROVIDER, SHELL_BADGES } from './nav.token';

/**
 * Product-agnostic navigation sidebar.
 *
 * Knows nothing about tcheck or vcheck routes: the host app supplies its nav via
 * NAV_PROVIDER and any badge counts via SHELL_BADGES.
 */
@Component({
  selector: 'omni-sidebar',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink, RouterLinkActive, IconComponent],
  template: `
    <aside class="sidebar">
      <div class="sidebar-brand">
        <svg class="brand-logo" width="28" height="28" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
          <rect width="100" height="100" rx="18" fill="#3B82F6"/>
          <path d="M25 22H75V34H56V78H44V34H25V22Z" fill="white"/>
          <circle cx="68" cy="68" r="18" fill="white" stroke="#3B82F6" stroke-width="4"/>
          <path d="M58 68L65 75L79 59" stroke="#3B82F6" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <span class="brand-wordmark">TallyCheck</span>
      </div>

      @for (group of groups(); track group.label) {
        <div class="section-label">{{ group.label }}</div>
        @for (item of group.items; track item.id) {
          <a class="nav-item" [routerLink]="'/' + item.id" routerLinkActive="active">
            <omni-icon [name]="item.icon" />
            <span>{{ item.label }}</span>
            @if (item.badge) {
              <span class="badge">{{ item.badge }}</span>
            }
          </a>
        }
      }

      @if (isDemo) {
        <div class="sidebar-footer">
          <div class="section-label" style="padding-top:0">View as</div>
          <select [value]="role()" (change)="onRoleChange($event)">
            @for (opt of roleOptions; track opt.value) {
              <option [value]="opt.value">{{ opt.label }}</option>
            }
          </select>
        </div>
      }
    </aside>
  `,
  styleUrl: './sidebar.component.scss',
})
export class SidebarComponent {
  private readonly auth = inject(AuthService);
  private readonly navForRole = inject(NAV_PROVIDER);
  private readonly badges = inject(SHELL_BADGES, { optional: true });

  readonly role = this.auth.role;
  readonly roleOptions = ROLE_OPTIONS;

  /** The "View as" switcher is a demo affordance, not a product feature. */
  readonly isDemo = is_demo_mode();

  readonly groups = computed(() => {
    const counts = this.badges?.() ?? {};
    // Rebuild rather than mutate: the nav builder is pure, and a computed that
    // writes into its own inputs is a debugging trap.
    return this.navForRole(this.role()).map((group) => ({
      ...group,
      items: group.items.map((item) =>
        counts[item.id] ? { ...item, badge: counts[item.id] } : item
      ),
    }));
  });

  onRoleChange(event: Event): void {
    this.auth.set_role((event.target as HTMLSelectElement).value as RoleKey);
  }
}
