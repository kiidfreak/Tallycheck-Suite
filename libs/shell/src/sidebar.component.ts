import { ChangeDetectionStrategy, Component, computed, inject, signal, OnInit } from '@angular/core';
import { RouterLink, RouterLinkActive, Router } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { API_URL, AuthService, RoleKey } from '@omni/auth';
import { IconComponent } from '@omni/ui';
import { COMM_SUBITEMS, NavItem, ROLE_OPTIONS, navForRole } from './nav';

/** Role-aware navigation sidebar — ported from Sidebar.jsx. */
@Component({
  selector: 'omni-sidebar',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink, RouterLinkActive, IconComponent],
  template: `
    <aside class="sidebar">
      <div class="sidebar-brand">
        <span class="brand-dots"><i></i><i></i><i></i></span>
        <span class="brand-wordmark">TallyCheck</span>
      </div>

      @for (group of groups(); track group.label) {
        <div class="section-label">{{ group.label }}</div>
        @for (item of group.items; track item.id) {
          @if (item.expandable) {
            <button class="nav-item" type="button" (click)="toggleComm()">
              <omni-icon [name]="item.icon" />
              <span>{{ item.label }}</span>
              @if (item.badge && !commExpanded()) {
                <span class="badge">{{ item.badge }}</span>
              }
              <omni-icon
                class="chevron"
                [name]="commExpanded() ? 'chevron-down' : 'chevron-right'"
                [size]="14"
              />
            </button>
            @if (commExpanded()) {
              @for (sub of commSubItems; track sub.id) {
                <a
                  class="nav-item nav-sub"
                  [routerLink]="'/' + sub.id"
                  routerLinkActive="active"
                  [routerLinkActiveOptions]="{ exact: true }"
                >
                  <omni-icon [name]="sub.icon" />
                  <span>{{ sub.label }}</span>
                </a>
              }
            }
          } @else {
            <a class="nav-item" [routerLink]="'/' + item.id" routerLinkActive="active">
              <omni-icon [name]="item.icon" />
              <span>{{ item.label }}</span>
              @if (item.badge) {
                <span class="badge">{{ item.badge }}</span>
              }
            </a>
          }
        }
      }

      <!--
      <div class="sidebar-footer">
        <div class="section-label" style="padding-top:0">View as</div>
        <select [value]="role()" (change)="onRoleChange($event)">
          @for (opt of roleOptions; track opt.value) {
            <option [value]="opt.value">{{ opt.label }}</option>
          }
        </select>
      </div>
      -->
    </aside>
  `,
  styleUrl: './sidebar.component.scss',
})
export class SidebarComponent implements OnInit {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  private readonly http = inject(HttpClient);
  private readonly apiUrl = inject(API_URL);

  readonly role = this.auth.role;
  readonly pendingUsersCount = signal(0);
  
  readonly groups = computed(() => {
    const role = this.role();
    const groupsData = navForRole(role);
    const pendingCount = this.pendingUsersCount();
    
    if (pendingCount > 0 && (role === 'hr' || role === 'super_admin')) {
      for (const group of groupsData) {
        for (const item of group.items) {
          if (item.id === 'employees') {
            item.badge = pendingCount;
          }
        }
      }
    }
    return groupsData;
  });
  
  readonly commExpanded = signal(false);
  readonly commSubItems: NavItem[] = COMM_SUBITEMS;
  readonly roleOptions = ROLE_OPTIONS;

  ngOnInit() {
    if (this.role() === 'hr' || this.role() === 'super_admin') {
      this.http.get<any[]>(`${this.apiUrl}/auth/users/pending`).subscribe({
        next: (users) => {
          this.pendingUsersCount.set(users?.length || 0);
        }
      });
    }
  }

  toggleComm(): void {
    const opening = !this.commExpanded();
    this.commExpanded.set(opening);
    if (opening) this.router.navigate(['/communication']);
  }

  onRoleChange(event: Event): void {
    const role = (event.target as HTMLSelectElement).value as RoleKey;
    this.auth.set_role(role);
  }
}
