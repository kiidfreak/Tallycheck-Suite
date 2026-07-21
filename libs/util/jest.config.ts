export default {
  displayName: 'util',
  preset: '../../jest.preset.js',
  coverageDirectory: '../../coverage/libs/util',
  transform: {
    '^.+\\.[tj]s$': ['ts-jest', { tsconfig: '<rootDir>/tsconfig.spec.json' }],
  },
  moduleFileExtensions: ['ts', 'js', 'html'],
};
