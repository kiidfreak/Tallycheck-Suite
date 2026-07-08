export interface Department {
  id: number;
  name: string;
  manager_id: string | null;
  manager_name: string | null;
  employee_count: number;
  parent_department_id: number | null;
  parent_department_name: string | null;
}
