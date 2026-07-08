// @omni/theme
//
// This library's primary surface is SCSS — import it from an app's styles.scss:
//
//     @use '@omni/theme' as *;
//
// (styles live in ./styles/index.scss and ./styles/tokens.scss)
//
// This TS entry point exists so the lib resolves through tsconfig path aliases and
// can later export shared TypeScript token values (e.g. for charts) if needed.

export const THEME_TOKENS_SCSS = '@omni/theme/styles/index.scss';
