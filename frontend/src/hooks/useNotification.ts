/**
 * useNotification Hook
 * Easy-to-use notification hook for components
 */

import { useCallback } from 'react';

import { useNotificationStore } from '../store/notificationStore';
import { NotificationOptions } from '../types/notification';

export const useNotification = () => {
  const { addNotification, removeNotification, clearAll } = useNotificationStore();

  const success = useCallback(
    (message: string, options?: NotificationOptions) => {
      return addNotification('success', message, options);
    },
    [addNotification],
  );

  const error = useCallback(
    (message: string, options?: NotificationOptions) => {
      return addNotification('error', message, options);
    },
    [addNotification],
  );

  const warning = useCallback(
    (message: string, options?: NotificationOptions) => {
      return addNotification('warning', message, options);
    },
    [addNotification],
  );

  const info = useCallback(
    (message: string, options?: NotificationOptions) => {
      return addNotification('info', message, options);
    },
    [addNotification],
  );

  const remove = useCallback(
    (id: string) => {
      removeNotification(id);
    },
    [removeNotification],
  );

  const clear = useCallback(() => {
    clearAll();
  }, [clearAll]);

  return {
    success,
    error,
    warning,
    info,
    remove,
    clear,
  };
};

/**
 * Service status notification helpers
 */
export const useServiceNotification = () => {
  const notification = useNotification();

  const notifyServiceDown = useCallback(
    (serviceName: string) => {
      notification.error(`${serviceName} servisi şu anda kullanılamıyor`, {
        title: 'Servis Hatası',
        duration: 0, // Persistent
        action: {
          label: 'Yeniden Dene',
          onClick: () => window.location.reload(),
        },
      });
    },
    [notification],
  );

  const notifyServiceDegraded = useCallback(
    (serviceName: string) => {
      notification.warning(`${serviceName} servisi yavaş çalışıyor`, {
        title: 'Servis Uyarısı',
        duration: 7000,
      });
    },
    [notification],
  );

  const notifyServiceRestored = useCallback(
    (serviceName: string) => {
      notification.success(`${serviceName} servisi normale döndü`, {
        title: 'Servis Aktif',
        duration: 5000,
      });
    },
    [notification],
  );

  const notifyDatabaseDown = useCallback(() => {
    notifyServiceDown('Veritabanı');
  }, [notifyServiceDown]);

  const notifyRedisDown = useCallback(() => {
    notifyServiceDown('Önbellek');
  }, [notifyServiceDown]);

  const notifyApiError = useCallback(
    (message?: string) => {
      notification.error(message || 'API isteği başarısız oldu', {
        title: 'API Hatası',
        duration: 5000,
      });
    },
    [notification],
  );

  return {
    notifyServiceDown,
    notifyServiceDegraded,
    notifyServiceRestored,
    notifyDatabaseDown,
    notifyRedisDown,
    notifyApiError,
  };
};
