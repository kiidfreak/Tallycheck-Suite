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
        font-size: var(--fs-xs);
        font-weight: var(--fw-semibold);
        padding: 4px 10px;
        border-radius: var(--radius-pill);
        line-height: 1.4;
      }
      .dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background: currentColor;
      }
      .pill-info {
        background: var(--info-100);
        color: var(--info);
      }
      .pill-success {
        background: var(--success-100);
        color: var(--success);
      }
      .pill-warning {
        background: var(--warning-100);
        color: var(--warning);
      }
      .pill-danger {
        background: var(--danger-100);
        color: var(--danger);
      }
      .pill-purple {
        background: #ece9fb;
        color: var(--status-remote);
      }
      .pill- {
        background: var(--info-100);
        color: var(--info);
      }
    `,
  ],
})
export class PillComponent {
  @Input() tone: 'info' | 'success' | 'warning' | 'danger' | 'purple' | '' = 'info';
}
