/**
 * VideoErrorHandler - Video yükleme hata yönetimi
 * 
 * Bu servis, video yükleme sırasında oluşan hataları sınıflandırır,
 * kullanıcı dostu mesajlar üretir ve retry kararları verir.
 * 
 * @module VideoErrorHandler
 * @requires Requirements: 1.2, 1.3, 3.4, 3.10, 5.3, 10.4, 10.6
 */

/**
 * Hata tipleri
 */
export type VideoErrorType = 
  | 'timeout'      // İstek zaman aşımı
  | 'network'      // Ağ bağlantı hatası
  | 'server'       // Sunucu hatası (5xx)
  | 'cors'         // CORS politika hatası
  | 'rate_limit'   // Rate limit aşımı
  | 'validation'   // Veri doğrulama hatası
  | 'unknown';     // Bilinmeyen hata

/**
 * Video hatası interface
 */
export interface VideoError {
  /** Hata tipi */
  type: VideoErrorType;
  
  /** Orijinal hata mesajı (teknik) */
  message: string;
  
  /** Kullanıcı dostu hata mesajı (Türkçe) */
  userMessage: string;
  
  /** Hatanın tekrar denenebilir olup olmadığı */
  retryable: boolean;
  
  /** HTTP status code (varsa) */
  statusCode?: number;
  
  /** Hata detayları */
  details?: Record<string, any>;
  
  /** Hata zamanı */
  timestamp: Date;
  
  /** Request ID (varsa) */
  requestId?: string;
  
  /** Önerilen aksiyon */
  suggestedAction?: string;
}

/**
 * Hata context bilgisi
 */
export interface ErrorContext {
  /** Request ID */
  requestId?: string;
  
  /** API endpoint */
  endpoint?: string;
  
  /** Öğrenci profili özeti */
  profile?: Record<string, any>;
  
  /** Retry sayısı */
  retryCount?: number;
  
  /** Yükleme süresi */
  loadingTime?: number;
  
  /** Ek bilgiler */
  metadata?: Record<string, any>;
}

/**
 * Sentry/logging için hata log formatı
 */
export interface ErrorLog {
  /** Hata tipi */
  type: VideoErrorType;
  
  /** Hata mesajı */
  message: string;
  
  /** Severity level */
  level: 'error' | 'warning' | 'info';
  
  /** Context bilgisi */
  context: ErrorContext;
  
  /** Stack trace */
  stack?: string;
  
  /** Timestamp */
  timestamp: Date;
  
  /** Browser bilgisi */
  browser?: {
    userAgent: string;
    language: string;
    online: boolean;
  };
}

/**
 * VideoErrorHandler - Hata yönetimi ve sınıflandırma
 * 
 * Özellikler:
 * - Hata tipi sınıflandırma
 * - Kullanıcı dostu mesaj üretimi
 * - Retry kararı verme
 * - Structured error logging
 * - Sentry entegrasyonu (opsiyonel)
 */
export class VideoErrorHandler {
  private sentryEnabled: boolean;
  private consoleLoggingEnabled: boolean;

  /**
   * VideoErrorHandler constructor
   * 
   * @param sentryEnabled - Sentry logging aktif mi? (default: false)
   * @param consoleLoggingEnabled - Console logging aktif mi? (default: true)
   */
  constructor(
    sentryEnabled: boolean = false,
    consoleLoggingEnabled: boolean = true
  ) {
    this.sentryEnabled = sentryEnabled;
    this.consoleLoggingEnabled = consoleLoggingEnabled;
  }

  /**
   * Hatayı işle ve VideoError nesnesine dönüştür
   * 
   * @param error - Orijinal hata
   * @param context - Hata context bilgisi
   * @returns VideoError
   */
  handleError(error: unknown, context?: ErrorContext): VideoError {
    // Hata tipini belirle
    const errorType = this._classifyError(error);
    
    // Hata mesajını çıkar
    const message = this._extractErrorMessage(error);
    
    // Status code'u çıkar
    const statusCode = this._extractStatusCode(error);
    
    // Kullanıcı dostu mesaj üret
    const userMessage = this._generateUserMessage(errorType, statusCode);
    
    // Retry kararı ver
    const retryable = this._shouldRetry(errorType, statusCode);
    
    // Önerilen aksiyon belirle
    const suggestedAction = this._getSuggestedAction(errorType, retryable);
    
    // VideoError nesnesi oluştur
    const videoError: VideoError = {
      type: errorType,
      message,
      userMessage,
      retryable,
      statusCode,
      timestamp: new Date(),
      requestId: context?.requestId,
      suggestedAction,
      details: {
        originalError: error instanceof Error ? error.name : typeof error,
        context,
      },
    };

    // Log error
    this.logError(videoError, context);

    return videoError;
  }

  /**
   * Kullanıcı dostu hata mesajı al
   * 
   * @param error - VideoError nesnesi
   * @returns Kullanıcı dostu mesaj (Türkçe)
   */
  getUserMessage(error: VideoError): string {
    return error.userMessage;
  }

  /**
   * Hatanın tekrar denenebilir olup olmadığını kontrol et
   * 
   * @param error - VideoError nesnesi
   * @returns Retry yapılabilir mi?
   */
  shouldRetry(error: VideoError): boolean {
    return error.retryable;
  }

  /**
   * Hatayı logla (console + Sentry)
   * 
   * @param error - VideoError nesnesi
   * @param context - Hata context bilgisi
   */
  logError(error: VideoError, context?: ErrorContext): void {
    // Error log oluştur
    const errorLog: ErrorLog = {
      type: error.type,
      message: error.message,
      level: this._getLogLevel(error.type),
      context: context || {},
      stack: error.details?.originalError instanceof Error 
        ? error.details.originalError.stack 
        : undefined,
      timestamp: error.timestamp,
      browser: {
        userAgent: navigator.userAgent,
        language: navigator.language,
        online: navigator.onLine,
      },
    };

    // Console logging
    if (this.consoleLoggingEnabled) {
      this._logToConsole(errorLog);
    }

    // Sentry logging
    if (this.sentryEnabled) {
      this._logToSentry(errorLog);
    }
  }

  /**
   * Birden fazla hatayı toplu işle
   * 
   * @param errors - Hata listesi
   * @param context - Hata context bilgisi
   * @returns VideoError listesi
   */
  handleMultipleErrors(
    errors: unknown[],
    context?: ErrorContext
  ): VideoError[] {
    return errors.map(error => this.handleError(error, context));
  }

  /**
   * Hata istatistiklerini al (debugging için)
   * 
   * @param errors - VideoError listesi
   * @returns Hata istatistikleri
   */
  getErrorStats(errors: VideoError[]): Record<string, number> {
    const stats: Record<string, number> = {};

    errors.forEach(error => {
      stats[error.type] = (stats[error.type] || 0) + 1;
    });

    return stats;
  }

  // Private methods

  /**
   * Hatayı sınıflandır
   */
  private _classifyError(error: unknown): VideoErrorType {
    if (error instanceof Error) {
      const errorMessage = error.message.toLowerCase();
      const errorName = error.name.toLowerCase();

      // Timeout
      if (errorName === 'aborterror' || errorMessage.includes('timeout')) {
        return 'timeout';
      }

      // Network error
      if (
        errorName === 'typeerror' ||
        errorMessage.includes('fetch') ||
        errorMessage.includes('network') ||
        errorMessage.includes('failed to fetch')
      ) {
        return 'network';
      }

      // CORS error
      if (
        errorMessage.includes('cors') ||
        errorMessage.includes('cross-origin') ||
        errorMessage.includes('access-control')
      ) {
        return 'cors';
      }

      // Rate limit
      if (
        errorMessage.includes('429') ||
        errorMessage.includes('rate limit') ||
        errorMessage.includes('too many requests')
      ) {
        return 'rate_limit';
      }

      // Validation error (4xx except 429) - Check BEFORE server errors
      if (
        errorMessage.includes('400') ||
        errorMessage.includes('401') ||
        errorMessage.includes('403') ||
        errorMessage.includes('404') ||
        errorMessage.includes('validation')
      ) {
        return 'validation';
      }

      // Server error (5xx)
      if (
        errorMessage.includes('500') ||
        errorMessage.includes('502') ||
        errorMessage.includes('503') ||
        errorMessage.includes('504') ||
        errorMessage.includes('backend error') ||
        errorMessage.includes('server error')
      ) {
        return 'server';
      }
    }

    return 'unknown';
  }

  /**
   * Hata mesajını çıkar
   */
  private _extractErrorMessage(error: unknown): string {
    if (error instanceof Error) {
      return error.message;
    }

    if (typeof error === 'string') {
      return error;
    }

    return 'Unknown error occurred';
  }

  /**
   * Status code'u çıkar
   */
  private _extractStatusCode(error: unknown): number | undefined {
    if (error instanceof Error) {
      const message = error.message;
      
      // Extract status code from message (e.g., "Backend error: 500")
      const match = message.match(/\b([45]\d{2})\b/);
      if (match) {
        return parseInt(match[1], 10);
      }
    }

    return undefined;
  }

  /**
   * Kullanıcı dostu mesaj üret
   */
  private _generateUserMessage(
    errorType: VideoErrorType,
    statusCode?: number
  ): string {
    switch (errorType) {
      case 'timeout':
        return '⏰ İstek zaman aşımına uğradı. Lütfen tekrar deneyin.';

      case 'network':
        return '🌐 İnternet bağlantınızı kontrol edin ve tekrar deneyin.';

      case 'server':
        if (statusCode === 500) {
          return '🔧 Sunucu hatası oluştu. Lütfen birkaç dakika sonra tekrar deneyin.';
        } else if (statusCode === 502 || statusCode === 503) {
          return '⚠️ Video servisi şu anda bakımda. Lütfen daha sonra tekrar deneyin.';
        } else if (statusCode === 504) {
          return '⏱️ Sunucu yanıt vermedi. Lütfen tekrar deneyin.';
        }
        return '❌ Video servisi şu anda erişilebilir değil. Lütfen birkaç dakika sonra tekrar deneyin.';

      case 'cors':
        return '🔒 Bağlantı güvenlik hatası oluştu. Lütfen sistem yöneticisi ile iletişime geçin.';

      case 'rate_limit':
        return '⚡ Çok fazla istek gönderildi. Lütfen 1-2 dakika bekleyip tekrar deneyin.';

      case 'validation':
        if (statusCode === 401) {
          return '🔐 Oturum süreniz dolmuş. Lütfen tekrar giriş yapın.';
        } else if (statusCode === 403) {
          return '🚫 Bu işlem için yetkiniz yok.';
        } else if (statusCode === 404) {
          return '🔍 İstenen kaynak bulunamadı.';
        }
        return '📝 Gönderilen veri geçersiz. Lütfen bilgilerinizi kontrol edin.';

      case 'unknown':
      default:
        return '❓ Beklenmeyen bir hata oluştu. Lütfen tekrar deneyin veya destek ekibi ile iletişime geçin.';
    }
  }

  /**
   * Retry kararı ver
   */
  private _shouldRetry(
    errorType: VideoErrorType,
    statusCode?: number
  ): boolean {
    switch (errorType) {
      case 'timeout':
        return true; // Timeout hatalarında retry yap

      case 'network':
        return true; // Network hatalarında retry yap

      case 'server':
        // 5xx hatalarında retry yap (503 hariç - bakım modu)
        return statusCode !== 503;

      case 'rate_limit':
        return false; // Rate limit'te retry yapma (kullanıcı beklemeli)

      case 'cors':
        return false; // CORS hatası retry ile çözülmez

      case 'validation':
        return false; // Validation hataları retry ile çözülmez

      case 'unknown':
        return true; // Bilinmeyen hatalarda bir kez retry dene

      default:
        return false;
    }
  }

  /**
   * Önerilen aksiyon belirle
   */
  private _getSuggestedAction(
    errorType: VideoErrorType,
    retryable: boolean
  ): string {
    if (retryable) {
      return 'retry';
    }

    switch (errorType) {
      case 'network':
        return 'check_connection';

      case 'cors':
        return 'contact_admin';

      case 'rate_limit':
        return 'wait_and_retry';

      case 'validation':
        return 'check_input';

      default:
        return 'show_fallback';
    }
  }

  /**
   * Log level belirle
   */
  private _getLogLevel(errorType: VideoErrorType): 'error' | 'warning' | 'info' {
    switch (errorType) {
      case 'server':
      case 'cors':
      case 'unknown':
        return 'error';

      case 'timeout':
      case 'network':
      case 'rate_limit':
        return 'warning';

      case 'validation':
        return 'info';

      default:
        return 'error';
    }
  }

  /**
   * Console'a logla
   */
  private _logToConsole(errorLog: ErrorLog): void {
    const logMethod = errorLog.level === 'error' 
      ? console.error 
      : errorLog.level === 'warning' 
        ? console.warn 
        : console.info;

    logMethod('🎬 VideoErrorHandler:', {
      type: errorLog.type,
      message: errorLog.message,
      level: errorLog.level,
      timestamp: errorLog.timestamp.toISOString(),
      context: errorLog.context,
      browser: errorLog.browser,
      stack: errorLog.stack,
    });
  }

  /**
   * Sentry'ye logla (opsiyonel)
   */
  private _logToSentry(errorLog: ErrorLog): void {
    // Sentry entegrasyonu için placeholder
    // Gerçek implementasyonda Sentry SDK kullanılacak
    
    try {
      // @ts-ignore - Sentry global object
      if (typeof window !== 'undefined' && window.Sentry) {
        // @ts-ignore
        window.Sentry.captureException(new Error(errorLog.message), {
          level: errorLog.level,
          tags: {
            errorType: errorLog.type,
            requestId: errorLog.context.requestId,
          },
          extra: {
            context: errorLog.context,
            browser: errorLog.browser,
            timestamp: errorLog.timestamp,
          },
        });
      }
    } catch (sentryError) {
      console.warn('Failed to log to Sentry:', sentryError);
    }
  }
}

/**
 * Singleton instance for global usage
 */
let globalInstance: VideoErrorHandler | null = null;

/**
 * Get or create global VideoErrorHandler instance
 * 
 * @returns VideoErrorHandler
 */
export function getVideoErrorHandler(): VideoErrorHandler {
  if (!globalInstance) {
    globalInstance = new VideoErrorHandler();
  }
  return globalInstance;
}

/**
 * Create new VideoErrorHandler instance
 * 
 * @param sentryEnabled - Sentry logging aktif mi?
 * @param consoleLoggingEnabled - Console logging aktif mi?
 * @returns VideoErrorHandler
 */
export function createVideoErrorHandler(
  sentryEnabled?: boolean,
  consoleLoggingEnabled?: boolean
): VideoErrorHandler {
  return new VideoErrorHandler(sentryEnabled, consoleLoggingEnabled);
}

/**
 * Helper function: Hatayı hızlıca işle ve kullanıcı mesajı al
 * 
 * @param error - Orijinal hata
 * @param context - Hata context bilgisi
 * @returns Kullanıcı dostu hata mesajı
 */
export function getQuickErrorMessage(
  error: unknown,
  context?: ErrorContext
): string {
  const handler = getVideoErrorHandler();
  const videoError = handler.handleError(error, context);
  return videoError.userMessage;
}

/**
 * Helper function: Hatanın retry edilebilir olup olmadığını kontrol et
 * 
 * @param error - Orijinal hata
 * @returns Retry yapılabilir mi?
 */
export function isRetryableError(error: unknown): boolean {
  const handler = getVideoErrorHandler();
  const videoError = handler.handleError(error);
  return videoError.retryable;
}

export default VideoErrorHandler;
