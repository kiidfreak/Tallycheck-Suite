import { ChangeDetectionStrategy, Component, inject, signal, computed, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule } from 'lucide-angular';
import { TeamService } from './team.service';
import { DashboardStats, TimelineEmployee, TimelineRecord } from '../../interfaces/team.interface';
import { PendingUser } from '../../interfaces/users.interface';
import { AuthService } from '@omni/auth';
import { CardComponent, StatCardComponent, PillComponent, ButtonComponent, AvatarComponent, IconComponent, FormatLabelPipe } from '@omni/ui';

@Component({
  selector: 'app-team',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule,
    LucideAngularModule,
    CardComponent,
    StatCardComponent,
    PillComponent,
    ButtonComponent,
    AvatarComponent,
    IconComponent,
    FormatLabelPipe
  ],
  styleUrls: ['./team.component.scss'],
  templateUrl: './team.component.html'
})
export class TeamComponent implements OnInit {
  private readonly team_service = inject(TeamService);
  private readonly auth_service = inject(AuthService);

  readonly role = this.auth_service.role;
  readonly pending_users = signal<PendingUser[]>([]);

  stats = signal<DashboardStats | null>(null);
  employees = signal<TimelineEmployee[]>([]);

  selectedDepartment = signal<string>('All departments');
  selectedTime = signal<string>('Today');

  departments = computed(() => {
    const emps = this.employees();
    const depts = new Set(emps.map(e => e.department));
    return ['All departments', ...Array.from(depts)].sort();
  });

  filteredEmployees = computed(() => {
    const emps = this.employees();
    const dept = this.selectedDepartment();
    if (dept === 'All departments') return emps;
    return emps.filter(e => e.department === dept);
  });

  Math = Math; // Make Math available in template

  ngOnInit() {
    this.load_data();
  }

  load_data() {
    this.team_service.get_dashboard_stats().subscribe(s => this.stats.set(s));
    this.team_service.get_timeline().subscribe(res => {
      this.employees.set(res.data);
    });

    const current_role = this.role();
    if (current_role === 'hr_admin' || current_role === 'department_manager' || current_role === 'super_admin') {
      this.team_service.get_pending_users().subscribe(users => {
        this.pending_users.set(users);
      });
    }
  }

  approveUser(userId: string) {
    this.team_service.approve_user(userId).subscribe(() => {
      this.load_data();
    });
  }

  rejectUser(userId: string) {
    this.team_service.reject_user(userId).subscribe(() => {
      this.load_data();
    });
  }

  format_date(dateStr: string): string {
    if (!dateStr) return '';
    const d = new Date(dateStr);
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    return `${d.getDate()} ${months[d.getMonth()]}`;
  }

  get_relative_time(dateStr: string): string {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) {
      return 'Just now';
    } else if (diffMins < 60) {
      return `${diffMins}m ago`;
    } else if (diffHours < 24) {
      return `${diffHours}h ago`;
    } else if (diffDays === 1) {
      return 'Yesterday';
    } else {
      return `${diffDays} days ago`;
    }
  }

  get_user_initials(emp: PendingUser): string {
    const f = emp.first_name ? emp.first_name[0] : '';
    const l = emp.last_name ? emp.last_name[0] : '';
    return (f + l).toUpperCase() || 'EE';
  }

  get_avatar_tone(emp: TimelineEmployee): '' | 'success' | 'warning' | 'purple' {
    if (emp.records.length === 0) return '';
    const has_active = emp.records.some((r: TimelineRecord) => !r.clock_out);
    return has_active ? 'success' : 'purple'; 
  }

  onDepartmentChange(event: Event) {
    const select = event.target as HTMLSelectElement;
    this.selectedDepartment.set(select.value);
  }

  is_remote(record: TimelineRecord): boolean {
    return record.notes?.includes('[Remote]') ?? false;
  }

  format_time(isoString: string | null): string {
    if (!isoString) return '';
    const d = new Date(isoString);
    // For local display (ensure consistent timezone if needed, here just HH:MM)
    const h = d.getHours().toString().padStart(2, '0');
    const m = d.getMinutes().toString().padStart(2, '0');
    return `${h}:${m}`;
  }

  /**
   * Calculates left percentage relative to 08:00 (0%) and 18:00 (100%).
   */
  calculate_left(clockIn: string): string {
    const d = new Date(clockIn);
    let hours = d.getHours() + d.getMinutes() / 60;
    
    // Clamp to 08:00 boundary
    if (hours < 8) hours = 8;
    
    const pct = ((hours - 8) / 10) * 100;
    return `${Math.max(0, Math.min(100, pct))}%`;
  }

  /**
   * Calculates width relative to 10 hour window (08:00 - 18:00)
   */
  calculate_width(clockIn: string, clockOut: string | null): string {
    const dIn = new Date(clockIn);
    let inHours = dIn.getHours() + dIn.getMinutes() / 60;
    if (inHours < 8) inHours = 8;

    let outHours: number;
    if (clockOut) {
      const dOut = new Date(clockOut);
      outHours = dOut.getHours() + dOut.getMinutes() / 60;
    } else {
      const now = new Date();
      outHours = now.getHours() + now.getMinutes() / 60;
    }

    if (outHours > 18) outHours = 18;

    const duration = outHours - inHours;
    if (duration <= 0) return '0%';

    const pct = (duration / 10) * 100;
    return `${Math.min(100, pct)}%`;
  }
}
