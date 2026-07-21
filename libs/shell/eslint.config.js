const nx = require('@nx/eslint-plugin');
const baseConfig = require('../../eslint.config.js');

module.exports = [
  ...baseConfig,
  ...nx.configs['flat/angular'],
  ...nx.configs['flat/angular-template'],
  {
    files: ['**/*.ts'],
    rules: {
      '@angular-eslint/directive-selector': [
        'error',
        { type: 'attribute', prefix: 'omni', style: 'camelCase' },
      ],
      '@angular-eslint/component-selector': [
        'error',
        { type: 'element', prefix: 'omni', style: 'kebab-case' },
      ],
    },
  },
  {
    files: ['**/*.html'],
    rules: {
      // Angular extracts inline templates into virtual .html files; this rule
      // crashes on them because there is no TS program behind the virtual file.
      '@typescript-eslint/ban-ts-comment': 'off',
    },
  },
];
