import { ChangeDetectionStrategy, Component, HostListener, signal } from '@angular/core';
import { NavigationEnd, Router, RouterOutlet } from '@angular/router';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { filter } from 'rxjs';
import { SidebarComponent } from './sidebar.component';
import { HeaderComponent } from './header.component';

/**
 * App chrome — sidebar + header wrapping the routed content. Used as a layout
 * route: authenticated screens render inside <router-outlet>.
 *
 * Below the tablet breakpoint the sidebar becomes an overlay drawer. It stays
 * in the DOM and is moved off-canvas with a transform, so nav state and focus
 * order are identical at every width and the markup does not fork.
 */
@Component({
  selector: 'omni-shell',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterOutlet, SidebarComponent, HeaderComponent],
  template: `
    <div class="app-shell" [class.nav-open]="navOpen()">
      @if (navOpen()) {
        <button
          type="button"
          class="nav-scrim"
          aria-label="Close navigation"
          (click)="closeNav()"
        ></button>
      }

      <omni-sidebar />

      <div class="app-main">
        <omni-header [navOpen]="navOpen()" (menuToggle)="toggleNav()" />
        <main class="content">
          <router-outlet />
        </main>
      </div>
    </div>
  `,
  styleUrl: './shell.component.scss',
})
export class ShellComponent {
  readonly navOpen = signal(false);

  constructor(router: Router) {
    // Navigating from the drawer must dismiss it, or the new page renders
    // behind an open overlay.
    router.events
      .pipe(
        filter((e) => e instanceof NavigationEnd),
        takeUntilDestroyed()
      )
      .subscribe(() => this.closeNav());
  }

  toggleNav(): void {
    this.navOpen.update((open) => !open);
  }

  closeNav(): void {
    this.navOpen.set(false);
  }

  @HostListener('document:keydown.escape')
  onEscape(): void {
    this.closeNav();
  }
}
