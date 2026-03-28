/**
 * useAccessibilityAnnouncer Hook
 * Easy-to-use hook for ARIA live region announcements
 * WCAG 2.1 Level AA - 4.1.3 Status Messages
 */

import { useState, useCallback } from 'react';

import type { Announcement, AnnouncementPriority } from '../components/ui/AccessibilityAnnouncer';

let announcementIdCounter = 0;

export interface UseAccessibilityAnnouncerReturn {
  announcements: Announcement[]
  announce: (message: string, priority?: AnnouncementPriority, timeout?: number) => void
  announceSuccess: (message: string) => void
  announceError: (message: string) => void
  announceInfo: (message: string) => void
  clear: () => void
}

/**
 * useAccessibilityAnnouncer Hook
 *
 * Provides functions to announce messages to screen readers.
 *
 * @example
 * ```tsx
 * const { announcements, announceSuccess, announceError } = useAccessibilityAnnouncer()
 *
 * // In your component
 * <AccessibilityAnnouncer announcements={announcements} />
 *
 * // Success notification
 * announceSuccess('Sınav başarıyla kaydedildi')
 *
 * // Error notification (urgent)
 * announceError('Hata: Bağlantı kurulamadı')
 * ```
 */
export const useAccessibilityAnnouncer = (): UseAccessibilityAnnouncerReturn => {
  const [announcements, setAnnouncements] = useState<Announcement[]>([]);

  const announce = useCallback(
    (message: string, priority: AnnouncementPriority = 'polite', timeout = 3000) => {
      const id = `announcement-${++announcementIdCounter}`;

      setAnnouncements((prev) => [
        ...prev,
        {
          id,
          message,
          priority,
          timeout,
        },
      ]);

      // Auto-remove after timeout
      if (timeout) {
        setTimeout(() => {
          setAnnouncements((prev) => prev.filter((a) => a.id !== id));
        }, timeout);
      }
    },
    [],
  );

  const announceSuccess = useCallback(
    (message: string) => {
      announce(`Başarılı: ${message}`, 'polite', 3000);
    },
    [announce],
  );

  const announceError = useCallback(
    (message: string) => {
      announce(`Hata: ${message}`, 'assertive', 5000);
    },
    [announce],
  );

  const announceInfo = useCallback(
    (message: string) => {
      announce(message, 'polite', 3000);
    },
    [announce],
  );

  const clear = useCallback(() => {
    setAnnouncements([]);
  }, []);

  return {
    announcements,
    announce,
    announceSuccess,
    announceError,
    announceInfo,
    clear,
  };
};

export default useAccessibilityAnnouncer;
