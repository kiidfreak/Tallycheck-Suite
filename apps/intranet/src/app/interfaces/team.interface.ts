export interface DashboardStats {
  total_headcount: number;
  present_today: number;
  absent_today: number;
  currently_clocked_in: number;
  attendance_rate_today: number;
  late_arrivals: number;
  remote_today: number;
  pending_corrections: number;
}

export interface TimelineRecord {
  clock_in: string | null;
  clock_out: string | null;
  status: 'open' | 'closed' | 'corrected';
  notes: string | null;
}

export interface TimelineEmployee {
  employee_id: string;
  first_name: string;
  last_name: string;
  initials: string;
  department: string;
  records: TimelineRecord[];
}

export interface TimelineResponse {
  date: string;
  data: TimelineEmployee[];
}
