/**
 * Notification Store
 * Global notification state management using Zustand
 */

import { create } from 'zustand';

import {
  Notification,
  NotificationOptions,
  NotificationType,
  NotificationDuration,
  NotificationTitles,
} from '../types/notification';

interface NotificationStore {
  notifications: Notification[];
  addNotification: (
    type: NotificationType,
    message: string,
    options?: NotificationOptions
  ) => string;
  removeNotification: (id: string) => void;
  clearAll: () => void;

  // Convenience methods
  success: (message: string, options?: NotificationOptions) => string;
  error: (message: string, options?: NotificationOptions) => string;
  warning: (message: string, options?: NotificationOptions) => string;
  info: (message: string, options?: NotificationOptions) => string;
}

/**
 * Generate unique notification ID
 */
const generateId = (): string => {
  return `notification-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
};

export const useNotificationStore = create<NotificationStore>((set, get) => ({
  notifications: [],

  addNotification: (type, message, options = {}): string => {
    const id = generateId();

    const duration = options.duration ?? NotificationDuration.MEDIUM;

    const notification: Notification = {
      id,
      type,
      title: options.title || NotificationTitles[type],
      message,
      duration,
      position: options.position || 'top-right',
      closable: options.closable ?? true,
      action: options.action,
      createdAt: Date.now(),
    };

    set((state) => ({
      notifications: [...state.notifications, notification],
    }));

    // Auto-remove after duration (if not persistent)
    if (duration > 0) {
      setTimeout(() => {
        set((state) => ({
          notifications: state.notifications.filter((n) => n.id !== id),
        }));
      }, duration);
    }

    return id;
  },

  removeNotification: (id) => {
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
    }));
  },

  clearAll: () => {
    set({ notifications: [] });
  },

  // Convenience methods
  success: (message, options): string => {
    return get().addNotification('success', message, options);
  },

  error: (message, options): string => {
    return get().addNotification('error', message, options);
  },

  warning: (message, options): string => {
    return get().addNotification('warning', message, options);
  },

  info: (message, options): string => {
    return get().addNotification('info', message, options);
  },
}));
