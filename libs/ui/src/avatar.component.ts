import { ChangeDetectionStrategy, Component, Input } from '@angular/core';

/** Port of shared.jsx <Avatar>. Initials chip with tone-based color. */
@Component({
  selector: 'omni-avatar',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `<div [class]="'avatar ' + tone + (size ? ' ' + size : '')">{{ initials }}</div>`,
  styles: [
    `
      .avatar {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 36px;
        height: 36px;
        border-radius: 50%;
        font-family: var(--font-display);
        font-weight: var(--fw-semibold);
        font-size: var(--text-sm);
        background: var(--brand-100);
        color: var(--brand-700);
      }
      .avatar.success {
        background: var(--success-tint);
        color: var(--success);
      }
      .avatar.warning {
        background: var(--warning-tint);
        color: var(--warning);
      }
      .avatar.purple {
        background: #ece9fb;
        color: var(--status-remote);
      }
      .avatar.sm {
        width: 28px;
        height: 28px;
        font-size: var(--text-xs);
      }
      .avatar.lg {
        width: 48px;
        height: 48px;
        font-size: var(--text-lg);
      }
    `,
  ],
})
export class AvatarComponent {
  @Input({ required: true }) initials!: string;
  @Input() tone: '' | 'success' | 'warning' | 'purple' = '';
  @Input() size?: 'sm' | 'lg';
}
