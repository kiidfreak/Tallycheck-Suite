export interface Employee {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role_id: number | null;
  role_name: string | null;
  department_id: number | null;
  department_name: string | null;
  is_active: boolean;
  is_approved: boolean;
  is_manager: boolean;
  hire_date: string | null;
  created_at: string | null;
  manager_name: string | null;
}

export interface EmployeeListResponse {
  data: Employee[];
  meta: {
    page: number;
    per_page: number;
    total: number;
    pages: number;
  };
}

export interface EmployeeFilters {
  page?: number;
  per_page?: number;
  search?: string;
  department_id?: number | null;
  department_name?: string;
  is_active?: boolean;
  is_approved?: boolean;
  role?: string;
}

export interface CreateEmployeePayload {
  email: string;
  first_name: string;
  last_name: string;
  role_id?: number;
  department_id?: number;
  hire_date?: string;
  is_approved?: boolean;
  is_active?: boolean;
  is_internal?: boolean;
}

export type UpdateEmployeePayload = Partial<CreateEmployeePayload>;

