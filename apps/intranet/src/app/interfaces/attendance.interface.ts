export interface AttendanceRecord {
  id: number;
  employee_id: string;
  clock_in: string;
  clock_out: string | null;
  work_date: string;
  source: string;
  status: 'open' | 'closed' | 'corrected';
  notes: string | null;
  worked_hours: number | null;
  edited_by?: string | null;
}

export interface PaginatedAttendance {
  records: AttendanceRecord[];
  total: number;
  page: number;
  pages: number;
  per_page: number;
}

export interface AuditLog {
  id: number;
  changed_by: string;
  record_changed: string;
  previous_clock_in: string | null;
  previous_clock_out: string | null;
  changed_at: string | null;
  reason_for_change: string;
}

export interface ClockOutResponse {
  record?: AttendanceRecord | null;
  cancelled?: boolean;
  message?: string;
  data?: {
    record?: AttendanceRecord | null;
    cancelled?: boolean;
  };
}

export interface AttendanceManualRequest {
  employee_id: string;
  work_date: string;
  clock_in: string;
  clock_out?: string | null;
  reason: string;
}

export interface AttendanceCorrectionRequest {
  clock_in: string;
  clock_out?: string | null;
  reason: string;
}