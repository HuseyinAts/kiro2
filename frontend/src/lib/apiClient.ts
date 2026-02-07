/**
 * Centralized API Client with Automatic URL Construction
 *
 * ✅ BUG FIX #4: URL Routing Fix
 * - Prevents hardcoded URL prefix errors
 * - Automatic /api prefix handling
 * - Consistent error handling
 * - Auth token injection
 *
 * ✅ BUG FIX #5: Retry Logic + Circuit Breaker
 * - Exponential backoff retry
 * - Circuit breaker pattern
 * - Detailed error context
 */

import config from '../config';

import { retryWithBackoff, apiCircuitBreaker, RetryOptions } from './retryUtils';

const API_BASE_URL = config.api.baseURL;

export class APIError extends Error {
  constructor(
    message: string,
    public status: number,
    public detail?: string,
    public context?: Record<string, any>,
  ) {
    super(message);
    this.name = 'APIError';
  }
}

export class APIClient {
  private baseURL: string;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL.replace(/\/$/, ''); // Remove trailing slash
  }

  /**
   * Build full URL from endpoint path
   * Automatically adds /api prefix if not present
   */
  private buildURL(endpoint: string): string {
    // Ensure endpoint starts with /
    const path = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;

    // Add /api prefix if not present
    const fullPath = path.startsWith('/api') ? path : `/api${path}`;

    return `${this.baseURL}${fullPath}`;
  }

  /**
   * Generic fetch with error handling + retry logic
   * ✅ BUG FIX #5: Now with circuit breaker and retry
   */
  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    retryOptions?: RetryOptions,
  ): Promise<T> {
    const url = this.buildURL(endpoint);

    // Add auth token if available
    const token = localStorage.getItem('access_token');
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    // Add any provided headers
    if (options.headers) {
      const providedHeaders = options.headers as Record<string, string>;
      Object.assign(headers, providedHeaders);
    }

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    // Wrap fetch with retry + circuit breaker
    return retryWithBackoff(
      async () => {
        return apiCircuitBreaker.execute(async () => {
          try {
            const response = await fetch(url, {
              ...options,
              headers,
            });

            if (!response.ok) {
              const error = await response.json().catch(() => ({}));
              throw new APIError(
                error.message || error.detail || `HTTP ${response.status}`,
                response.status,
                error.detail,
                {
                  url,
                  method: options.method || 'GET',
                  timestamp: new Date().toISOString(),
                },
              );
            }

            return response.json();
          } catch (error) {
            if (error instanceof APIError) {
              throw error;
            }
            throw new APIError(
              error instanceof Error ? error.message : 'Network error',
              0,
              undefined,
              {
                url,
                method: options.method || 'GET',
                timestamp: new Date().toISOString(),
                originalError: error,
              },
            );
          }
        });
      },
      {
        maxAttempts: retryOptions?.maxAttempts || 3,
        initialDelay: retryOptions?.initialDelay || 1000,
        maxDelay: retryOptions?.maxDelay || 10000,
        timeout: retryOptions?.timeout || 30000,
        onRetry: (attempt, error) => {
          console.warn(
            `[API Retry] Attempt ${attempt} failed for ${url}:`,
            error.message,
          );
          if (retryOptions?.onRetry) {
            retryOptions.onRetry(attempt, error);
          }
        },
      },
    );
  }

  async get<T>(endpoint: string, retryOptions?: RetryOptions): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET' }, retryOptions);
  }

  async post<T>(
    endpoint: string,
    data?: any,
    retryOptions?: RetryOptions,
  ): Promise<T> {
    return this.request<T>(
      endpoint,
      {
        method: 'POST',
        body: data ? JSON.stringify(data) : undefined,
      },
      retryOptions,
    );
  }

  async put<T>(
    endpoint: string,
    data?: any,
    retryOptions?: RetryOptions,
  ): Promise<T> {
    return this.request<T>(
      endpoint,
      {
        method: 'PUT',
        body: data ? JSON.stringify(data) : undefined,
      },
      retryOptions,
    );
  }

  async delete<T>(endpoint: string, retryOptions?: RetryOptions): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' }, retryOptions);
  }

  /**
   * Get circuit breaker status for monitoring
   */
  getCircuitBreakerStatus() {
    return {
      state: apiCircuitBreaker.getState(),
      timestamp: new Date().toISOString(),
    };
  }

  /**
   * Reset circuit breaker (for recovery/testing)
   */
  resetCircuitBreaker() {
    apiCircuitBreaker.reset();
  }
}

// Singleton instance
export const apiClient = new APIClient();
