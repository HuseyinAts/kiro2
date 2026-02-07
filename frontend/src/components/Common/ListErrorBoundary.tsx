import { AlertCircle, RefreshCw, ChevronDown } from 'lucide-react';
import { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  /** Liste adı (hata mesajında gösterilir) */
  listName?: string;
  /** Hata durumunda gösterilecek özel fallback */
  fallback?: ReactNode;
  /** Hata callback'i */
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  /** Yeniden deneme fonksiyonu */
  onRetry?: () => void;
  /** Compact mod (daha küçük UI) */
  compact?: boolean;
}

interface State {
  hasError: boolean;
  error: Error | null;
  showDetails: boolean;
}

/**
 * ListErrorBoundary - Liste componentleri için özelleştirilmiş Error Boundary
 *
 * Özellikler:
 * - Liste verisi yüklenirken oluşan hataları yakalar
 * - Kompakt ve tam boyutlu mod
 * - Yeniden deneme butonu
 * - Hata detayları (development modunda)
 *
 * @example
 * <ListErrorBoundary listName="Kullanıcı Listesi" onRetry={refetch}>
 *   <UserList data={users} />
 * </ListErrorBoundary>
 */
class ListErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      showDetails: false,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error(`ListErrorBoundary [${this.props.listName || 'Unknown'}]:`, error, errorInfo);

    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null });
    if (this.props.onRetry) {
      this.props.onRetry();
    }
  };

  toggleDetails = () => {
    this.setState((prev) => ({ showDetails: !prev.showDetails }));
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      const { compact = false, listName = 'Liste' } = this.props;
      const isDev = process.env.NODE_ENV === 'development';

      if (compact) {
        // Kompakt mod - tablo satırı içinde kullanım için
        return (
          <div className="flex items-center justify-center p-4 bg-red-50 border border-red-200 rounded-lg">
            <AlertCircle className="w-5 h-5 text-red-500 mr-2" />
            <span className="text-sm text-red-700">{listName} yüklenirken hata oluştu</span>
            {this.props.onRetry && (
              <button
                onClick={this.handleRetry}
                className="ml-3 text-sm text-red-600 hover:text-red-800 underline"
              >
                Tekrar dene
              </button>
            )}
          </div>
        );
      }

      // Tam boyutlu mod
      return (
        <div className="w-full bg-white border border-red-200 rounded-lg shadow-sm overflow-hidden">
          {/* Header */}
          <div className="bg-red-50 px-4 py-3 border-b border-red-200">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-red-500" />
              <h3 className="font-medium text-red-800">{listName} Yüklenemedi</h3>
            </div>
          </div>

          {/* Body */}
          <div className="p-4 space-y-3">
            <p className="text-sm text-gray-600">
              {listName} verileri yüklenirken beklenmeyen bir hata oluştu.
              Lütfen tekrar deneyin veya daha sonra geri gelin.
            </p>

            {/* Error Message */}
            {this.state.error && (
              <div className="bg-red-50 border border-red-100 rounded p-3">
                <p className="text-sm text-red-700 font-mono">
                  {this.state.error.message}
                </p>
              </div>
            )}

            {/* Dev Details */}
            {isDev && this.state.error?.stack && (
              <div>
                <button
                  onClick={this.toggleDetails}
                  className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700"
                >
                  <ChevronDown
                    className={`w-4 h-4 transition-transform ${
                      this.state.showDetails ? 'rotate-180' : ''
                    }`}
                  />
                  Geliştirici Detayları
                </button>
                {this.state.showDetails && (
                  <pre className="mt-2 p-2 bg-gray-900 text-green-400 text-xs rounded overflow-x-auto max-h-40">
                    {this.state.error.stack}
                  </pre>
                )}
              </div>
            )}

            {/* Actions */}
            <div className="flex gap-2 pt-2">
              {this.props.onRetry && (
                <button
                  onClick={this.handleRetry}
                  className="flex items-center gap-2 px-4 py-2 bg-red-500 text-white text-sm font-medium rounded-lg hover:bg-red-600 transition-colors"
                >
                  <RefreshCw className="w-4 h-4" />
                  Tekrar Dene
                </button>
              )}
              <button
                onClick={() => window.location.reload()}
                className="px-4 py-2 bg-gray-100 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-200 transition-colors"
              >
                Sayfayı Yenile
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ListErrorBoundary;

/**
 * HOC: Liste componentlerini ErrorBoundary ile sarmalayan Higher-Order Component
 *
 * @example
 * const SafeUserList = withListErrorBoundary(UserList, 'Kullanıcı Listesi');
 */
export function withListErrorBoundary<P extends object>(
  WrappedComponent: React.ComponentType<P>,
  listName: string,
  options?: { compact?: boolean; onError?: (error: Error, errorInfo: ErrorInfo) => void },
) {
  const displayName = WrappedComponent.displayName || WrappedComponent.name || 'Component';

  const WithErrorBoundary = (props: P & { onRetry?: () => void }) => {
    return (
      <ListErrorBoundary
        listName={listName}
        compact={options?.compact}
        onError={options?.onError}
        onRetry={props.onRetry}
      >
        <WrappedComponent {...props} />
      </ListErrorBoundary>
    );
  };

  WithErrorBoundary.displayName = `withListErrorBoundary(${displayName})`;

  return WithErrorBoundary;
}
