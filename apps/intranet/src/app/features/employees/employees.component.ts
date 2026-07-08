import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { API_URL, AuthService } from '@omni/auth';
import { EmployeeService } from './employee.service';
import { Employee } from '../../interfaces/employees.interface';
import { 
  ButtonComponent, 
  AvatarComponent,
  PillComponent,
  IconComponent,
  StatCardComponent,
  FormatLabelPipe,
  ToastService
} from '@omni/ui';
import { forkJoin } from 'rxjs';


@Component({
  selector: 'app-employees',
  standalone: true,
  imports: [
    CommonModule, 
    FormsModule, 
    ButtonComponent, 
    AvatarComponent,
    PillComponent,
    IconComponent,
    StatCardComponent,
    FormatLabelPipe
  ],
  templateUrl: './employees.component.html',
  styleUrls: ['./employees.component.scss']
})
export class EmployeesComponent implements OnInit {
  private readonly employeeService = inject(EmployeeService);
  private readonly http = inject(HttpClient);
  private readonly apiUrl = inject(API_URL);
  private readonly auth = inject(AuthService);
  private readonly toast_service = inject(ToastService);

  readonly employees = signal<Employee[]>([]);
  readonly loading = signal(false);
  readonly searchQuery = signal('');
  readonly filterDepartment = signal<number | null>(null);

  readonly selectedTab = signal<'all' | 'pending'>('all');
  
  readonly selections = signal<Record<string, { role_id: number, department_id: number | null, is_internal: boolean }>>({});

  readonly displayedEmployees = computed(() => {
    const list = this.employees();
    const tab = this.selectedTab();
    if (tab === 'pending') {
      return list.filter(e => !e.is_approved);
    }
    return list;
  });

  readonly roles = signal<{ id: number; name: string }[]>([]);
  readonly departments = signal<{ id: number; name: string }[]>([]);

  // Computed signals for stats
  readonly totalUsers = computed(() => this.employees().filter(e => e.is_approved).length);
  readonly activeUsers = computed(() => this.employees().filter(e => e.is_active).length);
  readonly managersCount = computed(() => this.employees().filter(e => e.is_manager).length);
  readonly pendingUsers = computed(() => this.employees().filter(e => !e.is_approved).length);

  // Drawer state
  readonly isDrawerOpen = signal(false);
  readonly editingEmployee = signal<Employee | null>(null);

  // Form state
  readonly formEmail = signal('');
  readonly formFirstName = signal('');
  readonly formLastName = signal('');
  readonly formRoleId = signal<number | null>(null);
  readonly formDepartmentId = signal<number | null>(null);

  ngOnInit() {
    this.loadMetadata();
    this.loadEmployees();
  }

  loadMetadata() {
    interface MetadataItem {
      id: number;
      name: string;
    }

    interface MetadataResponse {
      roles?: MetadataItem[];
      departments?: MetadataItem[];
      data?: {
        roles?: MetadataItem[];
        departments?: MetadataItem[];
      };
    }

    this.http.get<MetadataResponse>(`${this.apiUrl}/auth/metadata`).subscribe({
      next: (res) => {
        const data = res?.roles ? res : res?.data;
        let fetchedRoles = data?.roles || [];
        const currentUserRole = this.auth.role();
        if (currentUserRole !== 'super_admin') {
          fetchedRoles = fetchedRoles.filter(r => r.name !== 'Super Admin');
        }
        this.roles.set(fetchedRoles);
        this.departments.set(data?.departments || []);
      }
    });
  }

  loadEmployees() {
    this.loading.set(true);
    
    interface PendingUser {
      id: string;
      email: string;
      first_name: string;
      last_name: string;
      role_id?: number | null;
      role_name?: string | null;
      department_id?: number | null;
      department_name?: string | null;
      manager_name?: string | null;
      is_active?: boolean;
      is_manager?: boolean;
      hire_date?: string | null;
      created_at?: string | null;
    }

    forkJoin({
      approved: this.employeeService.getEmployees({
        search: this.searchQuery(),
        department_id: this.filterDepartment()
      }),
      pending: this.http.get<PendingUser[]>(`${this.apiUrl}/auth/users/pending`)
    }).subscribe({
      next: (res) => {
        const approvedList = res.approved?.data || [];
        const pendingList = res.pending || [];
        
        const defaultStaffRole = this.roles().find((r) => r.name.toLowerCase() === 'staff')?.id || this.roles()[0]?.id || 0;
        const initialSelections: Record<string, { role_id: number, department_id: number | null, is_internal: boolean }> = {};
        
        const mappedPending: Employee[] = pendingList.map((p: PendingUser) => {
          initialSelections[p.id] = {
            role_id: defaultStaffRole,
            department_id: this.departments()[0]?.id || null,
            is_internal: true
          };
          
          return {
            id: p.id,
            email: p.email,
          first_name: p.first_name,
          last_name: p.last_name,
          role_id: p.role_id || null,
          role_name: p.role_name || null,
          department_id: p.department_id || null,
          department_name: p.department_name || null,
          manager_name: p.manager_name || null,
          is_active: p.is_active !== undefined ? p.is_active : false,
          is_approved: false,
          is_manager: p.is_manager || false,
          hire_date: p.hire_date || null,
          created_at: p.created_at || null
          };
        });


        const searchLower = this.searchQuery().trim().toLowerCase();
        const deptFilter = this.filterDepartment();
        
        const filteredPending = mappedPending.filter(p => {
          if (deptFilter !== null) return false;
          if (!searchLower) return true;
          return (
            p.first_name.toLowerCase().includes(searchLower) ||
            p.last_name.toLowerCase().includes(searchLower) ||
            p.email.toLowerCase().includes(searchLower)
          );
        });

        this.selections.set(initialSelections);
        this.employees.set([...approvedList, ...filteredPending]);
        this.loading.set(false);
      },
      error: () => {
        this.loading.set(false);
      }
    });
  }

  onSearchChange() {
    this.loadEmployees();
  }

  onDepartmentFilterChange() {
    this.loadEmployees();
  }

  openDrawer(employee?: Employee) {
    if (employee) {
      this.editingEmployee.set(employee);
      this.formEmail.set(employee.email);
      this.formFirstName.set(employee.first_name);
      this.formLastName.set(employee.last_name);
      this.formRoleId.set(employee.role_id);
      this.formDepartmentId.set(employee.department_id);
    } else {
      this.editingEmployee.set(null);
      this.formEmail.set('');
      this.formFirstName.set('');
      this.formLastName.set('');
      this.formRoleId.set(null);
      this.formDepartmentId.set(null);
    }
    this.isDrawerOpen.set(true);
  }

  closeDrawer() {
    this.isDrawerOpen.set(false);
  }

  approvePendingUser(userId: string) {
    const userSelection = this.selections()[userId];
    if (!userSelection?.role_id) return;
    
    this.http.post(`${this.apiUrl}/auth/users/${userId}/approve`, {
      role_id: userSelection.role_id,
      department_id: userSelection.department_id,
      is_internal: userSelection.is_internal
    }).subscribe({
      next: () => {
        this.loadEmployees();
      }
    });
  }

  saveEmployee() {
    const roleIdVal = this.formRoleId();
    const deptIdVal = this.formDepartmentId();

    const payload = {
      email: this.formEmail(),
      first_name: this.formFirstName(),
      last_name: this.formLastName(),
      role_id: roleIdVal ? Number(roleIdVal) : undefined,
      department_id: deptIdVal ? Number(deptIdVal) : undefined,
    };

    const editing = this.editingEmployee();
    if (editing && !editing.is_approved) {
      this.http.post(`${this.apiUrl}/auth/users/${editing.id}/approve`, {
        role_id: roleIdVal ? Number(roleIdVal) : undefined,
        department_id: deptIdVal ? Number(deptIdVal) : undefined,
        is_internal: true
      }).subscribe({
        next: () => {
          this.closeDrawer();
          this.loadEmployees();
        }
      });
    } else if (editing) {
      this.employeeService.updateEmployee(editing.id, payload).subscribe(() => {
        this.closeDrawer();
        this.loadEmployees();
      });
    } else {
      this.employeeService.createEmployee(payload).subscribe(() => {
        this.closeDrawer();
        this.loadEmployees();
      });
    }
  }

  getInitials(emp: Employee): string {
    const f = emp.first_name ? emp.first_name[0] : '';
    const l = emp.last_name ? emp.last_name[0] : '';
    return (f + l).toUpperCase() || 'EE';
  }

  getRoleTone(role: string | null): 'info' | 'success' | 'warning' | 'danger' | 'purple' | '' {
    if (!role) return '';
    const normalized = role.toLowerCase().replace(/-/g, '_');
    switch (normalized) {
      case 'super_admin':
        return 'danger';
      case 'manager':
        return 'success';
      case 'hr':
        return 'warning';
      case 'call_centre_agent':
      case 'call_centre_admin':
        return 'purple';
      case 'staff':
      default:
        return '';
    }
  }
}
