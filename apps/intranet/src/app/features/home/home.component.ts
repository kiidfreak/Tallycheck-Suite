import { ChangeDetectionStrategy, Component, inject, signal, computed, effect, OnDestroy, untracked } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { AuthService, UserProfile } from '@omni/auth';
import {
  CardComponent,
  StatCardComponent,
  PillComponent,
  ButtonComponent,
  AvatarComponent,
  IconComponent,
  ToastService
} from '@omni/ui';
import { AttendanceService } from '../attendance/attendance.service';
import { SafeChildService, Child } from '../safechild/safechild.service';
import { BeaconService } from '../beacons/beacon.service';
import { AttendanceRecord, ClockOutResponse } from '../../interfaces/attendance.interface';
import { LucideAngularModule } from 'lucide-angular';
import { ClockInFormComponent, ClockInSubmit } from './clock-in-form/clock-in-form.component';
import { ClockOutFormComponent } from './clock-out-form/clock-out-form.component';

/** Dynamic Home screen with Attendance clock-in/out integration. */
@Component({
  selector: 'app-home',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule,
    FormsModule,
    RouterLink,
    CardComponent,
    StatCardComponent,
    PillComponent,
    ButtonComponent,
    AvatarComponent,
    IconComponent,
    LucideAngularModule,
    ClockInFormComponent,
    ClockOutFormComponent
  ],
  templateUrl: './home.component.html',
  styleUrl: './home.component.scss'
})
export class HomeComponent implements OnDestroy {
  readonly auth = inject(AuthService);
  readonly user = this.auth.user;
  private readonly attendance_service = inject(AttendanceService);
  private readonly safechild_service = inject(SafeChildService);
  private readonly beacon_service = inject(BeaconService);

  readonly is_admin = computed(
    () => this.auth.role() === 'super_admin' || this.auth.role() === 'company_admin' || this.auth.role() === 'it_admin'
  );

  readonly beacons_total = signal(12);
  readonly beacons_online = signal(12);
  readonly management_sla = signal('99.85%');

  /**
   * True for users whose day is the children's roster rather than corporate
   * attendance — Sunday School teachers and guardians.
   *
   * Discriminated on `view:employees` rather than the SafeChild permissions
   * alone: admins and department managers also hold safechild:* but run the
   * corporate dashboard, so keying off the roster permission by itself would
   * wrongly flip them too.
   */
  readonly is_safechild_focused = computed(
    () => (this.auth.can('safechild:drop_off') || this.auth.can('safechild:manage_children')) && !this.auth.can('view:employees')
  );

  readonly is_guardian = computed(
    () => this.auth.role() === 'guardian' || (this.auth.can('safechild:my_children') && !this.auth.can('safechild:drop_off'))
  );

  readonly my_children = computed(() => {
    const user = this.auth.user();
    const userName = (user?.name || user?.first_name || 'Grace').toLowerCase();
    
    const myKids = this.children().filter(c => 
      c.guardians.some(g => g.name.toLowerCase().includes(userName) || userName.includes(g.name.toLowerCase().split(' ')[0]))
    );

    return myKids.length ? myKids : this.children().slice(0, 1);
  });

  readonly children = signal<Child[]>([]);
  readonly children_loading = signal(false);

  readonly children_total = computed(() => this.children().length);
  readonly children_checked_in = computed(
    () => this.children().filter((c) => c.status === 'checked_in').length
  );
  readonly children_picked_up = computed(
    () => this.children().filter((c) => c.status === 'released' || c.status === 'picked_up').length
  );
  readonly children_awaiting = computed(
    () => Math.max(0, this.children_total() - this.children_checked_in())
  );
  readonly attendance_rate = computed(() => {
    const total = this.children_total();
    if (total === 0) return '0%';
    return `${Math.round((this.children_checked_in() / total) * 100)}%`;
  });

  readonly selected_child_ids = signal<string[]>([]);

  toggle_child_selection(id: string): void {
    this.selected_child_ids.update(ids => 
      ids.includes(id) ? ids.filter(i => i !== id) : [...ids, id]
    );
  }

  toggle_all_selection(): void {
    if (this.selected_child_ids().length === this.children().length) {
      this.selected_child_ids.set([]);
    } else {
      this.selected_child_ids.set(this.children().map(c => c.id));
    }
  }

  bulk_check_in(): void {
    const ids = this.selected_child_ids();
    if (ids.length === 0) return;
    this.children.update(list => list.map(c => ids.includes(c.id) ? { ...c, status: 'checked_in' } : c));
    this.toast_service.show(`Bulk checked in ${ids.length} children`, 'success');
    this.selected_child_ids.set([]);
  }

  bulk_release(): void {
    const ids = this.selected_child_ids();
    if (ids.length === 0) return;
    this.children.update(list => list.map(c => ids.includes(c.id) ? { ...c, status: 'released' } : c));
    this.toast_service.show(`Bulk verified & released ${ids.length} children to guardians`, 'success');
    this.selected_child_ids.set([]);
  }

  load_children(): void {
    this.children_loading.set(true);
    this.safechild_service.getChildren().subscribe({
      next: (rows) => {
        this.children.set(rows ?? []);
        this.children_loading.set(false);
      },
      error: () => {
        this.children.set([]);
        this.children_loading.set(false);
      },
    });
  }
  private readonly toast_service = inject(ToastService);

  readonly loading = signal(false);
  readonly history_loaded = signal(false);
  readonly show_timesheet = signal(false);

  readonly current_date_str = signal('');

  // History state
  readonly records = signal<AttendanceRecord[]>([]);
  readonly total_records = signal(0);
  readonly active_record = signal<AttendanceRecord | null>(null);

  // Pagination & filter state
  readonly page = signal(1);
  readonly per_page = signal(10);
  start_date = '';
  end_date = '';

  // Checkout warning countdown state
  readonly show_checkout_warning = signal(false);
  readonly countdown_seconds = signal(10);
  private checkout_timeout_id: ReturnType<typeof setTimeout> | null = null;
  private countdown_interval_id: ReturnType<typeof setInterval> | null = null;

  readonly max_pages = computed(() => {
    const total = this.total_records();
    const size = this.per_page();
    return Math.max(1, Math.ceil(total / size));
  });

  readonly hours_this_week = signal('0.0');
  readonly team_present = signal<number>(0);
  readonly team_total = signal<number>(0);
  readonly streak = signal<number>(0);
  readonly greeting = signal('Good morning');
  
  // Daily work hours = 10 hrs. Sign in cutoff is at half day(5 hrs)
  readonly daily_work_hours = 10;
  readonly daily_cutoff_hours = this.daily_work_hours / 2;

  readonly show_banner = computed(() => {
    if (!this.history_loaded()) return false;
    if (this.auth.role() === 'super_admin' || this.is_safechild_focused()) return false;

    const active = this.active_record();
    if (active) return false;
    
    const list = this.records();
    const todayStr = new Date().toISOString().split('T')[0];
    const has_today_record = list.some(r => r.work_date === todayStr);
    return !has_today_record;
  });

  readonly can_clock_in = computed(() => {
    const role = this.auth.role();
    if (role === 'super_admin' || role === 'guardian' || role === 'it_admin' || role === 'teacher' || this.is_safechild_focused()) return false;
    return this.auth.can('clock:in_out');
  });

  readonly recent_history = computed(() => [
    { id: 't1', child_name: 'Amani Wanjiru', class_name: 'Hekima Class (3-5 yrs)', guardian_name: 'Grace Wanjiru', dropped_off_at: '09:12 AM', status: 'checked_in', pin: '5842' },
    { id: 't2', child_name: 'Zawadi Kimani', class_name: 'Imani Class (6-8 yrs)', guardian_name: 'Joseph Kimani', dropped_off_at: '09:05 AM', status: 'checked_in', pin: '1904' },
    { id: 't3', child_name: 'Tumaini Njeri', class_name: 'Busara Class (9-11 yrs)', guardian_name: 'Lucy Njeri', dropped_off_at: '09:22 AM', status: 'checked_in', pin: '7392' },
    { id: 't4', child_name: 'Faraja Mutua', class_name: 'Upendo Class (12-14 yrs)', guardian_name: 'Ann Mutua', dropped_off_at: '09:30 AM', status: 'released', picked_up_at: '11:45 AM', pin: '4410' },
  ]);

  readonly announcements = computed(() => {
    if (this.is_safechild_focused()) {
      return [
        {
          title: 'TallyCheck SafeChild Pickup Active',
          meta: 'Children Ministry · FEM Church Karen',
          desc: 'Welcome to FEM Church Karen SafeChild Pickup Guard! Use the Class Check-in tab to issue 4-digit PINs and QR tickets at drop-off. Guardian authorization and visual verification are required before releasing any child.',
          isNew: true
        }
      ];
    }
    return [
      { 
        title: 'Welcome to TallyCheck for Business & Education!',
        meta: 'Admin · Posted today', 
        desc: 'Welcome to TallyCheck multi-tenant attendance ecosystem. Please log your daily shifts, view course timetables, and verify BLE beacon locations for seamless attendance tracking.', 
        isNew: true
      }
    ];
  });

  quickApps = [
    { name: 'LMS', icon: 'book-open', color: 'var(--brand-700)' },
    { name: 'IdeaHub', icon: 'lightbulb', color: '#d97706' },
    { name: 'Leads Generator', icon: 'users', color: 'var(--success)' }
  ];

  deptUpdates = [
    { name: 'Engineering', count: 3, icon: 'code' },
    { name: 'Sales', count: 1, icon: 'trending-up' },
    { name: 'HR', count: 2, icon: 'users' },
    { name: 'Operations', count: 0, icon: 'settings' }
  ];

  get_hours_delta(): string {
    const hours = parseFloat(this.hours_this_week()) || 0;
    const remaining = Math.max(0, 40 - hours).toFixed(1);
    return `${remaining} / 40 to go`;
  }

  private clock_date_interval: ReturnType<typeof setInterval> | null = null;

  // Modal State
  readonly show_attendance_modal = signal(false);
  readonly modal_type = signal<'clock_in' | 'clock_out' | null>(null);
  private has_shown_cutoff_warning = false;
  
  getShiftHours(user: UserProfile) {
    const hours = user?.shift_hours;
    const work_hours = user?.shift_duration_hours ?? 10;
    let startHour = 7;
    if (hours === '9am-7pm' || hours === '9am-630pm') startHour = 9;
    else if (hours === 'custom' && user?.custom_shift_start) {
      startHour = parseInt(user.custom_shift_start.split(':')[0], 10);
    }
    return { startHour, cutoffHour: startHour + 5, endHour: startHour + Math.round(work_hours), work_hours };
  }

  readonly is_past_cutoff = computed(() => {
    const user = this.auth.user();
    if (!user) return false;
    const { cutoffHour } = this.getShiftHours(user);
    return new Date().getHours() >= cutoffHour;
  });

  readonly cutoff_time_label = computed(() => {
    const user = this.auth.user();
    if (!user) return '1200 hrs';
    const { cutoffHour } = this.getShiftHours(user);
    return `${cutoffHour}00 hrs`;
  });

  constructor() {
    // Reload history dynamically whenever currentEmployee changes
    effect(() => {
      const emp = this.user();
      untracked(() => {
        if (emp) {
          this.page.set(1);
          setTimeout(() => this.load_history(), 1000);
          if (this.is_safechild_focused()) {
            this.load_children();
          }
        } else {
          this.children.set([]);
          this.records.set([]);
          this.total_records.set(0);
          this.active_record.set(null);
          this.history_loaded.set(false);
          this.clear_checkout_timers();
        }
      });
    }, { allowSignalWrites: true });

    const updateDate = () => {
      const d = new Date();
      const time = d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      const options: Intl.DateTimeFormatOptions = { weekday: 'long', day: 'numeric', month: 'short' };
      const datePart = d.toLocaleDateString('en-GB', options);
      this.current_date_str.set(`${datePart} · ${time}`);
      
      const hour = d.getHours();
      if (hour < 12) this.greeting.set('Good morning');
      else if (hour < 17) this.greeting.set('Good afternoon');
      else this.greeting.set('Good evening');
    };
    updateDate();
    this.clock_date_interval = setInterval(() => {
      updateDate();
      this.check_attendance_triggers(this.active_record() || undefined); 
    }, 60000);
  }

  ngOnDestroy(): void {
    this.clear_checkout_timers();
    if (this.clock_date_interval) {
      clearInterval(this.clock_date_interval);
    }
  }

  check_attendance_triggers(active?: AttendanceRecord) {
    // Super admins are not regular employees — never prompt them to check in
    if (this.auth.role() === 'super_admin') return;

    // Don't show any modal until the user profile is fully loaded
    if (!this.auth.user()?.shift_hours) return;

    if (this.show_attendance_modal() || localStorage.getItem('snooze_clock_out')) {
      // Check if snooze expired
      const snoozeStr = localStorage.getItem('snooze_clock_out');
      if (snoozeStr && new Date().getTime() > parseInt(snoozeStr, 10)) {
        localStorage.removeItem('snooze_clock_out');
      } else if (snoozeStr || this.show_attendance_modal()) {
        return;
      }
    }

    const now = new Date();
    const todayStr = now.toISOString().split('T')[0];
    const has_record_today = this.records().some(r => r.work_date === todayStr);

    if (localStorage.getItem('dismissed_clock_in') === todayStr) {
      // User manually dismissed the check-in modal for today. Do not prompt.
      return;
    }

    const user = this.auth.user();
    const { startHour, cutoffHour } = this.getShiftHours(user!);

    // Clock In
    if (!has_record_today && !active) {
      const promptHour = startHour;

      if (now.getHours() >= promptHour) {
        if (now.getHours() >= cutoffHour) {
          if (!this.has_shown_cutoff_warning) {
            this.has_shown_cutoff_warning = true;
            this.modal_type.set('clock_in');
            setTimeout(() => this.show_attendance_modal.set(true), 0);
          }
        } else {
          this.modal_type.set('clock_in');
          setTimeout(() => this.show_attendance_modal.set(true), 0);
        }
      }
    }

    // Clock Out
    if (active) {
      const { work_hours } = this.getShiftHours(this.auth.user()!);
      const clockInTime = new Date(active.clock_in);
      const elapsedMs = now.getTime() - clockInTime.getTime();
      const elapsedHours = elapsedMs / (1000 * 60 * 60);
      if (elapsedHours >= work_hours) {
        this.modal_type.set('clock_out');
        setTimeout(() => this.show_attendance_modal.set(true), 0);
      }
    }
  }

  snooze_clock_out(): void {
    const snoozeUntil = new Date().getTime() + (60 * 60 * 1000); // 60 mins (1 hour)
    localStorage.setItem('snooze_clock_out', snoozeUntil.toString());
    this.show_attendance_modal.set(false);
  }


  dismiss_if_cutoff(): void {
    if (this.is_past_cutoff() && this.modal_type() === 'clock_in') {
      this.dismiss_modal();
    }
  }

  dismiss_modal(): void {
    if (this.modal_type() === 'clock_in') {
      const todayStr = new Date().toISOString().split('T')[0];
      localStorage.setItem('dismissed_clock_in', todayStr);
    }
    this.show_attendance_modal.set(false);
  }

  load_history(): void {
    this.loading.set(true);
    
    this.attendance_service.get_stats().subscribe({
      next: (stats) => {
        this.hours_this_week.set(stats.hours_this_week.toFixed(1));
        this.team_present.set(stats.team_present);
        this.team_total.set(stats.team_total);
        this.streak.set(stats.streak);
      },
      error: (err: HttpErrorResponse) => {
        console.error('Error loading stats:', err);
      }
    });

    this.attendance_service.get_history({
      date_from: this.start_date || undefined,
      date_to: this.end_date || undefined,
      page: this.page(),
      per_page: this.per_page()
    }).subscribe({
      next: (data) => {
        this.records.set(data.records);
        this.total_records.set(data.total);

        const active = data.records.find(r => r.clock_out === null && r.status === 'open');

        if (active) {
          this.active_record.set(active);
          this.schedule_checkout_warning(active);
        } else {
          this.active_record.set(null);
          this.clear_checkout_timers();
        }

        this.check_attendance_triggers(active);
        this.history_loaded.set(true);
        this.loading.set(false);
      },
      error: (err: HttpErrorResponse) => {
        console.error('Error loading timesheet:', err);
        this.loading.set(false);
      }
    });
  }

  scrollToCheckIn(): void {
    const el = document.querySelector('.check-in-col');
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'center' });
      const card = el.querySelector('omni-card');
      if (card) {
        card.classList.add('highlight-flash');
        setTimeout(() => card.classList.remove('highlight-flash'), 1000);
      }
    }
  }

  clock_in(payload: ClockInSubmit): void {
    if (this.loading()) return;
    this.loading.set(true);
    
    // We append the location into the note for backend simplicity
    const combinedNote = `[${payload.location}] ${payload.note}`.trim();
    
    this.attendance_service.clock_in(combinedNote).subscribe({
      next: (record: AttendanceRecord) => {
        this.active_record.set(record);
        this.schedule_checkout_warning(record);
        this.show_attendance_modal.set(false);
        this.loading.set(false);
        this.load_history();
      },
      error: (err: HttpErrorResponse) => {
        this.toast_service.show(err.error?.message || 'Failed to clock in.', 'error');
        this.loading.set(false);
      }
    });
  }

  clock_out(note: string): void {
    if (this.loading()) return;
    this.loading.set(true);
    this.attendance_service.clock_out(note || undefined).subscribe({
      next: (res: ClockOutResponse) => {
        // Support direct data or unwrapped by interceptor
        const data = res.data || res;
        if (data && data.cancelled) {
          this.toast_service.show(res.message || "Attendance does not count. Shift too short.", 'warning');
        }
        
        this.active_record.set(null);
        this.clear_checkout_timers();
        this.show_checkout_warning.set(false);
        this.show_attendance_modal.set(false);
        this.loading.set(false);
        this.load_history();
      },
      error: (err: HttpErrorResponse) => {
        this.toast_service.show(err.error?.message || 'Failed to clock out.', 'error');
        this.loading.set(false);
      }
    });
  }

  toggle_timesheet(): void {
    this.show_timesheet.update(v => !v);
  }

  request_leave(): void {
    // In a real implementation, this would open a modal to submit a leave request.
    // That request would then appear on the HR team dashboard under "Pending correction requests".
    alert("Leave request form would open here. Once submitted, it will be visible on the HR page as a pending request!");
  }

  apply_filters(): void {
    this.page.set(1);
    this.load_history();
  }

  clear_filters(): void {
    this.start_date = '';
    this.end_date = '';
    this.page.set(1);
    this.load_history();
  }

  prev_page(): void {
    if (this.page() > 1) {
      this.page.update(p => p - 1);
      this.load_history();
    }
  }

  next_page(): void {
    if (this.page() < this.max_pages()) {
      this.page.update(p => p + 1);
      this.load_history();
    }
  }

  format_time(isoStr: string): string {
    if (!isoStr) return '';
    const date = new Date(isoStr);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  private schedule_checkout_warning(active: AttendanceRecord): void {
    this.clear_checkout_timers();

    const clockInTime = new Date(active.clock_in).getTime();
    const now = Date.now();
    const standardLimitMs = this.daily_work_hours * 60 * 60 * 1000; // 10 hours
    const hardLimitTime = clockInTime + standardLimitMs;
    let targetTime = hardLimitTime;

    const snoozeStr = localStorage.getItem('snooze_clock_out');
    if (snoozeStr) {
      const snoozeTime = parseInt(snoozeStr, 10);
      if (snoozeTime > now) {
        targetTime = snoozeTime;
      } else {
        localStorage.removeItem('snooze_clock_out');
      }
    }

    const delay = targetTime - now;
    if (delay <= 0) {
      this.start_checkout_countdown();
    } else {
      this.checkout_timeout_id = setTimeout(() => {
        this.start_checkout_countdown();
      }, delay);
    }
  }

  private start_checkout_countdown(): void {
    if (this.countdown_interval_id) return;
    this.show_checkout_warning.set(true);
    this.countdown_seconds.set(10);

    this.countdown_interval_id = setInterval(() => {
      this.countdown_seconds.update(s => s - 1);
      if (this.countdown_seconds() <= 0) {
        this.clear_checkout_timers();
        this.show_checkout_warning.set(false);
        this.auto_clock_out();
      }
    }, 1000);
  }

  private auto_clock_out(): void {
    this.clock_out('System Auto Checkout (10 Hours Limit)');
  }

  extend_shift(): void {
    this.clear_checkout_timers();
    this.show_checkout_warning.set(false);

    // Snooze/Extend for 1 hour
    const snoozeUntil = Date.now() + (60 * 60 * 1000); // 1 hour
    localStorage.setItem('snooze_clock_out', snoozeUntil.toString());

    const active = this.active_record();
    if (active) {
      this.schedule_checkout_warning(active);
    }
  }

  private clear_checkout_timers(): void {
    if (this.checkout_timeout_id) {
      clearTimeout(this.checkout_timeout_id);
      this.checkout_timeout_id = null;
    }
    if (this.countdown_interval_id) {
      clearInterval(this.countdown_interval_id);
      this.countdown_interval_id = null;
    }
  }
}
