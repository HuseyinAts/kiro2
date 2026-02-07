/**
 * Notification System Types
 * Turkish user-friendly notification system for KIRO2 platform
 */

export type NotificationType = 'success' | 'error' | 'warning' | 'info';

export type NotificationPosition =
  | 'top-left'
  | 'top-center'
  | 'top-right'
  | 'bottom-left'
  | 'bottom-center'
  | 'bottom-right';

export interface Notification {
  id: string;
  type: NotificationType;
  title?: string;
  message: string;
  duration?: number; // milliseconds, 0 = no auto-close
  position?: NotificationPosition;
  closable?: boolean;
  action?: {
    label: string;
    onClick: () => void;
  };
  createdAt: number;
}

export interface NotificationOptions {
  title?: string;
  duration?: number;
  position?: NotificationPosition;
  closable?: boolean;
  action?: {
    label: string;
    onClick: () => void;
  };
}

/**
 * Service status notification types
 */
export type ServiceStatus = 'operational' | 'degraded' | 'down' | 'maintenance';

export interface ServiceNotification {
  service: 'database' | 'redis' | 'api' | 'auth' | 'ai';
  status: ServiceStatus;
  message: string;
  timestamp: number;
}

/**
 * Default notification durations (ms)
 */
export const NotificationDuration = {
  SHORT: 3000,
  MEDIUM: 5000,
  LONG: 7000,
  PERSISTENT: 0, // Manual close only
} as const;

/**
 * Notification icons (emoji or can be replaced with icon components)
 */
export const NotificationIcons = {
  success: '✓',
  error: '✗',
  warning: '⚠',
  info: 'ℹ',
} as const;

/**
 * Turkish notification titles
 */
export const NotificationTitles = {
  success: 'Başarılı',
  error: 'Hata',
  warning: 'Uyarı',
  info: 'Bilgi',
} as const;
