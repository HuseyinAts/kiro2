/**
 * Centralized Error Handling
 * Consistent error handling across the application
 */

import config from '../config';

export enum ErrorType {
  NETWORK = 'NETWORK_ERROR',
  AUTH = 'AUTH_ERROR',
  VALIDATION = 'VALIDATION_ERROR',
  SERVER = 'SERVER_ERROR',
  TIMEOUT = 'TIMEOUT_ERROR',
  UNKNOWN = 'UNKNOWN_ERROR',
}

export interface AppError {
  type: ErrorType;
  message: string;
  status?: number;
  details?: any;
  timestamp: Date;
  requestId?: string;
}

export class ErrorHandler {
  private static instance: ErrorHandler;
  private errorListeners: Array<(error: AppError) => void> = [];

  private constructor() {}

  static getInstance(): ErrorHandler {
    if (!ErrorHandler.instance) {
      ErrorHandler.instance = new ErrorHandler();
    }
    return ErrorHandler.instance;
  }

  /**
   * Register error listener (for logging, analytics, etc.)
   */
  onError(listener: (error: AppError) => void): () => void {
    this.errorListeners.push(listener);
    // Return unsubscribe function
    return () => {
      this.errorListeners = this.errorListeners.filter((l) => l !== listener);
    };
  }

  /**
   * Handle API errors
   */
  handleApiError(error: any, context?: string): AppError {
    const appError = this.parseError(error, context);
    this.notifyListeners(appError);

    if (config.features.debug) {
      console.error('[ErrorHandler]', appError);
    }

    return appError;
  }

  /**
   * Parse error to AppError format
   */
  private parseError(error: any, _context?: string): AppError {
    // Network errors
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      return {
        type: ErrorType.NETWORK,
        message: 'İnternet bağlantınızı kontrol edin',
        details: error.message,
        timestamp: new Date(),
      };
    }

    // Timeout errors
    if (error.name === 'AbortError' || error.code === 'ECONNABORTED') {
      return {
        type: ErrorType.TIMEOUT,
        message: 'İstek zaman aşımına uğradı. Lütfen tekrar deneyin.',
        timestamp: new Date(),
      };
    }

    // Axios errors
    if (error.response) {
      const status = error.response.status;
      const data = error.response.data;

      // Auth errors (401, 403)
      if (status === 401 || status === 403) {
        return {
          type: ErrorType.AUTH,
          message: status === 401 ? 'Oturum süreniz doldu. Lütfen tekrar giriş yapın.' : 'Bu işlem için yetkiniz yok.',
          status,
          details: data,
          timestamp: new Date(),
        };
      }

      // Validation errors (400)
      if (status === 400) {
        return {
          type: ErrorType.VALIDATION,
          message: data?.detail || data?.message || 'Geçersiz istek',
          status,
          details: data,
          timestamp: new Date(),
        };
      }

      // Server errors (500+)
      if (status >= 500) {
        return {
          type: ErrorType.SERVER,
          message: 'Sunucu hatası. Lütfen daha sonra tekrar deneyin.',
          status,
          details: data,
          timestamp: new Date(),
        };
      }

      // Other HTTP errors
      return {
        type: ErrorType.UNKNOWN,
        message: data?.detail || data?.message || `HTTP ${status} Hatası`,
        status,
        details: data,
        timestamp: new Date(),
      };
    }

    // Unknown errors
    return {
      type: ErrorType.UNKNOWN,
      message: error.message || 'Bilinmeyen bir hata oluştu',
      details: error,
      timestamp: new Date(),
    };
  }

  /**
   * Notify all error listeners
   */
  private notifyListeners(error: AppError): void {
    this.errorListeners.forEach((listener) => {
      try {
        listener(error);
      } catch (e) {
        console.error('[ErrorHandler] Error in listener:', e);
      }
    });
  }

  /**
   * Get user-friendly error message
   */
  getUserMessage(error: AppError): string {
    switch (error.type) {
      case ErrorType.NETWORK:
        return 'İnternet bağlantınızı kontrol edin ve tekrar deneyin.';
      case ErrorType.AUTH:
        return error.message;
      case ErrorType.VALIDATION:
        return error.message;
      case ErrorType.TIMEOUT:
        return 'İşlem çok uzun sürdü. Lütfen tekrar deneyin.';
      case ErrorType.SERVER:
        return 'Sunucu hatası. Bir süre sonra tekrar deneyin.';
      default:
        return 'Bir hata oluştu. Lütfen tekrar deneyin.';
    }
  }

  /**
   * Check if error is recoverable
   */
  isRecoverable(error: AppError): boolean {
    return error.type === ErrorType.NETWORK || error.type === ErrorType.TIMEOUT;
  }

  /**
   * Get retry delay for recoverable errors
   */
  getRetryDelay(error: AppError, attempt: number): number {
    if (!this.isRecoverable(error)) {
      return 0;
    }

    // Exponential backoff: 1s, 2s, 4s, 8s, max 10s
    return Math.min(1000 * Math.pow(2, attempt), 10000);
  }
}

// Singleton instance
export const errorHandler = ErrorHandler.getInstance();

/**
 * React hook for error handling
 */
export function useErrorHandler() {
  const handleError = (error: any, context?: string) => {
    return errorHandler.handleApiError(error, context);
  };

  const getUserMessage = (error: AppError) => {
    return errorHandler.getUserMessage(error);
  };

  const isRecoverable = (error: AppError) => {
    return errorHandler.isRecoverable(error);
  };

  return {
    handleError,
    getUserMessage,
    isRecoverable,
  };
}

/**
 * Error boundary helper
 */
export function logError(error: Error, errorInfo: React.ErrorInfo): void {
  const appError: AppError = {
    type: ErrorType.UNKNOWN,
    message: error.message,
    details: {
      stack: error.stack,
      componentStack: errorInfo.componentStack,
    },
    timestamp: new Date(),
  };

  errorHandler.handleApiError(appError);
}

export default errorHandler;
