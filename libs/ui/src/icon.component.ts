import { ChangeDetectionStrategy, Component, Input } from '@angular/core';
import { LucideAngularModule } from 'lucide-angular';

/**
 * Port of shared.jsx <Icon>. Thin wrapper over lucide-angular so the rest of the
 * app uses the prototype's kebab-case icon names directly (e.g. "bar-chart-3").
 * The full icon set is registered once in app.config via LucideAngularModule.pick(icons).
 */
@Component({
  selector: 'omni-icon',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [LucideAngularModule],
  template: `<lucide-icon
    [name]="name"
    [size]="size"
    [strokeWidth]="strokeWidth"
    [class]="'omni-icon'"
  ></lucide-icon>`,
  styles: [
    `
      :host {
        display: inline-flex;
      }
      .omni-icon {
        color: currentColor;
      }
    `,
  ],
})
export class IconComponent {
  @Input({ required: true }) name!: string;
  @Input() size = 16;
  @Input() strokeWidth = 1.75;
}
