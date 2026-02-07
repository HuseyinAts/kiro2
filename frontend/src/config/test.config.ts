/**
 * Test Environment Configuration
 * Overrides for test environment (Jest, Vitest, etc.)
 */

export const testConfig = {
  api: {
    baseURL: 'http://localhost:8000',
    wsURL: 'ws://localhost:8000',
    timeout: 5000, // Shorter timeout for tests
  },
  app: {
    name: 'KIRO2 Test',
    version: '1.0.0-test',
    env: 'test',
  },
  features: {
    analytics: false, // Disable analytics in tests
    debug: true,
    websocket: false, // Disable WebSocket in tests
  },
  isDevelopment: false,
  isProduction: false,
  isTest: true,
};

export default testConfig;
