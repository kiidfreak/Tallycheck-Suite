export interface ReportEmployeeAttendance {
  employee_id: string;
  employee_name: string;
  department: string;
  total_days_present: number;
  total_days_absent: number;
  total_hours_worked: number;
  avg_clock_in: string | null;
  avg_clock_out: string | null;
  late_days: number;
}

export interface ReportDepartmentAttendance {
  department_id: number;
  department_name: string;
  date_from: string | null;
  date_to: string | null;
  total_employees: number;
  avg_attendance_rate: number;
  total_hours_worked: number;
  employees: ReportEmployeeAttendance[];
}

export interface DashboardMetrics {
  total_headcount: number;
  present_today: number;
  absent_today: number;
  currently_clocked_in: number;
  attendance_rate_today: number;
  late_arrivals: number;
  remote_today: number;
  pending_corrections: number;
}

export interface PaginatedReportAttendance {
  data: ReportEmployeeAttendance[];
  meta: {
    page: number;
    per_page: number;
    total: number;
    pages: number;
  };
}

export interface ReportTrendData {
  date: string;
  total_hours: number;
}
