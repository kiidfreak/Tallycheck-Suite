import { ChangeDetectionStrategy, Component, input, OnDestroy, OnInit, signal } from '@angular/core';

/** A reusable timer that calculates and displays elapsed time since a given start ISO timestamp. */
@Component({
  selector: 'omni-timer',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `{{ elapsedTime() }}`
})
export class TimerComponent implements OnInit, OnDestroy {
  /** The starting ISO date-string of the active shift. */
  readonly startTime = input.required<string>();

  readonly elapsedTime = signal('0h 0m 0s');
  private timerId: ReturnType<typeof setInterval> | null = null;

  ngOnInit(): void {
    this.start();
  }

  ngOnDestroy(): void {
    this.stop();
  }

  private start(): void {
    this.stop();
    const clockInTime = new Date(this.startTime()).getTime();
    const update = () => {
      const elapsedMs = Math.max(0, Date.now() - clockInTime);
      const totalSecs = Math.floor(elapsedMs / 1000);
      const hours = Math.floor(totalSecs / 3600);
      const minutes = Math.floor((totalSecs % 3600) / 60);
      const seconds = totalSecs % 60;
      this.elapsedTime.set(`${hours}h ${minutes}m ${seconds}s`);
    };
    update();
    this.timerId = setInterval(update, 1000);
  }

  private stop(): void {
    if (this.timerId) {
      clearInterval(this.timerId);
      this.timerId = null;
    }
  }
}
