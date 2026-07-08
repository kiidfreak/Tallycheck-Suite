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
        font-size: var(--fs-md);
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
        background: var(--adept-navy-700);
        color: var(--fg-on-navy);
      }
      .btn-primary:hover {
        background: var(--adept-navy-600);
      }
      .btn-secondary {
        background: var(--bg-surface);
        color: var(--fg-1);
        border-color: var(--border-2);
      }
      .btn-secondary:hover {
        background: var(--bg-hover);
      }
      .btn-ghost {
        background: transparent;
        color: var(--fg-2);
      }
      .btn-ghost:hover {
        background: var(--bg-hover);
      }
      .btn-danger {
        background: var(--adept-red-600);
        color: var(--fg-on-red);
      }
      .btn-danger:hover {
        background: var(--adept-red-700);
      }
      .btn-sm {
        padding: 6px 12px;
        font-size: var(--fs-sm);
      }
      .btn-lg {
        padding: 12px 20px;
        font-size: var(--fs-lg);
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
