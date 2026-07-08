import { ChangeDetectionStrategy, Component, inject, OnInit } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { AuthService as Auth0Service } from '@auth0/auth0-angular';
import { ToastComponent } from '@omni/ui';

/**
 * Root component. For now it just hosts the router outlet; once @omni/shell is
 * ported it will wrap the outlet in <omni-shell> (sidebar + header).
 */
@Component({
  standalone: true,
  imports: [RouterOutlet, ToastComponent],
  selector: 'app-root',
  template: `
    <router-outlet></router-outlet>
    <omni-toast></omni-toast>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AppComponent implements OnInit {
  private readonly auth0 = inject(Auth0Service);

  ngOnInit(): void {
    // Catch Auth0 Login/Signup errors and prevent infinite SSO loops
    this.auth0.error$.subscribe((err) => {
      if (err) {
        alert(err.message || 'Access Denied.');
        
        // Force logout to clear the stuck Auth0 SSO session
        this.auth0.logout({ logoutParams: { returnTo: window.location.origin } });
      }
    });
  }
}
