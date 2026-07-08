export interface Role {
  id: number;
  name: string;
}

export interface Department {
  id: number;
  name: string;
}

export interface PendingUser {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  role: string;
  created_at: string;
}

export interface MetadataResponse {
  roles: Role[];
  departments: Department[];
}

export interface UserSelection {
  role_id: number;
  department_id: number | null;
  is_internal: boolean;
}

