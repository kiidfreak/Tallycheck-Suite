import { Component, OnInit, inject, signal, computed, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { IconComponent, StatCardComponent, AvatarComponent, PillComponent, ButtonComponent, FormatLabelPipe } from '@omni/ui';
import { NgApexchartsModule } from 'ng-apexcharts';
import { 
  ApexAxisChartSeries,
  ApexChart,
  ApexXAxis,
  ApexTitleSubtitle,
  ApexDataLabels,
  ApexTooltip,
  ApexPlotOptions,
  ApexYAxis,
  ApexGrid,
  ApexLegend,
  ApexStroke
} from 'ng-apexcharts';
import { chartSeries, chartTheme } from '@omni/theme';

import { ActivatedRoute } from '@angular/router';
import { AuthService } from '@omni/auth';
import { ReportService } from './report.service';
import { DepartmentService } from '../departments/department.service';
import { DashboardMetrics, ReportEmployeeAttendance, ReportDepartmentAttendance, PaginatedReportAttendance, ReportTrendData } from '../../interfaces/reports.interface';
import { Department } from '../../interfaces/departments.interface';

export type ChartOptions = {
  series: ApexAxisChartSeries;
  chart: ApexChart;
  xaxis: ApexXAxis;
  yaxis: ApexYAxis & { categories?: string[] };
  title: ApexTitleSubtitle;
  dataLabels: ApexDataLabels;
  tooltip: ApexTooltip;
  plotOptions: ApexPlotOptions;
  grid: ApexGrid;
  legend: ApexLegend;
  colors: string[];
  stroke: ApexStroke;
};

@Component({
  selector: 'app-reports',
  standalone: true,
  imports: [CommonModule, FormsModule, IconComponent, NgApexchartsModule, StatCardComponent, AvatarComponent, PillComponent, ButtonComponent, FormatLabelPipe],
  templateUrl: './reports.component.html',
  styleUrls: ['./reports.component.scss']
})
export class ReportsComponent implements OnInit {
  private report_service = inject(ReportService);
  private department_service = inject(DepartmentService);
  private route = inject(ActivatedRoute);
  readonly auth = inject(AuthService);
  readonly Math = Math;

  readonly active_tab = signal<'hr' | 'safechild'>('hr');

  readonly has_safechild_access = computed(() => 
    this.auth.can('safechild:view_roster') || this.auth.can('safechild:drop_off') || this.auth.role() === 'teacher'
  );

  readonly has_hr_access = computed(() => this.auth.can('view:reports'));

  readonly is_safechild_reports = computed(() => this.active_tab() === 'safechild');

  readonly is_super_admin = computed(() => this.auth.role() === 'super_admin' || this.auth.role() === 'it_admin');
  readonly is_company_admin = computed(() => this.auth.role() === 'company_admin' || this.auth.role() === 'hr_admin' || this.auth.role() === 'department_manager');
  readonly is_individual = computed(() => !this.is_super_admin() && !this.is_company_admin());

  readonly report_title = computed(() => {
    if (this.is_safechild_reports()) return 'Sunday School Child Attendance & Ministry Analytics';
    if (this.is_super_admin()) return 'Organization-Wide Attendance & Multi-Tenant Analytics';
    if (this.is_company_admin()) return 'Company & Team Attendance Reports';
    return 'My Personal Attendance & Timesheet History';
  });

  readonly report_subtitle = computed(() => {
    if (this.is_safechild_reports()) return 'FEM Church Karen — Children Ministry Attendance & Checkout Analytics';
    if (this.is_super_admin()) return 'Platform-wide attendance compliance across tenant organizations and schemas';
    if (this.is_company_admin()) return 'Real-time team presence, department attendance rates, and employee logs';
    return 'Your personal clock-in timestamps, weekly logged hours, and timesheet records';
  });

  readonly report_scope_pill = computed(() => {
    if (this.is_super_admin()) return { label: 'Organization Scope', icon: 'building-2', tone: 'purple' as const };
    if (this.is_company_admin()) return { label: 'Team Scope', icon: 'users', tone: 'info' as const };
    return { label: 'Personal Scope', icon: 'user', tone: 'success' as const };
  });

  readonly safechild_metrics = signal({
    total_children: 148,
    checked_in_today: 112,
    picked_up_today: 108,
    attendance_rate: '94.8%'
  });

  readonly safechild_class_reports = signal([
    { class_name: 'Hekima Class (3-5 yrs)', total: 38, present: 32, released: 30, teacher: 'Tr. Alice Wambui', location: 'Ezra Building' },
    { class_name: 'Imani Class (6-8 yrs)', total: 42, present: 35, released: 34, teacher: 'Tr. Josephat Otieno', location: 'Facility Centre' },
    { class_name: 'Busara Class (9-11 yrs)', total: 40, present: 30, released: 28, teacher: 'Tr. Mary Njeri', location: 'Main Tent' },
    { class_name: 'Upendo Class (12-14 yrs)', total: 28, present: 15, released: 16, teacher: 'Tr. David Mwangi', location: 'Main Tent (Wing B)' }
  ]);

  // State
  departments = signal<Department[]>([]);
  dashboard_metrics = signal<DashboardMetrics | null>(null);
  employee_attendance = signal<ReportEmployeeAttendance[]>([]);
  department_attendance = signal<ReportDepartmentAttendance[]>([]);
  trend_attendance = signal<ReportTrendData[]>([]);
  active_departments = computed(() => this.department_attendance().filter(d => d.total_employees > 0));
  
  // UI State
  currentLayout = signal<'list' | 'chart'>('list');

  // Filters
  filter_date_from = signal<string>('');
  filter_date_to = signal<string>('');
  filter_department_id = signal<number | null>(null);
  trend_interval = signal<'daily' | 'weekly' | 'monthly'>('daily');

  // Loading states
  is_loading_metrics = signal<boolean>(false);
  is_loading_table = signal<boolean>(false);
  is_loading_chart = signal<boolean>(false);

  // Chart configurations
  public trend_chart_options: Partial<ChartOptions> = {};
  public department_chart_options: Partial<ChartOptions> = {};
  public person_chart_options: Partial<ChartOptions> = {};
  public bubble_chart_options: Partial<ChartOptions> = {};
  public top_dept_chart_options: Partial<ChartOptions> = {};

  constructor() {
    this.init_chart_options();
    
    // Create an effect to watch department attendance changes and update chart
    effect(() => {
      const depts = this.active_departments();
      const emps = this.employee_attendance();
      const trends = this.trend_attendance();
      const interval = this.trend_interval();
      this.update_chart_data(depts, emps, trends, interval);
    });
  }

  ngOnInit() {
    const routeData = this.route.snapshot.data;
    const routePath = this.route.snapshot.routeConfig?.path;
    if (routeData['type'] === 'safechild' || routePath === 'safechild-reports' || (this.auth.role() === 'teacher' && !this.auth.can('view:reports'))) {
      this.active_tab.set('safechild');
    } else {
      this.active_tab.set('hr');
    }

    this.set_default_dates();
    this.load_departments();
    this.load_dashboard_metrics();
    this.apply_filters(); // Loads table and charts
  }

  set_default_dates() {
    // Default to last 30 days
    const today = new Date();
    const thirtyDaysAgo = new Date();
    thirtyDaysAgo.setDate(today.getDate() - 30);
    
    if (this.filter_date_to().trim() === '') this.filter_date_to.set(today.toISOString().split('T')[0]);
    if (this.filter_date_from().trim() === '') this.filter_date_from.set(thirtyDaysAgo.toISOString().split('T')[0]);
  }

  load_departments() {
    this.department_service.getDepartments().subscribe({
      next: (data) => this.departments.set(data),
      error: (err) => console.error('Failed to load departments', err)
    });
  }

  load_dashboard_metrics() {
    this.is_loading_metrics.set(true);
    this.report_service.get_dashboard_metrics().subscribe({
      next: (data: DashboardMetrics) => {
        this.dashboard_metrics.set(data);
        this.is_loading_metrics.set(false);
      },
      error: (err: unknown) => {
        console.error('Failed to load dashboard metrics', err);
        this.is_loading_metrics.set(false);
      }
    });
  }

  apply_filters() {
    this.load_employee_attendance();
    this.load_department_attendance();
    this.load_trends();
  }

  clear_filters() {
    this.filter_department_id.set(null);
    this.set_default_dates();
    this.apply_filters();
  }

  load_employee_attendance() {
    this.is_loading_table.set(true);
    this.report_service.get_attendance_report({
      date_from: this.filter_date_from(),
      date_to: this.filter_date_to(),
      department_id: this.filter_department_id()
    }).subscribe({
      next: (response: PaginatedReportAttendance) => {
        this.employee_attendance.set(response.data || []); 
        this.is_loading_table.set(false);
      },
      error: (err: unknown) => {
        console.error('Failed to load attendance table', err);
        this.is_loading_table.set(false);
      }
    });
  }

  load_department_attendance() {
    this.is_loading_chart.set(true);
    this.report_service.get_department_attendance_report({
      date_from: this.filter_date_from(),
      date_to: this.filter_date_to(),
    }).subscribe({
      next: (data: ReportDepartmentAttendance[]) => {
        this.department_attendance.set(data || []);
        this.is_loading_chart.set(false);
      },
      error: (err: unknown) => {
        console.error('Failed to load department attendance', err);
        this.is_loading_chart.set(false);
      }
    });
  }

  load_trends() {
    this.report_service.get_attendance_trends({
      date_from: this.filter_date_from(),
      date_to: this.filter_date_to(),
      department_id: this.filter_department_id()
    }).subscribe({
      next: (response: {data: ReportTrendData[]}) => {
        this.trend_attendance.set(response.data || []);
      },
      error: (err: unknown) => {
        console.error('Failed to load trends', err);
      }
    });
  }

  init_chart_options() {
    const commonFont = chartTheme.fontFamily;

    // 1. Attendance Trends (Line)
    this.trend_chart_options = {
      series: [{
        name: "Total Hours",
        data: []
      }],
      chart: {
        type: "line",
        height: 300,
        fontFamily: commonFont,
        toolbar: { show: false },
        animations: { enabled: true, speed: 800 }
      },
      dataLabels: { enabled: false },
      stroke: { curve: 'smooth', width: 3, colors: [chartSeries[0]] },
      xaxis: {
        labels: { style: { colors: chartTheme.axisLabel } }
      },
      yaxis: {
        title: { text: "Hours", style: { color: chartTheme.axisLabel } },
        min: 0
      },
      grid: { borderColor: chartTheme.gridBorder, strokeDashArray: 4, yaxis: { lines: { show: true } } },
      tooltip: { theme: 'light', y: { formatter: (val: number) => val + " hrs" } }
    };

    // 2. Attendance by Department (Column)
    this.department_chart_options = {
      series: [{ name: "Attendance Rate (%)", data: [] }],
      chart: {
        type: "bar",
        height: 300,
        fontFamily: commonFont,
        toolbar: { show: false },
        animations: { enabled: true, speed: 800 }
      },
      plotOptions: {
        bar: { horizontal: false, columnWidth: "45%", borderRadius: 4 }
      },
      colors: [chartSeries[0]],
      dataLabels: { enabled: false },
      xaxis: { categories: [], labels: { style: { colors: chartTheme.axisLabel } } },
      yaxis: { title: { text: "Rate (%)", style: { color: chartTheme.axisLabel } }, min: 0, max: 100 },
      grid: { borderColor: chartTheme.gridBorder, strokeDashArray: 4 },
      tooltip: { theme: 'light', y: { formatter: (val: number) => val + "%" } }
    };

    // 3. Top 10 Departments by Hours (Horizontal Bar)
    this.top_dept_chart_options = {
      series: [{ name: "Total Hours", data: [] }],
      chart: {
        type: "bar",
        height: 300,
        fontFamily: commonFont,
        toolbar: { show: false },
        animations: { enabled: true, speed: 800 }
      },
      plotOptions: {
        bar: { horizontal: true, barHeight: "50%", borderRadius: 4 }
      },
      colors: [chartSeries[2]],
      dataLabels: { enabled: false },
      xaxis: { title: { text: "Hours", style: { color: chartTheme.axisLabel } }, labels: { style: { colors: chartTheme.axisLabel } } },
      yaxis: { categories: [], labels: { style: { colors: chartTheme.axisLabel } } },
      grid: { borderColor: chartTheme.gridBorder, strokeDashArray: 4, xaxis: { lines: { show: true } }, yaxis: { lines: { show: false } } },
      tooltip: { theme: 'light', y: { formatter: (val: number) => val + " hrs" } }
    };

    // 4. Attendance by Person (Bar)
    this.person_chart_options = {
      series: [{ name: "Total Hours", data: [] }],
      chart: {
        type: "bar",
        height: 300,
        fontFamily: commonFont,
        toolbar: { show: false },
        animations: { enabled: true, speed: 800 }
      },
      plotOptions: {
        bar: { horizontal: true, barHeight: "50%", borderRadius: 4 }
      },
      colors: [chartSeries[4]],
      dataLabels: { enabled: false },
      xaxis: { title: { text: "Hours", style: { color: chartTheme.axisLabel } }, labels: { style: { colors: chartTheme.axisLabel } } },
      yaxis: { categories: [], labels: { style: { colors: chartTheme.axisLabel } } },
      grid: { borderColor: chartTheme.gridBorder, strokeDashArray: 4, xaxis: { lines: { show: true } }, yaxis: { lines: { show: false } } },
      tooltip: { theme: 'light', y: { formatter: (val: number) => val + " hrs" } }
    };

    // 5. Check-In & Check-Out Times (Bubble)
    this.bubble_chart_options = {
      series: [
        { name: "Check In", data: [] },
        { name: "Check Out", data: [] }
      ],
      chart: {
        type: "bubble",
        height: 300,
        fontFamily: commonFont,
        toolbar: { show: false },
        animations: { enabled: true, speed: 800 }
      },
      colors: [chartSeries[1], chartSeries[3]],
      dataLabels: { enabled: false },
      xaxis: {
        title: { text: "Time of Day (Hours)", style: { color: chartTheme.axisLabel } },
        min: 6,
        max: 20,
        tickAmount: 14,
        labels: { 
          style: { colors: chartTheme.axisLabel },
          formatter: (val: string) => {
            const num = parseFloat(val);
            if (isNaN(num)) return val;
            const h = Math.floor(num);
            const m = Math.round((num - h) * 60);
            return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}`;
          }
        }
      },
      yaxis: {
        title: { text: "Employee", style: { color: chartTheme.axisLabel } },
        labels: { style: { colors: chartTheme.axisLabel } },
        min: 0
      },
      grid: { borderColor: chartTheme.gridBorder, strokeDashArray: 4 },
      tooltip: { theme: 'light' }
    };
  }

  format_snake_case(str: string): string {
    if (!str) return '';
    return str.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
  }

  parseTime(timeStr: string | null | undefined): number | null {
    if (!timeStr) return null;
    const parts = timeStr.split(':');
    if (parts.length >= 2) {
      return parseInt(parts[0], 10) + parseInt(parts[1], 10) / 60;
    }
    return null;
  }

  update_chart_data(activeDepts: ReportDepartmentAttendance[], emps: ReportEmployeeAttendance[], trends: ReportTrendData[], interval: 'daily' | 'weekly' | 'monthly' = 'daily') {
    // 1. Attendance Trends (Line)
    if (trends.length > 0) {
      let aggregated_trends = trends;

      if (interval === 'weekly') {
        const grouped = new Map<string, number>();
        trends.forEach(t => {
          const d = new Date(t.date);
          const firstDayOfYear = new Date(d.getFullYear(), 0, 1);
          const pastDaysOfYear = (d.getTime() - firstDayOfYear.getTime()) / 86400000;
          const weekNum = Math.ceil((pastDaysOfYear + firstDayOfYear.getDay() + 1) / 7);
          const key = `Wk ${weekNum}`;
          grouped.set(key, (grouped.get(key) || 0) + t.total_hours);
        });
        aggregated_trends = Array.from(grouped.entries()).map(([k, v]) => ({ date: k, total_hours: v }));
      } else if (interval === 'monthly') {
        const grouped = new Map<string, number>();
        const monthNames = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
        trends.forEach(t => {
          const d = new Date(t.date);
          const key = `${monthNames[d.getMonth()]} '${d.getFullYear().toString().slice(2)}`;
          grouped.set(key, (grouped.get(key) || 0) + t.total_hours);
        });
        aggregated_trends = Array.from(grouped.entries()).map(([k, v]) => ({ date: k, total_hours: v }));
      }

      this.trend_chart_options = {
        ...this.trend_chart_options,
        series: [{
          name: "Total Hours",
          data: aggregated_trends.map(t => {
            let label = t.date;
            if (interval === 'daily') {
              const d = new Date(t.date);
              label = `${d.getMonth() + 1}/${d.getDate()}`;
            }
            return {
              x: label,
              y: parseFloat(Number(t.total_hours).toFixed(1))
            };
          })
        }]
      };
    }

    // 2. Department Chart & Top 10 Depts
    if (activeDepts.length > 0) {
      this.department_chart_options = {
        ...this.department_chart_options,
        series: [{
          name: "Attendance Rate (%)",
          data: activeDepts.map(d => Number(d.avg_attendance_rate))
        }],
        xaxis: {
          ...(this.department_chart_options as ChartOptions).xaxis,
          categories: activeDepts.map(d => this.format_snake_case(d.department_name))
        }
      };

      const sortedDepts = [...activeDepts].sort((a, b) => b.total_hours_worked - a.total_hours_worked).slice(0, 10);
      this.top_dept_chart_options = {
        ...this.top_dept_chart_options,
        series: [{
          name: "Total Hours",
          data: sortedDepts.map(d => ({
            x: this.format_snake_case(d.department_name),
            y: parseFloat(Number(d.total_hours_worked).toFixed(1))
          }))
        }]
      };
    }

    // 3. Person Chart (Top 10 by hours to avoid crowding)
    if (emps.length > 0) {
      const sortedEmps = [...emps].sort((a, b) => b.total_hours_worked - a.total_hours_worked).slice(0, 10);
      this.person_chart_options = {
        ...this.person_chart_options,
        series: [{
          name: "Total Hours",
          data: sortedEmps.map(e => ({
            x: e.employee_name,
            y: e.total_hours_worked
          }))
        }],
        yaxis: {
          ...(this.person_chart_options as ChartOptions).yaxis,
          labels: {
            style: { colors: chartTheme.axisLabel },
            formatter: (val: number) => val ? String(val).split(' ')[0] : String(val)
          }
        }
      };

      // 4. Bubble Chart
      const check_in_data: [number, number, number][] = [];
      const check_out_data: [number, number, number][] = [];

      emps.forEach((e, index) => {
        // Y-axis uses index + 1 for spacing
        const yIndex = index + 1;
        const inTime = this.parseTime(e.avg_clock_in);
        const outTime = this.parseTime(e.avg_clock_out);

        if (inTime !== null) {
          check_in_data.push([inTime, yIndex, 20]); // [x, y, size]
        }
        if (outTime !== null) {
          check_out_data.push([outTime, yIndex, 20]);
        }
      });

      this.bubble_chart_options = {
        ...this.bubble_chart_options,
        series: [
          { name: "Check In", data: check_in_data },
          { name: "Check Out", data: check_out_data }
        ],
        yaxis: {
          ...(this.bubble_chart_options as ChartOptions).yaxis,
          max: emps.length + 1,
          labels: {
            style: { colors: chartTheme.axisLabel },
            formatter: (val: number) => {
              const i = Math.round(val) - 1;
              if (i >= 0 && i < emps.length) return emps[i].employee_name.split(' ')[0];
              return '';
            }
          }
        },
        tooltip: {
          theme: 'light',
          x: {
            formatter: (val: number) => {
              const h = Math.floor(val);
              const m = Math.round((val - h) * 60);
              return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}`;
            }
          },
          y: {
            formatter: (val: number) => {
              const i = Math.round(val) - 1;
              if (i >= 0 && i < emps.length) return emps[i].employee_name;
              return val.toString();
            },
            title: {
              formatter: () => 'Employee:'
            }
          }
        }
      };
    }
  }

  get_initials(name: string): string {
    if (!name) return '?';
    const parts = name.trim().split(' ').filter(p => p.length > 0);
    if (parts.length >= 2) {
      return (parts[0][0] + parts[1][0]).toUpperCase();
    }
    return name.substring(0, 2).toUpperCase();
  }

  get_possible_hours(record: ReportEmployeeAttendance): number {
    return (record.total_days_present + record.total_days_absent) * 10;
  }

  get_attendance_rate(record: ReportEmployeeAttendance): number {
    const total_days = record.total_days_present + record.total_days_absent;
    if (total_days === 0) return 0;
    return (record.total_days_present / total_days) * 100;
  }
}
