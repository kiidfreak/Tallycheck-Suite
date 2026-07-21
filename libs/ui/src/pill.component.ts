import { ChangeDetectionStrategy, Component, Input } from '@angular/core';

/** Port of shared.jsx <Pill>. A status chip with a leading dot. */
@Component({
  selector: 'omni-pill',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <span [class]="'pill pill-' + tone">
      <span class="dot"></span><ng-content></ng-content>
    </span>
  `,
  styles: [
    `
      .pill {
        display: inline-flex;
        align-items: center;
        gap: var(--space-2);
        font-size: var(--text-xs);
        font-weight: var(--fw-semibold);
        padding: 4px 10px;
        border-radius: var(--radius-full);
        line-height: 1.4;
      }
      .dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background: currentColor;
      }
      .pill-info {
        background: var(--info-tint);
        color: var(--info);
      }
      .pill-success {
        background: var(--success-tint);
        color: var(--success);
      }
      .pill-warning {
        background: var(--warning-tint);
        color: var(--warning);
      }
      .pill-danger {
        background: var(--danger-tint);
        color: var(--danger);
      }
      .pill-purple {
        background: #ece9fb;
        color: var(--status-remote);
      }
      .pill- {
        background: var(--info-tint);
        color: var(--info);
      }
    `,
  ],
})
export class PillComponent {
  @Input() tone: 'info' | 'success' | 'warning' | 'danger' | 'purple' | '' = 'info';
}
