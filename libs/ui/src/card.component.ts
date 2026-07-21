import { ChangeDetectionStrategy, Component, Input } from '@angular/core';

/** Port of shared.jsx <Card>. Title/subtitle header is optional. */
@Component({
  selector: 'omni-card',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="card">
      @if (title || subtitle) {
        <div class="card-header">
          <div>
            @if (title) {
              <div class="card-title">{{ title }}</div>
            }
            @if (subtitle) {
              <div class="card-subtitle">{{ subtitle }}</div>
            }
          </div>
          <ng-content select="[card-right]"></ng-content>
        </div>
      }
      <ng-content></ng-content>
    </div>
  `,
  styles: [
    `
      :host {
        display: block;
        height: inherit;
      }
      .card {
        height: 100%;
        box-sizing: border-box;
        background: var(--surface-base);
        border: 1px solid var(--border-light);
        border-radius: var(--radius-lg);
        box-shadow: var(--shadow-sm);
        padding: var(--space-6);
        transition: border-color 0.2s ease, box-shadow 0.2s ease;
        
        &:hover {
          box-shadow: var(--shadow-md);
          border-color: var(--border-strong);
        }
      }
      .card-header {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: var(--space-3);
        margin-bottom: var(--space-5);
      }
      .card-title {
        font-family: var(--font-display);
        font-weight: var(--fw-bold);
        font-size: var(--text-lg);
        color: var(--text-primary);
      }
      .card-subtitle {
        font-size: var(--text-sm);
        color: var(--text-tertiary);
        margin-top: 4px;
      }
    `,
  ],
})
export class CardComponent {
  @Input() title?: string;
  @Input() subtitle?: string;
}
