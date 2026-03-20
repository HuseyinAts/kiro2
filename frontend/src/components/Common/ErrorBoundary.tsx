import { AlertTriangle, Home, RefreshCw } from 'lucide-react';
import { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  resetKeys?: Array<string | number>;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

/**
 * ErrorBoundary Component
 *
 * React uygulamasında beklenmeyen hataları yakalayan ve kullanıcı dostu
 * bir hata mesajı gösteren Error Boundary bileşeni.
 *
 * Özellikler:
 * - Hata durumunda özel fallback UI gösterimi
 * - Hata loglaması ve dış servislere raporlama
 * - Sayfa yenileme ve ana sayfaya dönüş seçenekleri
 * - Geliştirme ortamında detaylı hata bilgileri
 * - Özelleştirilebilir hata callback fonksiyonu
 *
 * @example
 * <ErrorBoundary onError={(error) => logToSentry(error)}>
 *   <App />
 * </ErrorBoundary>
 */
class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): State {
    // Hata yakalandığında state güncelle
    return {
      hasError: true,
      error,
      errorInfo: null,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Hata detaylarını state'e kaydet
    this.setState({
      error,
      errorInfo,
    });

    // Hatayı konsola logla
    console.error('ErrorBoundary caught an error:', error, errorInfo);

    // Dış hata raporlama servisi (Sentry, LogRocket, vb.)
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // Production ortamında hata raporlama servisi çağrılabilir
    if (process.env.NODE_ENV === 'production') {
      this.reportErrorToService(error, errorInfo);
    }
  }

  componentDidUpdate(prevProps: Props) {
    // resetKeys değiştiğinde hatayı sıfırla
    if (
      this.state.hasError &&
      this.props.resetKeys &&
      !this.areResetKeysEqual(prevProps.resetKeys, this.props.resetKeys)
    ) {
      this.resetErrorBoundary();
    }
  }

  areResetKeysEqual(
    prevKeys?: Array<string | number>,
    nextKeys?: Array<string | number>,
  ): boolean {
    if (!prevKeys || !nextKeys) {return true;}
    if (prevKeys.length !== nextKeys.length) {return false;}
    return prevKeys.every((key, index) => key === nextKeys[index]);
  }

  resetErrorBoundary = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  reportErrorToService = (error: Error, errorInfo: ErrorInfo) => {
    // Burada Sentry, LogRocket gibi servislere hata gönderilebilir
    // Örnek: Sentry.captureException(error, { extra: errorInfo });

    // API endpoint'e hata gönder (opsiyonel)
    try {
      fetch('/api/v1/errors/report', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          error: {
            name: error.name,
            message: error.message,
            stack: error.stack,
          },
          errorInfo: {
            componentStack: errorInfo.componentStack,
          },
          timestamp: new Date().toISOString(),
          userAgent: navigator.userAgent,
          url: window.location.href,
        }),
      }).catch((err) => {
        console.error('Failed to report error:', err);
      });
    } catch (err) {
      // Hata raporlama başarısız olursa sessizce geç
      console.error('Error reporting failed:', err);
    }
  };

  handleReload = () => {
    window.location.reload();
  };

  handleGoHome = () => {
    window.location.href = '/';
  };

  render() {
    if (this.state.hasError) {
      // Özel fallback varsa onu kullan
      if (this.props.fallback) {
        return this.props.fallback;
      }

      const isDevelopment = process.env.NODE_ENV === 'development';

      // Varsayılan hata UI
      return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-red-50 to-orange-50 p-4">
          <div className="max-w-2xl w-full bg-white rounded-2xl shadow-xl overflow-hidden">
            {/* Header */}
            <div className="bg-gradient-to-r from-red-500 to-orange-500 p-6 text-white">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-white/20 rounded-xl backdrop-blur-sm">
                  <AlertTriangle className="w-8 h-8" />
                </div>
                <div>
                  <h1 className="text-2xl font-bold">Beklenmeyen Bir Hata Oluştu</h1>
                  <p className="text-white/90 mt-1">
                    Üzgünüz, bir sorun oluştu. Lütfen sayfayı yenileyin veya ana sayfaya dönün.
                  </p>
                </div>
              </div>
            </div>

            {/* Body */}
            <div className="p-6 space-y-6">
              {/* Hata Mesajı */}
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <p className="text-sm font-medium text-red-800">
                  {this.state.error?.message || 'Bilinmeyen bir hata'}
                </p>
              </div>

              {/* Geliştirme Ortamı - Detaylı Bilgi */}
              {isDevelopment && (
                <details className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                  <summary className="cursor-pointer font-medium text-gray-700 hover:text-gray-900">
                    Geliştirici Bilgileri (Sadece Development)
                  </summary>
                  <div className="mt-4 space-y-4">
                    {/* Error Stack */}
                    {this.state.error?.stack && (
                      <div>
                        <h3 className="text-sm font-semibold text-gray-700 mb-2">
                          Error Stack:
                        </h3>
                        <pre className="text-xs bg-gray-900 text-green-400 p-3 rounded overflow-x-auto">
                          {this.state.error.stack}
                        </pre>
                      </div>
                    )}

                    {/* Component Stack */}
                    {this.state.errorInfo?.componentStack && (
                      <div>
                        <h3 className="text-sm font-semibold text-gray-700 mb-2">
                          Component Stack:
                        </h3>
                        <pre className="text-xs bg-gray-900 text-yellow-400 p-3 rounded overflow-x-auto">
                          {this.state.errorInfo.componentStack}
                        </pre>
                      </div>
                    )}
                  </div>
                </details>
              )}

              {/* Yardımcı Bilgiler */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h3 className="font-medium text-blue-900 mb-2">Ne Yapabilirsiniz?</h3>
                <ul className="text-sm text-blue-800 space-y-1 list-disc list-inside">
                  <li>Sayfayı yenileyin</li>
                  <li>Ana sayfaya dönün</li>
                  <li>Tarayıcı önbelleğini temizleyin</li>
                  <li>Daha sonra tekrar deneyin</li>
                </ul>
              </div>

              {/* Aksiyon Butonları */}
              <div className="flex flex-col sm:flex-row gap-3">
                <button
                  onClick={this.handleReload}
                  className="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-gradient-to-r from-red-500 to-orange-500 text-white font-medium rounded-lg hover:from-red-600 hover:to-orange-600 transition-all duration-200 shadow-lg hover:shadow-xl"
                >
                  <RefreshCw className="w-5 h-5" />
                  Sayfayı Yenile
                </button>

                <button
                  onClick={this.handleGoHome}
                  className="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-white text-gray-700 font-medium rounded-lg border-2 border-gray-300 hover:border-gray-400 hover:bg-gray-50 transition-all duration-200"
                >
                  <Home className="w-5 h-5" />
                  Ana Sayfaya Dön
                </button>
              </div>

              {/* Reset Boundary Button (Development) */}
              {isDevelopment && (
                <button
                  onClick={this.resetErrorBoundary}
                  className="w-full px-6 py-2 bg-gray-100 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-200 transition-colors"
                >
                  🔄 Error Boundary&apos;yi Sıfırla (Dev Only)
                </button>
              )}
            </div>

            {/* Footer */}
            <div className="bg-gray-50 px-6 py-4 border-t border-gray-200">
              <p className="text-xs text-gray-500 text-center">
                Sorun devam ederse lütfen destek ekibi ile iletişime geçin
              </p>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
