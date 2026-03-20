/**
 * VideoErrorHandler Tests
 * 
 * Unit tests for VideoErrorHandler service
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import {
  VideoErrorHandler,
  VideoError,
  VideoErrorType,
  ErrorContext,
  getQuickErrorMessage,
  isRetryableError,
} from '../VideoErrorHandler';

describe('VideoErrorHandler', () => {
  let handler: VideoErrorHandler;

  beforeEach(() => {
    // Create handler instance with console logging disabled for tests
    handler = new VideoErrorHandler(false, false);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Constructor', () => {
    it('should initialize with default values', () => {
      const defaultHandler = new VideoErrorHandler();
      expect(defaultHandler).toBeDefined();
    });

    it('should accept custom configuration', () => {
      const customHandler = new VideoErrorHandler(true, true);
      expect(customHandler).toBeDefined();
    });
  });

  describe('Error Classification', () => {
    it('should classify timeout errors', () => {
      const error = new Error('Request timeout');
      error.name = 'AbortError';

      const videoError = handler.handleError(error);

      expect(videoError.type).toBe('timeout');
      expect(videoError.retryable).toBe(true);
    });

    it('should classify network errors', () => {
      const error = new Error('Failed to fetch');
      error.name = 'TypeError';

      const videoError = handler.handleError(error);

      expect(videoError.type).toBe('network');
      expect(videoError.retryable).toBe(true);
    });

    it('should classify server errors (500)', () => {
      const error = new Error('Backend error: 500 Internal Server Error');

      const videoError = handler.handleError(error);

      expect(videoError.type).toBe('server');
      expect(videoError.statusCode).toBe(500);
      expect(videoError.retryable).toBe(true);
    });

    it('should classify server errors (502)', () => {
      const error = new Error('Backend error: 502 Bad Gateway');

      const videoError = handler.handleError(error);

      expect(videoError.type).toBe('server');
      expect(videoError.statusCode).toBe(502);
      expect(videoError.retryable).toBe(true);
    });

    it('should classify server errors (503)', () => {
      const error = new Error('Backend error: 503 Service Unavailable');

      const videoError = handler.handleError(error);

      expect(videoError.type).toBe('server');
      expect(videoError.statusCode).toBe(503);
      expect(videoError.retryable).toBe(false); // 503 is not retryable (maintenance)
    });

    it('should classify CORS errors', () => {
      const error = new Error('CORS policy blocked');

      const videoError = handler.handleError(error);

      expect(videoError.type).toBe('cors');
      expect(videoError.retryable).toBe(false);
    });

    it('should classify rate limit errors', () => {
      const error = new Error('Backend error: 429 Too Many Requests');

      const videoError = handler.handleError(error);

      expect(videoError.type).toBe('rate_limit');
      expect(videoError.retryable).toBe(false);
    });

    it('should classify validation errors (400)', () => {
      const error = new Error('Backend error: 400 Bad Request');

      const videoError = handler.handleError(error);

      expect(videoError.type).toBe('validation');
      expect(videoError.statusCode).toBe(400);
      expect(videoError.retryable).toBe(false);
    });

    it('should classify validation errors (401)', () => {
      const error = new Error('Backend error: 401 Unauthorized');

      const videoError = handler.handleError(error);

      expect(videoError.type).toBe('validation');
      expect(videoError.statusCode).toBe(401);
      expect(videoError.retryable).toBe(false);
    });

    it('should classify unknown errors', () => {
      const error = new Error('Something went wrong');

      const videoError = handler.handleError(error);

      expect(videoError.type).toBe('unknown');
      expect(videoError.retryable).toBe(true);
    });

    it('should handle non-Error objects', () => {
      const error = 'String error message';

      const videoError = handler.handleError(error);

      expect(videoError.type).toBe('unknown');
      expect(videoError.message).toBe('String error message');
    });
  });

  describe('User-Friendly Messages', () => {
    it('should generate Turkish message for timeout', () => {
      const error = new Error('Timeout');
      error.name = 'AbortError';

      const videoError = handler.handleError(error);

      expect(videoError.userMessage).toContain('zaman aşımı');
      expect(videoError.userMessage).toContain('⏰');
    });

    it('should generate Turkish message for network error', () => {
      const error = new Error('Network error');
      error.name = 'TypeError';

      const videoError = handler.handleError(error);

      expect(videoError.userMessage).toContain('İnternet');
      expect(videoError.userMessage).toContain('🌐');
    });

    it('should generate Turkish message for server error', () => {
      const error = new Error('Backend error: 500');

      const videoError = handler.handleError(error);

      expect(videoError.userMessage).toContain('Sunucu');
      expect(videoError.userMessage).toContain('🔧');
    });

    it('should generate Turkish message for CORS error', () => {
      const error = new Error('CORS error');

      const videoError = handler.handleError(error);

      expect(videoError.userMessage).toContain('güvenlik');
      expect(videoError.userMessage).toContain('🔒');
    });

    it('should generate Turkish message for rate limit', () => {
      const error = new Error('Rate limit exceeded');

      const videoError = handler.handleError(error);

      expect(videoError.userMessage).toContain('fazla istek');
      expect(videoError.userMessage).toContain('⚡');
    });
  });

  describe('Retry Decision Logic', () => {
    it('should allow retry for timeout errors', () => {
      const error = new Error('Timeout');
      error.name = 'AbortError';

      const videoError = handler.handleError(error);

      expect(handler.shouldRetry(videoError)).toBe(true);
    });

    it('should allow retry for network errors', () => {
      const error = new Error('Network error');
      error.name = 'TypeError';

      const videoError = handler.handleError(error);

      expect(handler.shouldRetry(videoError)).toBe(true);
    });

    it('should allow retry for server errors (except 503)', () => {
      const error500 = new Error('Backend error: 500');
      const videoError500 = handler.handleError(error500);
      expect(handler.shouldRetry(videoError500)).toBe(true);

      const error503 = new Error('Backend error: 503');
      const videoError503 = handler.handleError(error503);
      expect(handler.shouldRetry(videoError503)).toBe(false);
    });

    it('should not allow retry for CORS errors', () => {
      const error = new Error('CORS error');

      const videoError = handler.handleError(error);

      expect(handler.shouldRetry(videoError)).toBe(false);
    });

    it('should not allow retry for rate limit errors', () => {
      const error = new Error('Rate limit');

      const videoError = handler.handleError(error);

      expect(handler.shouldRetry(videoError)).toBe(false);
    });

    it('should not allow retry for validation errors', () => {
      const error = new Error('Backend error: 400');

      const videoError = handler.handleError(error);

      expect(handler.shouldRetry(videoError)).toBe(false);
    });
  });

  describe('Error Context', () => {
    it('should include context in error', () => {
      const error = new Error('Test error');
      const context: ErrorContext = {
        requestId: 'req_123',
        endpoint: '/api/v1/youtube/recommendations',
        retryCount: 1,
      };

      const videoError = handler.handleError(error, context);

      expect(videoError.requestId).toBe('req_123');
      expect(videoError.details?.context).toEqual(context);
    });

    it('should include timestamp', () => {
      const error = new Error('Test error');

      const videoError = handler.handleError(error);

      expect(videoError.timestamp).toBeInstanceOf(Date);
    });

    it('should include suggested action', () => {
      const error = new Error('Network error');
      error.name = 'TypeError';

      const videoError = handler.handleError(error);

      expect(videoError.suggestedAction).toBeDefined();
      expect(videoError.suggestedAction).toBe('retry');
    });
  });

  describe('Multiple Errors', () => {
    it('should handle multiple errors', () => {
      const errors = [
        new Error('Error 1'),
        new Error('Error 2'),
        new Error('Error 3'),
      ];

      const videoErrors = handler.handleMultipleErrors(errors);

      expect(videoErrors).toHaveLength(3);
      expect(videoErrors[0].message).toBe('Error 1');
      expect(videoErrors[1].message).toBe('Error 2');
      expect(videoErrors[2].message).toBe('Error 3');
    });

    it('should get error statistics', () => {
      const errors: VideoError[] = [
        handler.handleError(new Error('Timeout'), { requestId: '1' }),
        handler.handleError(new Error('Timeout'), { requestId: '2' }),
        handler.handleError(new Error('Network error'), { requestId: '3' }),
      ];

      errors[0].type = 'timeout';
      errors[1].type = 'timeout';
      errors[2].type = 'network';

      const stats = handler.getErrorStats(errors);

      expect(stats.timeout).toBe(2);
      expect(stats.network).toBe(1);
    });
  });

  describe('Helper Functions', () => {
    it('should get quick error message', () => {
      const error = new Error('Test error');
      error.name = 'AbortError';

      const message = getQuickErrorMessage(error);

      expect(message).toContain('zaman aşımı');
    });

    it('should check if error is retryable', () => {
      const retryableError = new Error('Network error');
      retryableError.name = 'TypeError';

      const nonRetryableError = new Error('CORS error');

      expect(isRetryableError(retryableError)).toBe(true);
      expect(isRetryableError(nonRetryableError)).toBe(false);
    });
  });

  describe('Logging', () => {
    it('should log to console when enabled', () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      const handlerWithLogging = new VideoErrorHandler(false, true);

      const error = new Error('Test error');
      handlerWithLogging.handleError(error);

      expect(consoleErrorSpy).toHaveBeenCalled();

      consoleErrorSpy.mockRestore();
    });

    it('should not log to console when disabled', () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      const handlerWithoutLogging = new VideoErrorHandler(false, false);

      const error = new Error('Test error');
      handlerWithoutLogging.handleError(error);

      expect(consoleErrorSpy).not.toHaveBeenCalled();

      consoleErrorSpy.mockRestore();
    });
  });

  describe('Status Code Extraction', () => {
    it('should extract status code from error message', () => {
      const error = new Error('Backend error: 404 Not Found');

      const videoError = handler.handleError(error);

      expect(videoError.statusCode).toBe(404);
    });

    it('should handle missing status code', () => {
      const error = new Error('Generic error');

      const videoError = handler.handleError(error);

      expect(videoError.statusCode).toBeUndefined();
    });
  });

  describe('Suggested Actions', () => {
    it('should suggest retry for retryable errors', () => {
      const error = new Error('Network error');
      error.name = 'TypeError';

      const videoError = handler.handleError(error);

      expect(videoError.suggestedAction).toBe('retry');
    });

    it('should suggest check_connection for network errors', () => {
      const error = new Error('Network error');
      error.name = 'TypeError';

      const videoError = handler.handleError(error);

      expect(videoError.suggestedAction).toBe('retry'); // Network errors are retryable
    });

    it('should suggest contact_admin for CORS errors', () => {
      const error = new Error('CORS error');

      const videoError = handler.handleError(error);

      expect(videoError.suggestedAction).toBe('contact_admin');
    });

    it('should suggest wait_and_retry for rate limit', () => {
      const error = new Error('Rate limit');

      const videoError = handler.handleError(error);

      expect(videoError.suggestedAction).toBe('wait_and_retry');
    });
  });

  describe('Edge Cases', () => {
    it('should handle null error', () => {
      const videoError = handler.handleError(null);

      expect(videoError.type).toBe('unknown');
      expect(videoError.message).toBe('Unknown error occurred');
    });

    it('should handle undefined error', () => {
      const videoError = handler.handleError(undefined);

      expect(videoError.type).toBe('unknown');
      expect(videoError.message).toBe('Unknown error occurred');
    });

    it('should handle object error', () => {
      const error = { message: 'Custom error object' };

      const videoError = handler.handleError(error);

      expect(videoError.type).toBe('unknown');
    });

    it('should handle error without name property', () => {
      const error = new Error('Test error');
      delete (error as any).name;

      const videoError = handler.handleError(error);

      expect(videoError.type).toBeDefined();
    });
  });
});
