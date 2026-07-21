// @omni/shell — app chrome: sidebar, header, layout shell.
//
// Product-agnostic. Apps supply their own navigation via NAV_PROVIDER and any
// badge counts via SHELL_BADGES; nothing here knows tcheck or vcheck routes.
export { ShellComponent } from './shell.component';
export { SidebarComponent } from './sidebar.component';
export { HeaderComponent } from './header.component';
export { NAV_PROVIDER, SHELL_BADGES } from './nav.token';
export type { NavItem, NavGroup } from './nav.types';
