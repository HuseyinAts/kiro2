import React from 'react';
import { Loader2, AlertCircle, CheckCircle2 } from 'lucide-react';

/**
 * LoadingSpinner Component
 *
 * Yükleme durumunu gösteren spinner bileşeni.
 * Farklı boyut ve renk seçenekleri ile özelleştirilebilir.
 */
interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  color?: 'primary' | 'white' | 'gray';
  className?: string;
  text?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'md',
  color = 'primary',
  className = '',
  text,
}) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
    xl: 'w-12 h-12',
  };

  const colorClasses = {
    primary: 'text-blue-600',
    white: 'text-white',
    gray: 'text-gray-600',
  };

  return (
    <div className={`flex items-center justify-center gap-2 ${className}`}>
      <Loader2 className={`${sizeClasses[size]} ${colorClasses[color]} animate-spin`} />
      {text && <span className="text-sm text-gray-600">{text}</span>}
    </div>
  );
};

/**
 * FullPageLoader Component
 *
 * Tam sayfa yükleme göstergesi.
 * Sayfa geçişleri ve büyük veri yüklemeleri için kullanılır.
 */
interface FullPageLoaderProps {
  message?: string;
  subMessage?: string;
}

export const FullPageLoader: React.FC<FullPageLoaderProps> = ({
  message = 'Yükleniyor...',
  subMessage,
}) => {
  return (
    <div className="fixed inset-0 bg-white/80 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="text-center space-y-4">
        <LoadingSpinner size="xl" />
        <div>
          <p className="text-lg font-medium text-gray-900">{message}</p>
          {subMessage && <p className="text-sm text-gray-500 mt-1">{subMessage}</p>}
        </div>
      </div>
    </div>
  );
};

/**
 * SkeletonLoader Component
 *
 * İçerik yüklenirken gösterilen iskelet yükleyici.
 * Daha iyi kullanıcı deneyimi için placeholder görünümü sağlar.
 */
interface SkeletonLoaderProps {
  type?: 'text' | 'card' | 'avatar' | 'image' | 'table';
  count?: number;
  className?: string;
}

export const SkeletonLoader: React.FC<SkeletonLoaderProps> = ({
  type = 'text',
  count = 1,
  className = '',
}) => {
  const skeletons = Array.from({ length: count });

  const renderSkeleton = () => {
    switch (type) {
      case 'text':
        return (
          <div className={`space-y-3 ${className}`}>
            {skeletons.map((_, i) => (
              <div key={i} className="h-4 bg-gray-200 rounded animate-pulse" />
            ))}
          </div>
        );

      case 'card':
        return (
          <div className="space-y-4">
            {skeletons.map((_, i) => (
              <div key={i} className={`bg-white rounded-lg border p-4 space-y-3 ${className}`}>
                <div className="h-6 bg-gray-200 rounded animate-pulse w-3/4" />
                <div className="h-4 bg-gray-200 rounded animate-pulse w-full" />
                <div className="h-4 bg-gray-200 rounded animate-pulse w-5/6" />
              </div>
            ))}
          </div>
        );

      case 'avatar':
        return (
          <div className="flex items-center gap-3">
            {skeletons.map((_, i) => (
              <div key={i} className="flex items-center gap-3">
                <div className="w-10 h-10 bg-gray-200 rounded-full animate-pulse" />
                <div className="space-y-2">
                  <div className="h-4 w-24 bg-gray-200 rounded animate-pulse" />
                  <div className="h-3 w-16 bg-gray-200 rounded animate-pulse" />
                </div>
              </div>
            ))}
          </div>
        );

      case 'image':
        return (
          <div className="space-y-4">
            {skeletons.map((_, i) => (
              <div
                key={i}
                className={`aspect-video bg-gray-200 rounded-lg animate-pulse ${className}`}
              />
            ))}
          </div>
        );

      case 'table':
        return (
          <div className="space-y-2">
            <div className="h-10 bg-gray-200 rounded animate-pulse" />
            {skeletons.map((_, i) => (
              <div key={i} className="h-12 bg-gray-100 rounded animate-pulse" />
            ))}
          </div>
        );

      default:
        return null;
    }
  };

  return <>{renderSkeleton()}</>;
};

/**
 * ErrorState Component
 *
 * Hata durumunu gösteren bileşen.
 * Kullanıcı dostu hata mesajları ve retry seçeneği sunar.
 */
interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  retryText?: string;
  className?: string;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'Bir Hata Oluştu',
  message,
  onRetry,
  retryText = 'Tekrar Dene',
  className = '',
}) => {
  return (
    <div className={`flex flex-col items-center justify-center p-8 text-center ${className}`}>
      <div className="bg-red-50 rounded-full p-3 mb-4">
        <AlertCircle className="w-8 h-8 text-red-500" />
      </div>
      <h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>
      <p className="text-gray-600 mb-6 max-w-md">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors"
        >
          {retryText}
        </button>
      )}
    </div>
  );
};

/**
 * EmptyState Component
 *
 * İçerik olmadığında gösterilen boş durum bileşeni.
 */
interface EmptyStateProps {
  title?: string;
  message: string;
  actionText?: string;
  onAction?: () => void;
  icon?: React.ReactNode;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title = 'Veri Bulunamadı',
  message,
  actionText,
  onAction,
  icon,
  className = '',
}) => {
  return (
    <div className={`flex flex-col items-center justify-center p-8 text-center ${className}`}>
      {icon && <div className="mb-4">{icon}</div>}
      <h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>
      <p className="text-gray-600 mb-6 max-w-md">{message}</p>
      {actionText && onAction && (
        <button
          onClick={onAction}
          className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
        >
          {actionText}
        </button>
      )}
    </div>
  );
};

/**
 * SuccessState Component
 *
 * Başarılı işlem sonrası gösterilen bileşen.
 */
interface SuccessStateProps {
  title?: string;
  message: string;
  actionText?: string;
  onAction?: () => void;
  className?: string;
}

export const SuccessState: React.FC<SuccessStateProps> = ({
  title = 'Başarılı!',
  message,
  actionText,
  onAction,
  className = '',
}) => {
  return (
    <div className={`flex flex-col items-center justify-center p-8 text-center ${className}`}>
      <div className="bg-green-50 rounded-full p-3 mb-4">
        <CheckCircle2 className="w-8 h-8 text-green-500" />
      </div>
      <h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>
      <p className="text-gray-600 mb-6 max-w-md">{message}</p>
      {actionText && onAction && (
        <button
          onClick={onAction}
          className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors"
        >
          {actionText}
        </button>
      )}
    </div>
  );
};

/**
 * LoadingButton Component
 *
 * Yükleme durumu olan buton bileşeni.
 */
interface LoadingButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  isLoading?: boolean;
  loadingText?: string;
  children: React.ReactNode;
  variant?: 'primary' | 'secondary' | 'danger';
}

export const LoadingButton: React.FC<LoadingButtonProps> = ({
  isLoading = false,
  loadingText = 'Yükleniyor...',
  children,
  variant = 'primary',
  className = '',
  disabled,
  ...props
}) => {
  const variantClasses = {
    primary: 'bg-blue-600 hover:bg-blue-700 text-white',
    secondary: 'bg-gray-200 hover:bg-gray-300 text-gray-800',
    danger: 'bg-red-600 hover:bg-red-700 text-white',
  };

  return (
    <button
      {...props}
      disabled={isLoading || disabled}
      className={`
        px-4 py-2 rounded-lg font-medium transition-colors
        disabled:opacity-50 disabled:cursor-not-allowed
        flex items-center justify-center gap-2
        ${variantClasses[variant]}
        ${className}
      `}
    >
      {isLoading && <Loader2 className="w-4 h-4 animate-spin" />}
      {isLoading ? loadingText : children}
    </button>
  );
};

/**
 * ProgressBar Component
 *
 * İlerleme çubuğu bileşeni.
 */
interface ProgressBarProps {
  progress: number; // 0-100 arası
  showLabel?: boolean;
  size?: 'sm' | 'md' | 'lg';
  color?: 'blue' | 'green' | 'red' | 'yellow';
  className?: string;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  progress,
  showLabel = true,
  size = 'md',
  color = 'blue',
  className = '',
}) => {
  const sizeClasses = {
    sm: 'h-1',
    md: 'h-2',
    lg: 'h-3',
  };

  const colorClasses = {
    blue: 'bg-blue-600',
    green: 'bg-green-600',
    red: 'bg-red-600',
    yellow: 'bg-yellow-600',
  };

  const clampedProgress = Math.min(100, Math.max(0, progress));

  return (
    <div className={className}>
      <div className={`w-full bg-gray-200 rounded-full overflow-hidden ${sizeClasses[size]}`}>
        <div
          className={`${sizeClasses[size]} ${colorClasses[color]} transition-all duration-300 rounded-full`}
          style={{ width: `${clampedProgress}%` }}
        />
      </div>
      {showLabel && (
        <div className="text-xs text-gray-600 mt-1 text-right">{Math.round(clampedProgress)}%</div>
      )}
    </div>
  );
};

/**
 * InlineLoader Component
 *
 * Satır içi yükleme göstergesi.
 * Metin yanında veya küçük alanlarda kullanılır.
 */
interface InlineLoaderProps {
  text?: string;
  size?: 'sm' | 'md';
  className?: string;
}

export const InlineLoader: React.FC<InlineLoaderProps> = ({
  text = 'Yükleniyor',
  size = 'sm',
  className = '',
}) => {
  return (
    <div className={`inline-flex items-center gap-2 ${className}`}>
      <LoadingSpinner size={size} />
      <span className="text-sm text-gray-600">{text}</span>
    </div>
  );
};

/**
 * PulseLoader Component
 *
 * Pulse animasyonlu yükleyici.
 */
export const PulseLoader: React.FC<{ className?: string }> = ({ className = '' }) => {
  return (
    <div className={`flex gap-2 ${className}`}>
      <div className="w-3 h-3 bg-blue-600 rounded-full animate-pulse" />
      <div className="w-3 h-3 bg-blue-600 rounded-full animate-pulse delay-75" />
      <div className="w-3 h-3 bg-blue-600 rounded-full animate-pulse delay-150" />
    </div>
  );
};

/**
 * ContentLoader Component
 *
 * İçerik alanları için wrapper loader.
 * Loading/Error/Empty/Success durumlarını otomatik yönetir.
 */
interface ContentLoaderProps {
  isLoading: boolean;
  error?: string | null;
  isEmpty?: boolean;
  onRetry?: () => void;
  loadingComponent?: React.ReactNode;
  errorComponent?: React.ReactNode;
  emptyComponent?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}

export const ContentLoader: React.FC<ContentLoaderProps> = ({
  isLoading,
  error,
  isEmpty = false,
  onRetry,
  loadingComponent,
  errorComponent,
  emptyComponent,
  children,
  className = '',
}) => {
  if (isLoading) {
    return <div className={className}>{loadingComponent || <SkeletonLoader type="card" count={3} />}</div>;
  }

  if (error) {
    return (
      <div className={className}>
        {errorComponent || <ErrorState message={error} onRetry={onRetry} />}
      </div>
    );
  }

  if (isEmpty) {
    return (
      <div className={className}>
        {emptyComponent || (
          <EmptyState message="Gösterilecek veri bulunmamaktadır." />
        )}
      </div>
    );
  }

  return <div className={className}>{children}</div>;
};

export default {
  LoadingSpinner,
  FullPageLoader,
  SkeletonLoader,
  ErrorState,
  EmptyState,
  SuccessState,
  LoadingButton,
  ProgressBar,
  InlineLoader,
  PulseLoader,
  ContentLoader,
};
