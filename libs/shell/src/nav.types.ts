/** Shape of the sidebar. Products build these; the shell only renders them. */

export interface NavItem {
  /** Route id, resolved against the app's router as `/{id}`. */
  id: string;
  label: string;
  /** lucide icon name */
  icon: string;
  badge?: number;
  expandable?: boolean;
}

export interface NavGroup {
  label: string;
  items: NavItem[];
}
