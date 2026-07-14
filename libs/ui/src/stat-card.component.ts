import { ChangeDetectionStrategy, Component, Input } from '@angular/core';
import { IconComponent } from './icon.component';

/** Port of shared.jsx <StatCard>. A metric tile with label, value and optional delta. */
@Component({
  selector: 'omni-stat-card',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [IconComponent],
  template: `
    <div class="stat-card">
      <div class="card-top">
        <span class="caption">{{ label }}</span>
        @if (infoText) {
          <omni-icon name="info" [size]="14" class="info-icon" [title]="infoText"></omni-icon>
        }
      </div>
      <div class="value">{{ value }}</div>
      @if (delta) {
        <div [class]="'delta ' + (deltaTone ?? '')" style="display: flex; align-items: center; gap: 4px;">
          @if (deltaIcon) {
            <omni-icon [name]="deltaIcon" [size]="14"></omni-icon>
          }
          <span>{{ delta }}</span>
        </div>
      }
    </div>
  `,
  styles: [
    `
      :host {
        display: block;
        height: 100%;
      }
      .stat-card {
        height: 100%;
        min-height: 110px;
        box-sizing: border-box;
        background: var(--bg-surface);
        border: 1px solid var(--border-1);
        border-radius: var(--radius-lg);
        box-shadow: var(--shadow-sm);
        padding: var(--space-5);
        display: flex;
        flex-direction: column;
        gap: var(--space-2);
        transition: transform 0.2s cubic-bezier(0.4, 0, 0.2, 1), border-color 0.2s ease, box-shadow 0.2s ease;
        
        &:hover {
          transform: translateY(-4px);
          box-shadow: var(--shadow-md);
          border-color: var(--border-2);
        }
      }
      .caption {
        font-size: 11px;
        color: var(--fg-3);
        text-transform: uppercase;
        letter-spacing: var(--tracking-wide);
        font-weight: var(--fw-bold);
      }
      .card-top {
        display: flex;
        justify-content: space-between;
        align-items: center;
      }
      .info-icon {
        color: var(--fg-4);
        cursor: help;
        transition: color 0.2s;
      }
      .info-icon:hover {
        color: var(--fg-2);
      }
      .value {
        font-family: var(--font-display);
        font-weight: var(--fw-extrabold);
        font-size: var(--fs-4xl);
        letter-spacing: var(--tracking-tight);
        color: var(--fg-brand);
        line-height: 1;
        margin: var(--space-1) 0;
      }
      .delta {
        font-size: var(--fs-xs);
        font-weight: var(--fw-semibold);
        color: var(--fg-3);
      }
      .delta.success {
        color: var(--success);
      }
      .delta.danger {
        color: var(--danger);
      }
    `,
  ],
})
export class StatCardComponent {
  @Input({ required: true }) label!: string;
  @Input({ required: true }) value!: string | number;
  @Input() infoText?: string;
  @Input() delta?: string;
  @Input() deltaIcon?: string;
  @Input() deltaTone?: 'success' | 'danger';
}
