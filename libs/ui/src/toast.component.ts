import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ToastService } from './toast.service';
import { LucideAngularModule } from 'lucide-angular';

@Component({
  selector: 'omni-toast',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    @if (toastService.currentToast(); as toast) {
      <div class="omni-toast">
        <div [class]="'toast-icon-container ' + (toast.type || 'info')">
          <lucide-icon [name]="getIconName(toast.type)" [size]="20"></lucide-icon>
        </div>
        <span>{{ toast.text }}</span>
      </div>
    }
  `,
  styles: [`
    .omni-toast {
      position: fixed;
      bottom: 24px;
      right: 24px;
      background: var(--brand-ink, #0a2540);
      color: white;
      padding: 16px 20px;
      border-radius: var(--radius-md, 8px);
      box-shadow: var(--shadow-xl, 0 20px 25px -5px rgba(0,0,0,0.1), 0 10px 10px -5px rgba(0,0,0,0.04));
      z-index: 10000;
      display: flex;
      align-items: center;
      gap: 12px;
      font-size: 0.9rem;
      max-width: 400px;
      animation: toastSlideUp 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards;
      .toast-icon-container {
        display: flex;
        align-items: center;
        justify-content: center;
        &.info { color: #3b82f6; }
        &.success { color: var(--success, #10b981); }
        &.warning { color: var(--warning, #f59e0b); }
        &.error { color: var(--danger, #ef4444); }
      }
    }
    @keyframes toastSlideUp {
      from { transform: translateY(100%); opacity: 0; }
      to { transform: translateY(0); opacity: 1; }
    }
  `]
})
export class ToastComponent {
  readonly toastService = inject(ToastService);

  getIconName(type?: string): string {
    switch (type) {
      case 'success': return 'circle-check';
      case 'warning': return 'triangle-alert';
      case 'error': return 'circle-x';
      default: return 'info';
    }
  }
}
