import { Injectable, signal } from '@angular/core';

export interface ToastMessage {
  text: string;
  type?: 'info' | 'success' | 'warning' | 'error';
}

@Injectable({
  providedIn: 'root'
})
export class ToastService {
  readonly currentToast = signal<ToastMessage | null>(null);
  private timerId: ReturnType<typeof setTimeout> | null = null;

  show(text: string, type: 'info' | 'success' | 'warning' | 'error' = 'info') {
    this.currentToast.set({ text, type });
    
    if (this.timerId) {
      clearTimeout(this.timerId);
    }
    
    this.timerId = setTimeout(() => {
      this.currentToast.set(null);
    }, 5000);
  }
}
