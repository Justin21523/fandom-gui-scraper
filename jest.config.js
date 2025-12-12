/**
 * Jest configuration for frontend testing.
 *
 * This configuration supports ES modules and provides a complete
 * testing environment for vanilla JavaScript frontend code.
 */

export default {
  // Use jsdom for DOM testing
  testEnvironment: 'jsdom',

  // Support ES modules
  transform: {},

  // Module resolution
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/frontend/js/$1',
    '^@tests/(.*)$': '<rootDir>/tests/frontend/$1',
  },

  // Test file patterns
  testMatch: [
    '**/tests/frontend/**/*.test.js',
    '**/tests/frontend/**/*.spec.js',
  ],

  // Coverage configuration
  collectCoverageFrom: [
    'frontend/js/**/*.js',
    '!frontend/js/**/*.test.js',
    '!frontend/js/**/*.spec.js',
    '!frontend/js/app.js', // Main entry point, tested via E2E
  ],

  coverageDirectory: 'coverage/frontend',

  coverageReporters: [
    'text',
    'text-summary',
    'lcov',
    'html',
    'json',
  ],

  // Coverage thresholds
  coverageThreshold: {
    global: {
      branches: 60,
      functions: 60,
      lines: 60,
      statements: 60,
    },
    // Stricter thresholds for critical modules
    './frontend/js/api/*.js': {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80,
    },
  },

  // Setup files
  setupFilesAfterEnv: ['<rootDir>/tests/frontend/setup.js'],

  // Test timeout (10 seconds)
  testTimeout: 10000,

  // Verbose output
  verbose: true,

  // Clear mocks between tests
  clearMocks: true,

  // Restore mocks between tests
  restoreMocks: true,

  // Reset modules between tests
  resetModules: true,

  // Collect coverage by default when running with --coverage
  collectCoverage: false,

  // Maximum number of concurrent workers
  maxWorkers: '50%',

  // Fail tests on console errors (optional, can be strict)
  // silent: false,
};
