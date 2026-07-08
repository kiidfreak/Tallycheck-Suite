import { ChangeDetectionStrategy, Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { SidebarComponent } from './sidebar.component';
import { HeaderComponent } from './header.component';

/**
 * App chrome — sidebar + header wrapping the routed content.
 * Ported from the app-shell layout in index.html. Used as a layout route:
 * authenticated screens render inside <router-outlet>.
 */
@Component({
  selector: 'omni-shell',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterOutlet, SidebarComponent, HeaderComponent],
  template: `
    <div class="app-shell">
      <omni-sidebar />
      <div class="app-main">
        <omni-header />
        <main class="content">
          <router-outlet />
        </main>
      </div>
    </div>
  `,
  styles: [
    `
      .app-shell {
        display: flex;
        min-height: 100vh;
        background: var(--bg-app);
      }
      .app-main {
        display: flex;
        flex-direction: column;
        min-width: 0;
        flex: 1;
      }
      .content {
        flex: 1;
        min-width: 0;
      }
    `,
  ],
})
export class ShellComponent {}
