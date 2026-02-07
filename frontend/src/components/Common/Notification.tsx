/**
 * Notification Component
 * Turkish user-friendly notification system
 */

import * as React from 'react';

import { useNotificationStore } from '../../store/notificationStore';
import { Notification as NotificationType, NotificationIcons } from '../../types/notification';

interface NotificationItemProps {
  notification: NotificationType;
  onClose: (id: string) => void;
}

const NotificationItem: React.FC<NotificationItemProps> = ({ notification, onClose }) => {
  const { id, type, title, message, closable, action } = notification;

  const colors = {
    success: 'bg-green-50 border-green-500 text-green-900',
    error: 'bg-red-50 border-red-500 text-red-900',
    warning: 'bg-yellow-50 border-yellow-500 text-yellow-900',
    info: 'bg-blue-50 border-blue-500 text-blue-900',
  };

  const iconColors = {
    success: 'text-green-600',
    error: 'text-red-600',
    warning: 'text-yellow-600',
    info: 'text-blue-600',
  };

  return (
    <div
      className={`flex items-start gap-3 p-4 mb-3 border-l-4 rounded-lg shadow-lg ${colors[type]}`}
      role="alert"
      aria-live="polite"
    >
      {/* Icon */}
      <div className={`text-xl ${iconColors[type]}`} aria-hidden="true">
        {NotificationIcons[type]}
      </div>

      {/* Content */}
      <div className="flex-1">
        {title && <div className="font-semibold mb-1">{title}</div>}
        <div className="text-sm">{message}</div>

        {/* Action Button */}
        {action && (
          <button
            onClick={() => {
              action.onClick();
              onClose(id);
            }}
            className="mt-2 text-sm font-medium underline hover:no-underline focus:outline-none focus:ring-2 focus:ring-offset-2"
          >
            {action.label}
          </button>
        )}
      </div>

      {/* Close Button */}
      {closable && (
        <button
          onClick={() => onClose(id)}
          className="text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 rounded"
          aria-label="Bildirimi kapat"
        >
          <svg
            className="w-5 h-5"
            fill="none"
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path d="M6 18L18 6M6 6l12 12"></path>
          </svg>
        </button>
      )}
    </div>
  );
};

export const NotificationContainer: React.FC = () => {
  const { notifications, removeNotification } = useNotificationStore();

  // Group notifications by position
  const notificationsByPosition = notifications.reduce((acc: Record<string, NotificationType[]>, notification: NotificationType) => {
    const position = notification.position || 'top-right';
    if (!acc[position]) {
      acc[position] = [];
    }
    acc[position].push(notification);
    return acc;
  }, {} as Record<string, NotificationType[]>);

  const positionClasses = {
    'top-left': 'top-4 left-4',
    'top-center': 'top-4 left-1/2 -translate-x-1/2',
    'top-right': 'top-4 right-4',
    'bottom-left': 'bottom-4 left-4',
    'bottom-center': 'bottom-4 left-1/2 -translate-x-1/2',
    'bottom-right': 'bottom-4 right-4',
  };

  return (
    <>
      {(Object.entries(notificationsByPosition) as [string, NotificationType[]][]).map(([position, notifs]) => (
        <div
          key={position}
          className={`fixed z-50 w-full max-w-sm ${positionClasses[position as keyof typeof positionClasses]}`}
        >
          {notifs.map((notification) => (
            <NotificationItem
              key={notification.id}
              notification={notification}
              onClose={removeNotification}
            />
          ))}
        </div>
      ))}
    </>
  );
};

/**
 * Example Usage:
 *
 * import { useNotification } from '@/hooks/useNotification';
 *
 * const MyComponent = () => {
 *   const notification = useNotification();
 *
 *   const handleSuccess = () => {
 *     notification.success('İşlem başarıyla tamamlandı!');
 *   };
 *
 *   const handleError = () => {
 *     notification.error('Bir hata oluştu, lütfen tekrar deneyin.');
 *   };
 *
 *   return (
 *     <div>
 *       <button onClick={handleSuccess}>Başarı</button>
 *       <button onClick={handleError}>Hata</button>
 *     </div>
 *   );
 * };
 */
