// @omni/theme
//
// The primary surface is SCSS — import it from an app's styles.scss:
//
//     @use '@omni/theme' as *;
//
// (styles live in ./styles/index.scss and ./styles/tokens.scss)
//
// This TS entry point exports the same tokens as readable constants, for the
// places CSS custom properties cannot reach: canvas, SVG and charting libraries
// (ApexCharts takes real colour values, not `var(--x)`).

export const THEME_TOKENS_SCSS = '@omni/theme/styles/index.scss';

export * from './tokens';
