import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'formatLabel',
  standalone: true
})
export class FormatLabelPipe implements PipeTransform {
  transform(value: string | null | undefined): string {
    if (!value) return '';
    
    return value
      .replace(/_/g, ' ')
      .split(' ')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join(' ');
  }
}
