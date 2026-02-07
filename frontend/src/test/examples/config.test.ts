/**
 * Config Test Examples
 * Test environment'da config kullanımı
 */

import { describe, it, expect, beforeAll } from 'vitest';
import config from '@/config';

describe('Config - Test Environment', () => {
  beforeAll(() => {
    // Set test environment
    process.env.NODE_ENV = 'test';
  });

  it('should use test configuration in test environment', () => {
    expect(config.isTest).toBe(true);
    expect(config.isDevelopment).toBe(false);
    expect(config.isProduction).toBe(false);
  });

  it('should have shorter timeout for tests', () => {
    expect(config.api.timeout).toBe(5000); // 5s instead of 30s
  });

  it('should disable analytics in tests', () => {
    expect(config.features.analytics).toBe(false);
  });

  it('should disable websocket in tests', () => {
    expect(config.features.websocket).toBe(false);
  });

  it('should enable debug mode in tests', () => {
    expect(config.features.debug).toBe(true);
  });

  it('should use test app name', () => {
    expect(config.app.name).toBe('KIRO2 Test');
  });

  it('should use localhost for API in tests', () => {
    expect(config.api.baseURL).toBe('http://localhost:8000');
    expect(config.api.wsURL).toBe('ws://localhost:8000');
  });
});

/**
 * Example: API Test with Test Config
 */
describe('API - Test with Test Config', () => {
  it('should use test timeout for API calls', async () => {
    const startTime = Date.now();

    try {
      // This should timeout after 5s (test config) instead of 30s (production)
      await fetch(`${config.api.baseURL}/api/slow-endpoint`, {
        signal: AbortSignal.timeout(config.api.timeout),
      });
    } catch (error) {
      const elapsed = Date.now() - startTime;
      // Should timeout around 5000ms (test config)
      expect(elapsed).toBeLessThan(6000);
      expect(elapsed).toBeGreaterThan(4000);
    }
  });

  it('should not send analytics in test environment', async () => {
    const analyticsCalls: any[] = [];

    // Mock analytics
    (window as any).gtag = (...args: any[]) => {
      analyticsCalls.push(args);
    };

    // Make API call
    if (config.features.analytics) {
      (window as any).gtag('event', 'api_call');
    }

    // Analytics should not be called
    expect(analyticsCalls).toHaveLength(0);
    expect(config.features.analytics).toBe(false);
  });
});

/**
 * Example: Mock API with Test Config
 */
describe('Mock API - Test Config Integration', () => {
  it('should mock API responses in test environment', async () => {
    // In test environment, we can safely mock without affecting production
    if (config.isTest) {
      global.fetch = async () => {
        return {
          ok: true,
          json: async () => ({ test: 'data' }),
        } as Response;
      };
    }

    const response = await fetch(`${config.api.baseURL}/api/test`);
    const data = await response.json();

    expect(data).toEqual({ test: 'data' });
  });
});
