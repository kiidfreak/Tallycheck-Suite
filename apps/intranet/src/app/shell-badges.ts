import { Injectable, Signal, computed, effect, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { API_URL, AuthService, hasPermission } from '@omni/auth';
import { Envelope, unwrap } from '@omni/api-client';

interface PendingUser {
  id: string;
}

/**
 * Badge counts for the tcheck sidebar, keyed by nav item id.
 *
 * This used to be an inline HttpClient call inside @omni/shell's sidebar, which
 * hardcoded a tcheck endpoint into a component shared with vcheck. The shell now
 * takes a signal via SHELL_BADGES and stays ignorant of where numbers come from.
 */
@Injectable({ providedIn: 'root' })
export class ShellBadgesService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = inject(API_URL);
  private readonly auth = inject(AuthService);

  private readonly pendingUsers = signal(0);

  readonly badges: Signal<Record<string, number>> = computed(() => {
    const pending = this.pendingUsers();
    const badges: Record<string, number> = {};
    if (pending > 0) badges['employees'] = pending;
    return badges;
  });

  constructor() {
    // Refetch whenever the role changes. The previous version fetched once in
    // the sidebar's ngOnInit, which ran before the profile resolved, so the
    // badge stayed empty for anyone whose role arrived from /auth/me.
    effect(() => {
      const role = this.auth.role();
      if (!hasPermission(role, 'approve:employees')) {
        this.pendingUsers.set(0);
        return;
      }
      this.http
        .get<Envelope<PendingUser[]>>(`${this.apiUrl}/auth/users/pending`)
        .pipe(unwrap())
        .subscribe({
        next: (users) => this.pendingUsers.set(users?.length ?? 0),
        error: () => this.pendingUsers.set(0),
      });
    });
  }
}
