/**
 * Frontend Logger Utility
 *
 * Provides structured logging with environment-aware behavior:
 * - Development: Full logging with timestamps and context
 * - Production: Only warnings and errors (console.log stripped by Vite)
 *
 * Usage:
 *   import { logger } from '@/utils/logger';
 *
 *   logger.debug('Debug message', { data: 'value' });
 *   logger.info('Info message');
 *   logger.warn('Warning message');
 *   logger.error('Error message', error);
 *
 * Features:
 * - Automatic timestamp
 * - Context object support
 * - Error stack trace extraction
 * - Environment-aware log levels
 */

type LogLevel = 'debug' | 'info' | 'warn' | 'error';

interface LogContext {
  [key: string]: unknown;
}

interface LogEntry {
  level: LogLevel;
  message: string;
  timestamp: string;
  context?: LogContext;
  stack?: string;
}

const LOG_LEVEL_PRIORITY: Record<LogLevel, number> = {
  debug: 0,
  info: 1,
  warn: 2,
  error: 3,
};

// Minimum log level based on environment
const getMinLevel = (): LogLevel => {
  if (typeof window === 'undefined') {
    return 'debug';
  }
  // In production, only show warnings and errors
  // Vite sets process.env.NODE_ENV or import.meta.env.MODE
  const isProd = (
    (typeof process !== 'undefined' && process.env?.NODE_ENV === 'production') ||
    window.location?.hostname !== 'localhost'
  );
  if (isProd) {
    return 'warn';
  }
  return 'debug';
};

const formatTimestamp = (): string => {
  return new Date().toISOString();
};

const shouldLog = (level: LogLevel): boolean => {
  const minLevel = getMinLevel();
  return LOG_LEVEL_PRIORITY[level] >= LOG_LEVEL_PRIORITY[minLevel];
};

const formatLogEntry = (entry: LogEntry): string => {
  const parts = [
    `[${entry.timestamp}]`,
    `[${entry.level.toUpperCase()}]`,
    entry.message,
  ];

  if (entry.context && Object.keys(entry.context).length > 0) {
    parts.push(JSON.stringify(entry.context));
  }

  return parts.join(' ');
};

/**
 * Logger class with environment-aware logging
 */
class Logger {
  private namespace: string;

  constructor(namespace = 'app') {
    this.namespace = namespace;
  }

  private log(level: LogLevel, message: string, context?: LogContext | Error): void {
    if (!shouldLog(level)) {
      return;
    }

    const entry: LogEntry = {
      level,
      message: `[${this.namespace}] ${message}`,
      timestamp: formatTimestamp(),
    };

    // Handle error objects
    if (context instanceof Error) {
      entry.context = {
        name: context.name,
        message: context.message,
      };
      entry.stack = context.stack;
    } else if (context) {
      entry.context = context;
    }

    // Output based on level
    const formattedMessage = formatLogEntry(entry);

    switch (level) {
      case 'debug':
        // eslint-disable-next-line no-console
        break;
      case 'info':
        // eslint-disable-next-line no-console
        console.info(formattedMessage);
        break;
      case 'warn':
        console.warn(formattedMessage);
        break;
      case 'error':
        console.error(formattedMessage);
        if (entry.stack) {
          console.error(entry.stack);
        }
        break;
    }
  }

  /**
   * Debug level logging (development only)
   */
  debug(message: string, context?: LogContext): void {
    this.log('debug', message, context);
  }

  /**
   * Info level logging (development only)
   */
  info(message: string, context?: LogContext): void {
    this.log('info', message, context);
  }

  /**
   * Warning level logging (always shown)
   */
  warn(message: string, context?: LogContext | Error): void {
    this.log('warn', message, context);
  }

  /**
   * Error level logging (always shown)
   */
  error(message: string, context?: LogContext | Error): void {
    this.log('error', message, context);
  }

  /**
   * Create a child logger with a specific namespace
   */
  child(namespace: string): Logger {
    return new Logger(`${this.namespace}:${namespace}`);
  }
}

// Default logger instance
export const logger = new Logger('kiro2');

// Factory function for creating namespaced loggers
export const createLogger = (namespace: string): Logger => {
  return new Logger(namespace);
};

// Export class for extension
export { Logger };

/**
 * Usage Examples:
 *
 * // Default logger
 * import { logger } from '@/utils/logger';
 * logger.info('User logged in', { userId: '123' });
 *
 * // Namespaced logger
 * import { createLogger } from '@/utils/logger';
 * const examLogger = createLogger('exam');
 * examLogger.debug('Exam started', { examId: 'abc' });
 *
 * // Error logging
 * try {
 *   await fetchData();
 * } catch (error) {
 *   logger.error('Failed to fetch data', error as Error);
 * }
 */
