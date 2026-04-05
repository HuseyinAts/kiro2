/**
 * Error Handler Demo Component
 * Merkezi error handling kullanımı örneği
 */

import * as React from 'react';
import {  useState  } from 'react';

import { getDashboardStats } from '@/api';
import { useErrorHandler, ErrorType, AppError } from '@/utils/errorHandler';

export const ErrorHandlerDemo: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<AppError | null>(null);
  const [data, setData] = useState<any>(null);

  const { handleError, getUserMessage, isRecoverable } = useErrorHandler();

  const fetchData = async () => {
    setLoading(true);
    setError(null);

    try {
      const result = await getDashboardStats();
      setData(result);
    } catch (err) {
      // Centralized error handling
      const appError = handleError(err, 'fetchData');
      setError(appError);

      // Show user-friendly message
      console.error(getUserMessage(appError));

      // Auto-retry for recoverable errors
      if (isRecoverable(appError)) {
        setTimeout(fetchData, 2000); // Retry after 2s
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="error-handler-demo">
      <h2>Error Handler Demo</h2>

      <button onClick={fetchData} disabled={loading}>
        {loading ? 'Loading...' : 'Fetch Dashboard Stats'}
      </button>

      {error && (
        <div className={`error-message ${error.type}`}>
          <h3>Error Type: {error.type}</h3>
          <p>{getUserMessage(error)}</p>
          {isRecoverable(error) && (
            <p className="retry-hint">This error is recoverable. Auto-retrying...</p>
          )}
          {error.details && (
            <pre>{JSON.stringify(error.details, null, 2)}</pre>
          )}
        </div>
      )}

      {data && (
        <div className="success-message">
          <h3>Data Loaded Successfully</h3>
          <pre>{JSON.stringify(data, null, 2)}</pre>
        </div>
      )}
    </div>
  );
};

/**
 * Example: Global Error Listener
 * Log all errors to analytics
 */
export const setupGlobalErrorTracking = () => {
  const { errorHandler } = require('@/utils/errorHandler');

  // Register global listener
  errorHandler.onError((error: AppError) => {
    // Send to analytics
    if (typeof window !== 'undefined' && (window as any).gtag) {
      (window as any).gtag('event', 'exception', {
        description: error.message,
        fatal: error.type === ErrorType.SERVER,
      });
    }

    // Send to Sentry (if configured)
    if (typeof window !== 'undefined' && (window as any).Sentry) {
      (window as any).Sentry.captureException(new Error(error.message), {
        extra: {
          type: error.type,
          status: error.status,
          details: error.details,
        },
      });
    }

    // Log to console in development
    if (process.env.NODE_ENV === 'development') {
      console.error('[Global Error Handler]', error);
    }
  });
};

export default ErrorHandlerDemo;
