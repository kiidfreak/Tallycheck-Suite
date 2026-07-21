export default {
  displayName: 'theme',
  preset: '../../jest.preset.js',
  coverageDirectory: '../../coverage/libs/theme',
  transform: {
    '^.+\\.[tj]s$': ['ts-jest', { tsconfig: '<rootDir>/tsconfig.spec.json' }],
  },
  moduleFileExtensions: ['ts', 'js', 'html'],
};
