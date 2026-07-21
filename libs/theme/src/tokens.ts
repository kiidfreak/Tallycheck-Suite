/**
 * Design tokens as readable TypeScript constants.
 *
 * These mirror `styles/tokens.scss`. Prefer the CSS custom properties in
 * stylesheets — `color: var(--text-primary)` — and reach for these only where
 * a real value is required: ApexCharts options, canvas, generated SVG.
 *
 * `tokens.spec.ts` asserts every value here matches the SCSS, so the two cannot
 * drift silently.
 */

/** Raw palette. Prefer the semantic groups below. */
export const palette = {
  brand: {
    50: '#EFF5FF',
    100: '#DBEAFE',
    200: '#BFDBFE',
    500: '#3B82F6',
    600: '#2563EB',
    700: '#1D4ED8',
    800: '#1E40AF',
    900: '#1E3A8A',
    ink: '#0A2540',
  },
  accent: {
    50: '#FDF3F4',
    100: '#FCE8EA',
    500: '#D80000',
    600: '#C8102E',
    700: '#B30100',
  },
  neutral: {
    0: '#FFFFFF',
    25: '#FBFCFD',
    50: '#F8F9FC',
    100: '#F1F3F8',
    200: '#E5E8EF',
    300: '#D2D7E0',
    400: '#9AA2B1',
    500: '#6B7383',
    600: '#4A5160',
    700: '#2F3441',
    800: '#1A1E28',
    900: '#0E1119',
  },
} as const;

export const text = {
  primary: palette.neutral[900],
  secondary: palette.neutral[700],
  tertiary: palette.neutral[500],
  disabled: palette.neutral[400],
  onBrand: '#FFFFFF',
  onAccent: '#FFFFFF',
  brand: palette.brand[800],
} as const;

export const surface = {
  body: palette.neutral[50],
  base: palette.neutral[0],
  raised: '#FFFFFF',
  sunken: palette.neutral[100],
  hover: palette.neutral[100],
  selected: palette.brand[100],
  inverted: palette.brand.ink,
  sidebar: palette.brand[700],
} as const;

export const border = {
  light: palette.neutral[200],
  strong: palette.neutral[300],
  focus: palette.brand[700],
} as const;

export const status = {
  success: '#1F8A5B',
  successTint: '#E0F2EA',
  successStrong: '#166944',
  warning: '#C77700',
  warningTint: '#FCEFD9',
  warningStrong: '#9A5D00',
  danger: palette.accent[600],
  dangerTint: palette.accent[100],
  dangerStrong: palette.accent[700],
  info: palette.brand[700],
  infoTint: palette.brand[100],
  infoStrong: palette.brand[800],
} as const;

/** Attendance states. Categorical — read as distinct, not as a scale. */
export const attendanceStatus = {
  checkedIn: '#1F8A5B',
  remote: '#6B5BD3',
  office: '#1C467A',
  field: '#C77700',
  sick: '#C8102E',
  leave: '#9AA2B1',
  late: '#E58900',
  absent: '#B30100',
} as const;

export const font = {
  display: "'Plus Jakarta Sans', 'Inter', system-ui, -apple-system, sans-serif",
  body: "'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif",
  mono: "'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, monospace",
} as const;

/** Breakpoints in px. Mirrors the Sass `$bp-*` variables. */
export const breakpoint = {
  phone: 640,
  tablet: 1024,
  desktop: 1280,
} as const;

/**
 * Ordered series colours for charts.
 *
 * Chosen to stay distinguishable in order and to keep the brand cobalt first,
 * so a single-series chart reads as brand-coloured without extra config.
 */
export const chartSeries = [
  palette.brand[600],
  status.success,
  palette.accent[600],
  status.warning,
  attendanceStatus.remote,
  palette.brand[900],
] as const;

/** Shared ApexCharts styling so every chart in the workspace matches. */
export const chartTheme = {
  fontFamily: font.body,
  axisLabel: text.tertiary,
  gridBorder: border.light,
  tooltipTheme: 'light' as const,
};
