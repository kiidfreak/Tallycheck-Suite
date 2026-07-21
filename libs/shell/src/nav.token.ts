import { InjectionToken } from '@angular/core';
import { Signal } from '@angular/core';
import { RoleKey } from '@omni/auth';
import { NavGroup } from './nav.types';

/**
 * How the shell learns what to put in the sidebar.
 *
 * The shell is shared by every product in the workspace (tcheck, vcheck, …), so
 * it must not know any product's routes. Each app provides its own builder.
 */
export const NAV_PROVIDER = new InjectionToken<(role: RoleKey) => NavGroup[]>('NAV_PROVIDER');

/**
 * Counts rendered as badges on nav items, keyed by nav item id.
 *
 * Badge data is product-specific and needs API calls, which the shell has no
 * business making. Apps expose a signal; the shell only renders it.
 */
export const SHELL_BADGES = new InjectionToken<Signal<Record<string, number>>>('SHELL_BADGES');
