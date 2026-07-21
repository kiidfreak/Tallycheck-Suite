import { readFileSync } from 'fs';
import { join } from 'path';
import { palette, text, surface, border, status, attendanceStatus, breakpoint } from './tokens';

/**
 * tokens.ts duplicates values from tokens.scss because charting libraries need
 * real colours, not `var(--x)`. Duplication is only safe if it cannot drift, so
 * these tests parse the SCSS and compare.
 */

const SCSS = readFileSync(join(__dirname, 'styles', 'tokens.scss'), 'utf-8');
// Breakpoints are a Sass-only API and live in their own partial so component
// stylesheets can use the mixins without inlining the token block.
const BREAKPOINTS_SCSS = readFileSync(join(__dirname, 'styles', '_breakpoints.scss'), 'utf-8');

/** Resolve a custom property to a literal, following one level of var() indirection. */
function cssVar(name: string): string {
  const direct = new RegExp(`^\\s*--${name}\\s*:\\s*([^;]+);`, 'm').exec(SCSS);
  if (!direct) throw new Error(`--${name} is not defined in tokens.scss`);
  const value = direct[1].trim();
  const indirect = /^var\(\s*--([a-z0-9-]+)\s*\)$/.exec(value);
  return indirect ? cssVar(indirect[1]) : value;
}

const eq = (actual: string, token: string) =>
  expect(actual.toUpperCase()).toBe(cssVar(token).toUpperCase());

describe('theme tokens stay in sync with tokens.scss', () => {
  it('brand ramp', () => {
    eq(palette.brand[50], 'brand-50');
    eq(palette.brand[100], 'brand-100');
    eq(palette.brand[200], 'brand-200');
    eq(palette.brand[500], 'brand-500');
    eq(palette.brand[600], 'brand-600');
    eq(palette.brand[700], 'brand-700');
    eq(palette.brand[800], 'brand-800');
    eq(palette.brand[900], 'brand-900');
    eq(palette.brand.ink, 'brand-ink');
  });

  it('accent ramp', () => {
    eq(palette.accent[50], 'accent-50');
    eq(palette.accent[100], 'accent-100');
    eq(palette.accent[500], 'accent-500');
    eq(palette.accent[600], 'accent-600');
    eq(palette.accent[700], 'accent-700');
  });

  it('neutrals', () => {
    for (const step of [0, 25, 50, 100, 200, 300, 400, 500, 600, 700, 800, 900] as const) {
      eq(palette.neutral[step], `neutral-${step}`);
    }
  });

  it('text roles', () => {
    eq(text.primary, 'text-primary');
    eq(text.secondary, 'text-secondary');
    eq(text.tertiary, 'text-tertiary');
    eq(text.disabled, 'text-disabled');
    eq(text.brand, 'text-brand');
  });

  it('surfaces', () => {
    eq(surface.body, 'bg-body');
    eq(surface.base, 'surface-base');
    eq(surface.sunken, 'surface-sunken');
    eq(surface.selected, 'surface-selected');
    eq(surface.inverted, 'surface-inverted');
    eq(surface.sidebar, 'surface-sidebar');
  });

  it('borders', () => {
    eq(border.light, 'border-light');
    eq(border.strong, 'border-strong');
    eq(border.focus, 'border-focus');
  });

  it('status colours', () => {
    eq(status.success, 'success');
    eq(status.successTint, 'success-tint');
    eq(status.successStrong, 'success-strong');
    eq(status.warning, 'warning');
    eq(status.danger, 'danger');
    eq(status.info, 'info');
  });

  it('attendance statuses', () => {
    eq(attendanceStatus.checkedIn, 'status-checked-in');
    eq(attendanceStatus.remote, 'status-remote');
    eq(attendanceStatus.office, 'status-office');
    eq(attendanceStatus.late, 'status-late');
    eq(attendanceStatus.absent, 'status-absent');
  });

  it('breakpoints match the Sass variables', () => {
    for (const [name, px] of Object.entries(breakpoint)) {
      const found = new RegExp(`\\$bp-${name}\\s*:\\s*(\\d+)px`).exec(BREAKPOINTS_SCSS);
      expect(found).not.toBeNull();
      expect(Number(found![1])).toBe(px);
    }
  });

  it('_breakpoints.scss emits no CSS', () => {
    // Component stylesheets @use this file. If it ever grows a rule that emits
    // CSS, that CSS is duplicated into every component and the per-component
    // style budget starts failing builds — which is exactly how it broke once.
    const withoutComments = BREAKPOINTS_SCSS.replace(/\/\/.*$/gm, '');
    expect(withoutComments).not.toMatch(/@import|:root|^\s*[.#a-z][^\n{]*\{/im);
  });
});
