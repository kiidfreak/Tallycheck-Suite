import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { toSignal } from '@angular/core/rxjs-interop';
import { map } from 'rxjs';
import { CardComponent, IconComponent } from '@omni/ui';

/**
 * Temporary screen for nav targets not yet ported from the prototype.
 * Reads { title, icon } from route data. Replace with the real feature component
 * as each screen is migrated.
 */
@Component({
  selector: 'app-placeholder',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CardComponent, IconComponent],
  template: `
    <section class="wrap">
      <header class="page-head">
        <div>
          <p class="eyebrow">TallyCheck</p>
          <h1>{{ data().title }}</h1>
        </div>
      </header>
      <omni-card>
        <div class="empty">
          <div class="badge"><omni-icon [name]="data().icon" [size]="26" /></div>
          <div class="t">{{ data().title }} — coming soon</div>
          <p class="b">
            This screen is being ported from the prototype to Angular. The shell, navigation,
            theme and auth are live; the screen content lands next.
          </p>
        </div>
      </omni-card>
    </section>
  `,
  styles: [
    `
      .wrap {
        max-width: var(--content-max);
        margin: 0 auto;
        padding: var(--space-8);
      }
      .page-head {
        margin-bottom: var(--space-6);
      }
      .empty {
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
        gap: var(--space-3);
        padding: var(--space-10) var(--space-4);
        color: var(--fg-3);
      }
      .badge {
        width: 56px;
        height: 56px;
        border-radius: var(--radius-lg);
        display: flex;
        align-items: center;
        justify-content: center;
        background: var(--adept-navy-50);
        color: var(--adept-navy-700);
      }
      .t {
        font-family: var(--font-display);
        font-weight: var(--fw-semibold);
        font-size: var(--fs-lg);
        color: var(--fg-1);
      }
      .b {
        max-width: 420px;
        font-size: var(--fs-sm);
      }
    `,
  ],
})
export class PlaceholderComponent {
  private readonly route = inject(ActivatedRoute);
  readonly data = toSignal(
    this.route.data.pipe(
      map((d) => ({ title: (d['title'] as string) ?? 'Screen', icon: (d['icon'] as string) ?? 'square' })),
    ),
    { initialValue: { title: 'Screen', icon: 'square' } },
  );
}
