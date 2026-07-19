export interface Organization {
  id: string;
  name: string;
  domain: string;
  schema_name: string;
  is_active: boolean;
  created_at?: string;
  org_type?: 'corporate' | 'education';
  admin_email?: string;
}

export interface CreateOrganizationPayload {
  name: string;
  domain: string;
  org_type: 'corporate' | 'education';
  admin_email: string;
}
