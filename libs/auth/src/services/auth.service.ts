import { Injectable, inject, signal } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Router } from '@angular/router';
import { AuthService as Auth0Service } from '@auth0/auth0-angular';
import { ROLES, RoleKey, UserProfile, Permission, hasPermission } from '../roles';
import { API_URL } from '../api-url.token';
import { is_demo_mode } from '../demo/demo-mode';
import { Envelope, unwrap } from '@omni/api-client';
import { catchError, map, of, take, switchMap } from 'rxjs';

export interface DbProfile {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  department_id: number | null;
  department_name: string | null;
  role_name: string | null;
  is_approved: boolean;
  standard_shift: string;
  shift_type?: 'standard' | 'extended';
  shift_hours?: '7am-5pm' | '9am-7pm' | 'custom';
  custom_shift_start?: string;
  custom_shift_end?: string;
}

export interface ApiError {
  error: string;       
  message: string;      
  details?: string | null; 
}

export interface RegisterResponse {
  message: string;
  employee: {
    id: string;
    auth0_id: string;
  };
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly auth0 = inject(Auth0Service);
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);
  private readonly apiUrl = inject(API_URL);

  private readonly _role = signal<RoleKey>('staff');
  private readonly _is_authenticated = signal<boolean>(false);
  private readonly _user_profile = signal<UserProfile | null>(null);
  
  private readonly _is_registered = signal<boolean>(true);
  private readonly _is_approved = signal<boolean>(true);
  private readonly _profile_loaded = signal<boolean>(true);

  constructor() {
    this._user_profile.set(ROLES['staff']);
    
    this.auth0.isAuthenticated$.subscribe(is_auth => {
      this._is_authenticated.set(is_auth);
      if (is_auth) {
        this.fetch_db_profile();
      }
    });
  }

  readonly role = this._role.asReadonly();
  readonly is_authenticated = this._is_authenticated.asReadonly();
  readonly user = this._user_profile.asReadonly();
  readonly is_registered = this._is_registered.asReadonly();
  readonly is_approved = this._is_approved.asReadonly();
  readonly profile_loaded = this._profile_loaded.asReadonly();

  /** Check if the current role has a specific permission. Use in templates: auth.can('manage:beacons') */
  can(permission: Permission): boolean {
    return hasPermission(this._role(), permission);
  }

  fetch_db_profile() {
    this._profile_loaded.set(false);
    this.auth0.getAccessTokenSilently().pipe(
      take(1),
      switchMap(token => {
        const headers = new HttpHeaders({ Authorization: `Bearer ${token}` });
        return this.http.get<Envelope<DbProfile>>(`${this.apiUrl}/auth/me`, { headers }).pipe(
          unwrap(),
          catchError(err => {
            const body = err.error as ApiError | undefined;
            if (err.status === 404 || body?.error === 'employee_not_found') {
              return of(null);
            }
            console.error(
              '[AuthService] fetch_db_profile failed:',
              err.status,
              body?.error ?? 'unknown_error',
              body?.message ?? err.message
            );
            return of(undefined);
          })
        );
      }),
      catchError(err => {
        console.error('[AuthService] Could not get access token:', err);
        return of(undefined);
      })
    ).subscribe(profile => {
      if (profile === undefined) {
        this._profile_loaded.set(true);
        return;
      }
      if (profile === null) {
        this._is_registered.set(false);
        this._is_approved.set(false);
        this._profile_loaded.set(true);
        this.router.navigate(['/onboarding']);
      } else {
        this._is_registered.set(true);
        this._is_approved.set(profile.is_approved);
        
        const role_key = (profile.role_name || 'staff') as RoleKey;
        this._role.set(role_key);
        const default_profile = ROLES[role_key] || ROLES['staff'];
        const initials = `${(profile.first_name || 'U')[0]}${(profile.last_name || 'U')[0]}`.toUpperCase();
        
        let display_role = default_profile.role;
        if (profile.department_name) {
          const formatted_dept = profile.department_name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
          display_role = `${default_profile.first_name} · ${formatted_dept}`;
        }

        this._user_profile.set({
          ...default_profile,
          first_name: profile.first_name,
          name: `${profile.first_name} ${profile.last_name}`,
          initials: initials,
          role: display_role,
          standard_shift: profile.standard_shift || 'morning',
          shift_type: profile.shift_type || 'standard',
          shift_hours: profile.shift_hours || '7am-5pm',
          custom_shift_start: profile.custom_shift_start,
          custom_shift_end: profile.custom_shift_end
        });

        const approved = profile.is_approved;
        this._is_approved.set(approved);
        this._profile_loaded.set(true);

        if (!approved) {
          this.router.navigate(['/pending']);
        } else if (window.location.pathname.includes('/onboarding') || window.location.pathname.includes('/pending')) {
          this.router.navigate(['/home']);
        }
      }
    });
  }

  register_user(
    first_name: string,
    last_name: string,
    shift_type = 'standard',
    shift_hours = '7am-5pm',
    custom_shift_start?: string,
    custom_shift_end?: string
  ) {
    // Grab the real email from Auth0's ID token profile!
    return this.auth0.user$.pipe(
      take(1),
      switchMap(auth_user => {
        return this.http.post<Envelope<RegisterResponse>>(`${this.apiUrl}/auth/register`, {
          first_name: first_name,
          last_name: last_name,
          shift_type: shift_type,
          shift_hours: shift_hours,
          custom_shift_start: custom_shift_start,
          custom_shift_end: custom_shift_end,
          email: auth_user?.email // Send the real email to the backend!
        });
      }),
      unwrap(),
      map(res => {
        this.fetch_db_profile(); // Reload the profile which will automatically redirect to /pending
        return res;
      })
    );
  }

  getOrganizationBySubdomain(subdomain: string) {
    return this.http
      .get<Envelope<{ id: string; name: string; domain: string; is_active: boolean }>>(
        `${this.apiUrl}/auth/organization-by-subdomain/${subdomain}`
      )
      .pipe(unwrap());
  }

  login(subdomain?: string): void {
    if (subdomain) {
      this.getOrganizationBySubdomain(subdomain).subscribe({
        next: (res) => {
          this.auth0.loginWithRedirect({
            appState: { target: '/home' },
            authorizationParams: {
              organization: res.id
            }
          });
        },
        error: (err) => {
          console.error('[AuthService] Subdomain resolution failed:', err);
          this.auth0.loginWithRedirect({ appState: { target: '/home' } });
        }
      });
    } else {
      this.auth0.loginWithRedirect({ appState: { target: '/home' } });
    }
  }

  logout(): void {
    this.auth0.logout({ logoutParams: { returnTo: window.location.origin } });
  }

  /**
   * Demo-only role switcher, backing the "View as" control in the sidebar.
   *
   * This grants itself approval and marks the profile loaded, so outside demo
   * mode it is a client-side privilege escalation against the UI. The server
   * still enforces `roles_required`, so it never widened data access — but it
   * let a signed-in user reach admin screens they should not see.
   */
  set_role(role: RoleKey): void {
    if (!is_demo_mode()) {
      console.warn('[AuthService] set_role() ignored: only available in demo mode.');
      return;
    }
    this._role.set(role);
    this._user_profile.set(ROLES[role]);
    this._is_approved.set(true);
    this._is_registered.set(true);
    this._profile_loaded.set(true);
    if (window.location.pathname.includes('/pending') || window.location.pathname.includes('/onboarding')) {
      this.router.navigate(['/home']);
    }
  }
}
