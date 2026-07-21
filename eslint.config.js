const nx = require('@nx/eslint-plugin');

module.exports = [
  ...nx.configs['flat/base'],
  ...nx.configs['flat/typescript'],
  ...nx.configs['flat/javascript'],
  {
    ignores: ['**/dist', '**/backend/.venv', '**/.venv', '**/venv'],
  },
  {
    files: ['**/*.ts', '**/*.tsx', '**/*.js', '**/*.jsx'],
    rules: {
      '@nx/enforce-module-boundaries': [
        'error',
        {
          enforceBuildableLibDependency: true,
          allow: ['^.*/eslint(\\.base)?\\.config\\.[cm]?js$'],
          depConstraints: [
            // ── Layering ──────────────────────────────────────────────
            // Read top to bottom: each layer may only reach downward. This is
            // what stops a shared UI component from importing a feature, or
            // theme tokens from growing a dependency on auth.
            {
              sourceTag: 'type:app',
              onlyDependOnLibsWithTags: ['type:feature', 'type:ui', 'type:data-access', 'type:util'],
            },
            {
              sourceTag: 'type:feature',
              onlyDependOnLibsWithTags: ['type:feature', 'type:ui', 'type:data-access', 'type:util'],
            },
            {
              sourceTag: 'type:ui',
              onlyDependOnLibsWithTags: ['type:ui', 'type:util'],
            },
            {
              sourceTag: 'type:data-access',
              onlyDependOnLibsWithTags: ['type:data-access', 'type:util'],
            },
            {
              sourceTag: 'type:util',
              onlyDependOnLibsWithTags: ['type:util'],
            },
            // ── Product scope ─────────────────────────────────────────
            // shared/ must never reach into a product; tcheck and vcheck must
            // never reach into each other. Anything both products need has to
            // be promoted into scope:shared deliberately.
            {
              sourceTag: 'scope:shared',
              onlyDependOnLibsWithTags: ['scope:shared'],
            },
            {
              sourceTag: 'scope:tcheck',
              onlyDependOnLibsWithTags: ['scope:tcheck', 'scope:shared'],
            },
            {
              sourceTag: 'scope:vcheck',
              onlyDependOnLibsWithTags: ['scope:vcheck', 'scope:shared'],
            },
            {
              // The marketing site consumes the design system and nothing else —
              // it must never reach into a product's code.
              sourceTag: 'scope:marketing',
              onlyDependOnLibsWithTags: ['scope:shared'],
            },
          ],
        },
      ],
    },
  },
  {
    files: ['**/*.ts', '**/*.tsx', '**/*.js', '**/*.jsx'],
    // Override or add rules here
    rules: {},
  },
];
