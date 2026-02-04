/**
 * Retry Logic + Circuit Breaker Utilities
 *
 * BUG FIX #5: Error Handling Enhancement
 * - Exponential backoff retry
 * - Circuit breaker pattern
 * - Detailed error context
 *
 * Best Practices (2024):
 * - Exponential backoff with jitter
 * - Circuit breaker state machine
 * - Error classification
 * - Timeout management
 */

export interface RetryOptions {
  maxAttempts?: number;
  initialDelay?: number;  // milliseconds
  maxDelay?: number;      // milliseconds
  backoffMultiplier?: number;
  timeout?: number;       // milliseconds
  shouldRetry?: (error: Error) => boolean;
  onRetry?: (attempt: number, error: Error) => void;
}

export interface CircuitBreakerOptions {
  failureThreshold?: number;  // Number of failures before opening
  successThreshold?: number;  // Number of successes to close
  timeout?: number;           // Time in ms before trying again
}

/**
 * Retry with exponential backoff
 *
 * @example
 * const result = await retryWithBackoff(
 *   () => fetch('/api/data'),
 *   { maxAttempts: 3, initialDelay: 1000 }
 * );
 */
export async function retryWithBackoff<T>(
  fn: () => Promise<T>,
  options: RetryOptions = {}
): Promise<T> {
  const {
    maxAttempts = 3,
    initialDelay = 1000,
    maxDelay = 10000,
    backoffMultiplier = 2,
    timeout = 30000,
    shouldRetry = (error) => {
      // Retry on network errors, 5xx errors, timeouts
      return (
        error.name === 'TypeError' ||  // Network error
        error.message.includes('timeout') ||
        error.message.includes('500') ||
        error.message.includes('502') ||
        error.message.includes('503') ||
        error.message.includes('504')
      );
    },
    onRetry,
  } = options;

  let lastError: Error;
  let delay = initialDelay;

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      // Add timeout to the operation
      const timeoutPromise = new Promise<never>((_, reject) => {
        setTimeout(() => reject(new Error(`Operation timed out after ${timeout}ms`)), timeout);
      });

      return await Promise.race([fn(), timeoutPromise]);
    } catch (error) {
      lastError = error as Error;

      // Don't retry if we've exhausted attempts
      if (attempt === maxAttempts) {
        throw enhanceError(lastError, {
          attempts: attempt,
          operation: fn.name || 'anonymous',
          timestamp: new Date().toISOString(),
        });
      }

      // Don't retry if error is not retryable
      if (!shouldRetry(lastError)) {
        throw enhanceError(lastError, {
          reason: 'non-retryable',
          attempts: attempt,
        });
      }

      // Call retry callback
      if (onRetry) {
        onRetry(attempt, lastError);
      }

      // Add jitter to prevent thundering herd
      const jitter = Math.random() * 0.3 * delay;
      const nextDelay = Math.min(delay + jitter, maxDelay);

      // Wait before retrying
      await new Promise((resolve) => setTimeout(resolve, nextDelay));

      // Increase delay for next attempt
      delay *= backoffMultiplier;
    }
  }

  throw lastError!;
}

/**
 * Circuit Breaker Pattern
 *
 * States:
 * - CLOSED: Normal operation
 * - OPEN: Too many failures, reject immediately
 * - HALF_OPEN: Testing if service recovered
 *
 * @example
 * const breaker = new CircuitBreaker({ failureThreshold: 5 });
 * const result = await breaker.execute(() => fetch('/api/data'));
 */
export class CircuitBreaker {
  private state: 'CLOSED' | 'OPEN' | 'HALF_OPEN' = 'CLOSED';
  private failureCount = 0;
  private successCount = 0;
  private nextAttempt = Date.now();
  private options: Required<CircuitBreakerOptions>;

  constructor(options: CircuitBreakerOptions = {}) {
    this.options = {
      failureThreshold: options.failureThreshold || 5,
      successThreshold: options.successThreshold || 2,
      timeout: options.timeout || 60000,  // 1 minute
    };
  }

  async execute<T>(fn: () => Promise<T>): Promise<T> {
    if (this.state === 'OPEN') {
      if (Date.now() < this.nextAttempt) {
        throw new Error(
          `Circuit breaker is OPEN. Service unavailable. Retry after ${
            Math.ceil((this.nextAttempt - Date.now()) / 1000)
          }s`
        );
      }
      // Transition to HALF_OPEN to test if service recovered
      this.state = 'HALF_OPEN';
    }

    try {
      const result = await fn();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }

  private onSuccess(): void {
    this.failureCount = 0;

    if (this.state === 'HALF_OPEN') {
      this.successCount++;
      if (this.successCount >= this.options.successThreshold) {
        this.state = 'CLOSED';
        this.successCount = 0;
      }
    }
  }

  private onFailure(): void {
    this.failureCount++;
    this.successCount = 0;

    if (this.failureCount >= this.options.failureThreshold) {
      this.state = 'OPEN';
      this.nextAttempt = Date.now() + this.options.timeout;
    }
  }

  getState(): 'CLOSED' | 'OPEN' | 'HALF_OPEN' {
    return this.state;
  }

  reset(): void {
    this.state = 'CLOSED';
    this.failureCount = 0;
    this.successCount = 0;
    this.nextAttempt = Date.now();
  }
}

/**
 * Enhance error with additional context
 */
export function enhanceError(error: Error, context: Record<string, any>): Error {
  const enhanced = new Error(error.message);
  enhanced.name = error.name;
  enhanced.stack = error.stack;
  (enhanced as any).context = context;
  (enhanced as any).originalError = error;
  return enhanced;
}

/**
 * Check if error is retryable
 */
export function isRetryableError(error: Error): boolean {
  // Network errors
  if (error.name === 'TypeError' || error.name === 'NetworkError') {
    return true;
  }

  // Timeout errors
  if (error.message.includes('timeout') || error.message.includes('timed out')) {
    return true;
  }

  // 5xx server errors
  if (/5\d{2}/.test(error.message)) {
    return true;
  }

  // 429 Too Many Requests (with backoff)
  if (error.message.includes('429')) {
    return true;
  }

  return false;
}

/**
 * Combine retry + circuit breaker
 * Best of both worlds!
 *
 * @example
 * const result = await retryWithCircuitBreaker(
 *   () => fetch('/api/data'),
 *   { maxAttempts: 3 },
 *   { failureThreshold: 5 }
 * );
 */
export async function retryWithCircuitBreaker<T>(
  fn: () => Promise<T>,
  retryOptions: RetryOptions = {},
  circuitOptions: CircuitBreakerOptions = {}
): Promise<T> {
  const breaker = new CircuitBreaker(circuitOptions);

  return retryWithBackoff(
    () => breaker.execute(fn),
    {
      ...retryOptions,
      shouldRetry: (error) => {
        // Don't retry if circuit is open
        if (breaker.getState() === 'OPEN') {
          return false;
        }
        return retryOptions.shouldRetry
          ? retryOptions.shouldRetry(error)
          : isRetryableError(error);
      },
    }
  );
}

// Export singleton circuit breakers for common services
export const apiCircuitBreaker = new CircuitBreaker({
  failureThreshold: 5,
  successThreshold: 2,
  timeout: 60000,  // 1 minute
});

export const videoCircuitBreaker = new CircuitBreaker({
  failureThreshold: 3,
  successThreshold: 2,
  timeout: 30000,  // 30 seconds
});
