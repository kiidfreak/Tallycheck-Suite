import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { API_URL, AuthService } from '@omni/auth';
import { ButtonComponent, IconComponent, ToastService } from '@omni/ui';
import { Department } from '../../interfaces/departments.interface';
import { Employee } from '../../interfaces/employees.interface';
import { EmployeeService } from '../employees/employee.service';

@Component({
  selector: 'app-departments',
  standalone: true,
  imports: [CommonModule, FormsModule, ButtonComponent, IconComponent],
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
  readonly deptSaving = signal(false);

  ngOnInit() {
    this.loadDepartments();
    if (this.auth.role() === 'hr' || this.auth.role() === 'super_admin') {
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

  openDeptDrawer(dept: Department) {
    if (this.auth.role() !== 'hr' && this.auth.role() !== 'super_admin') return;
    
    this.editingDepartment.set(dept);
    this.deptFormManagerId.set(dept.manager_id);
    this.deptFormParentId.set(dept.parent_department_id);
    this.isDeptDrawerOpen.set(true);
  }

  closeDeptDrawer() {
    this.isDeptDrawerOpen.set(false);
    this.editingDepartment.set(null);
  }

  saveDepartment() {
    if (this.auth.role() !== 'hr' && this.auth.role() !== 'super_admin') return;

    const dept = this.editingDepartment();
    if (!dept || this.deptSaving()) return;
    
    const newManagerId = this.deptFormManagerId() || null;
    if (dept.manager_id !== newManagerId) {
      const isConfirmed = window.confirm(
        "Confirm manager change for this department?"
      );
      if (!isConfirmed) return;
    }

    this.deptSaving.set(true);

    const payload = {
      manager_id: newManagerId,
      parent_department_id: this.deptFormParentId() || null,
    };

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
