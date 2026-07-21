import { ChangeDetectionStrategy, Component, Input } from '@angular/core';

/** Port of shared.jsx <Button>. Variants/sizes map to the prototype's btn classes. */
@Component({
  selector: 'omni-button',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <button [type]="type" [class]="'btn btn-' + variant + (size ? ' btn-' + size : '')" [disabled]="disabled">
      <ng-content></ng-content>
    </button>
  `,
  styles: [
    `
      .btn {
        display: inline-flex;
        align-items: center;
        gap: var(--space-2);
        font-family: var(--font-body);
        font-weight: var(--fw-semibold);
        font-size: var(--text-md);
        line-height: 1;
        padding: 10px 16px;
        border-radius: var(--radius-lg);
        border: 1px solid transparent;
        cursor: pointer;
        transition: background 0.15s ease, border-color 0.15s ease, color 0.15s ease;
      }
      .btn:disabled {
        opacity: 0.5;
        cursor: not-allowed;
      }
      .btn:focus-visible {
        outline: none;
        box-shadow: var(--shadow-focus);
      }
      .btn-primary {
        background: var(--brand-700);
        color: var(--text-on-brand);
      }
      .btn-primary:hover {
        background: var(--brand-600);
      }
      .btn-secondary {
        background: var(--surface-base);
        color: var(--text-primary);
        border-color: var(--border-strong);
      }
      .btn-secondary:hover {
        background: var(--surface-hover);
      }
      .btn-ghost {
        background: transparent;
        color: var(--text-secondary);
      }
      .btn-ghost:hover {
        background: var(--surface-hover);
      }
      .btn-danger {
        background: var(--accent-600);
        color: var(--text-on-accent);
      }
      .btn-danger:hover {
        background: var(--accent-700);
      }
      .btn-sm {
        padding: 6px 12px;
        font-size: var(--text-sm);
      }
      .btn-lg {
        padding: 12px 20px;
        font-size: var(--text-lg);
      }
    `,
  ],
})
export class ButtonComponent {
  @Input() variant: 'primary' | 'secondary' | 'ghost' | 'danger' = 'primary';
  @Input() size?: 'sm' | 'lg';
  @Input() type: 'button' | 'submit' | 'reset' = 'button';
  @Input() disabled = false;
}
