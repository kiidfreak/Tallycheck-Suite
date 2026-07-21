const nx = require('@nx/eslint-plugin');
const baseConfig = require('../../eslint.config.js');

module.exports = [
  {
    // Generated code is not hand-maintained — linting it produces findings
    // nobody can action without editing the generator.
    //
    // Flat-config ignore patterns resolve from the directory ESLint is invoked
    // from, which under Nx is the workspace root. A bare 'src/generated/**'
    // silently matches nothing.
    ignores: ['libs/api-client/src/generated/**'],
  },
  ...baseConfig,
  ...nx.configs['flat/angular'],
];
