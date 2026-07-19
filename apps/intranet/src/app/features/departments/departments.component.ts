import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { API_URL, AuthService } from '@omni/auth';
import { ButtonComponent, IconComponent, PillComponent, ToastService } from '@omni/ui';
import { Department } from '../../interfaces/departments.interface';
import { Employee } from '../../interfaces/employees.interface';
import { EmployeeService } from '../employees/employee.service';

@Component({
  selector: 'app-departments',
  standalone: true,
  imports: [CommonModule, FormsModule, ButtonComponent, IconComponent, PillComponent],
  templateUrl: './departments.component.html',
  styleUrls: ['./departments.component.scss']
})
export class DepartmentsComponent implements OnInit {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = inject(API_URL);
  readonly auth = inject(AuthService); // Expose auth to template for RBAC
  private readonly toast_service = inject(ToastService);
  private readonly employeeService = inject(EmployeeService);

  readonly departments = signal<Department[]>([]);
  readonly loading = signal(false);
  
  // For the manager dropdown
  readonly employees = signal<Employee[]>([]);

  // Drawer state
  readonly isDeptDrawerOpen = signal(false);
  readonly editingDepartment = signal<Department | null>(null);
  readonly deptFormManagerId = signal<string | null>(null);
  readonly deptFormParentId = signal<number | null>(null);
  readonly deptFormName = signal('');
  readonly deptSaving = signal(false);

  format_name(name: string): string {
    if (!name) return '—';
    return name
      .replace(/_/g, ' ')
      .replace(/\b\w/g, l => l.toUpperCase())
      .replace(/\bOf\b/g, 'of')
      .replace(/\bAnd\b/g, '&');
  }

  get_org_name(nameStr: string): string {
    if (!nameStr) return 'Corporate';
    const name = nameStr.toLowerCase();
    if (name.includes('fem') || name.includes('church') || name.includes('ministry')) {
      return 'FEM Church Karen';
    }
    if (name.includes('school') || name.includes('science') || name.includes('law') || name.includes('nursing') || name.includes('business') || name.includes('language')) {
      return 'Daystar University';
    }
    if (name.includes('security') || name.includes('patrol')) {
      return 'SecureGuard Kenya';
    }
    return 'Corporate Workspace';
  }

  readonly filtered_departments = computed(() => {
    const list = this.departments();
    const role = this.auth.role();

    // Platform Admins (super_admin & it_admin) see all multi-tenant organization departments
    if (role === 'super_admin' || role === 'it_admin') {
      return list;
    }

    // Sunday School Teachers see only Church Ministry departments
    if (role === 'teacher' || role === 'guardian') {
      return list.filter(d => this.get_org_name(d.name) === 'FEM Church Karen');
    }

    // Company Staff, Lecturers, and Admins see only their own Organization tenant departments
    return list.filter(d => this.get_org_name(d.name) === 'Daystar University' || this.get_org_name(d.name) === 'Corporate Workspace');
  });

  ngOnInit() {
    this.loadDepartments();
    if (this.auth.can('edit:departments')) {
      this.loadEmployees();
    }
  }

  loadDepartments() {
    this.loading.set(true);
    this.http.get<Department[]>(`${this.apiUrl}/departments`).subscribe({
      next: (res: { data?: Department[] } | Department[]) => {
        const responseData = res as { data?: Department[] };
        const list: Department[] = responseData?.data || (res as Department[]) || [];
        this.departments.set(list);
        this.loading.set(false);
      },
      error: () => {
        this.loading.set(false);
      }
    });
  }

  loadEmployees() {
    this.employeeService.getEmployees({}).subscribe({
      next: (res) => {
        this.employees.set(res.data || []);
      }
    });
  }

  openDeptDrawer(dept?: Department) {
    if (!this.auth.can('edit:departments')) return;
    
    this.editingDepartment.set(dept || null);
    this.deptFormName.set(dept?.name || '');
    this.deptFormManagerId.set(dept?.manager_id || null);
    this.deptFormParentId.set(dept?.parent_department_id || null);
    this.isDeptDrawerOpen.set(true);
  }

  closeDeptDrawer() {
    this.isDeptDrawerOpen.set(false);
    this.editingDepartment.set(null);
    this.deptFormName.set('');
  }

  saveDepartment() {
    if (!this.auth.can('edit:departments')) return;

    const dept = this.editingDepartment();
    const name = this.deptFormName().trim();
    if (this.deptSaving()) return;

    // Create mode
    if (!dept) {
      if (!name) {
        this.toast_service.show('Department name is required', 'error');
        return;
      }
      this.deptSaving.set(true);
      const payload = {
        name,
        manager_id: this.deptFormManagerId() || null,
        parent_department_id: this.deptFormParentId() || null,
      };
      this.http.post(`${this.apiUrl}/departments`, payload).subscribe({
        next: () => {
          this.deptSaving.set(false);
          this.closeDeptDrawer();
          this.loadDepartments();
          this.toast_service.show('Department created successfully', 'success');
        },
        error: () => {
          this.deptSaving.set(false);
          this.toast_service.show('Failed to create department', 'error');
        }
      });
      return;
    }

    // Edit mode
    const newManagerId = this.deptFormManagerId() || null;
    if (dept.manager_id !== newManagerId) {
      const isConfirmed = window.confirm(
        "Confirm manager change for this department?"
      );
      if (!isConfirmed) return;
    }

    this.deptSaving.set(true);

    const payload: Record<string, unknown> = {
      manager_id: newManagerId,
      parent_department_id: this.deptFormParentId() || null,
    };
    if (name && name !== dept.name) {
      payload['name'] = name;
    }

    this.http.put(`${this.apiUrl}/departments/${dept.id}`, payload).subscribe({
      next: () => {
        this.deptSaving.set(false);
        this.closeDeptDrawer();
        this.loadDepartments();
        this.toast_service.show('Department updated successfully', 'success');
      },
      error: () => {
        this.deptSaving.set(false);
        this.toast_service.show('Failed to update department', 'error');
      }
    });
  }
}
