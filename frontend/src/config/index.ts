/**
 * Application Configuration
 * Supports multiple environments: development, production, test
 */

// Check environment
const isTestEnv = typeof process !== 'undefined' && process.env.NODE_ENV === 'test';
const isDev = import.meta.env.DEV;
const isProd = import.meta.env.PROD;

export const config = {
  api: {
    baseURL: isTestEnv
      ? 'http://localhost:8000'
      : import.meta.env.VITE_API_URL ?? '',
    wsURL: isTestEnv
      ? 'ws://localhost:8000'
      : import.meta.env.VITE_WS_URL ?? '',
    timeout: isTestEnv
      ? 5000 // Shorter timeout for tests
      : parseInt(import.meta.env.VITE_API_TIMEOUT || '30000'),
  },
  app: {
    name: isTestEnv
      ? 'KIRO2 Test'
      : import.meta.env.VITE_APP_NAME || 'Teknofest Eğitim Eylemci',
    version: import.meta.env.VITE_APP_VERSION || '1.0.0',
    env: isTestEnv ? 'test' : import.meta.env.VITE_APP_ENV || 'development',
  },
  features: {
    analytics: isTestEnv ? false : import.meta.env.VITE_ENABLE_ANALYTICS === 'true',
    debug: isTestEnv ? true : import.meta.env.VITE_ENABLE_DEBUG === 'true',
    websocket: isTestEnv ? false : import.meta.env.VITE_ENABLE_WEBSOCKET === 'true',
  },
  isDevelopment: isDev,
  isProduction: isProd,
  isTest: isTestEnv,
};

export default config;