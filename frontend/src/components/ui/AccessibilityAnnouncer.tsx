/**
 * Accessibility Announcer Component
 * ARIA live region for screen reader announcements
 * WCAG 2.1 Level AA - 4.1.3 Status Messages
 */

import React, { useEffect, useState } from 'react'
import { Box } from '@mui/material'

export type AnnouncementPriority = 'polite' | 'assertive' | 'off'

export interface Announcement {
  id: string
  message: string
  priority: AnnouncementPriority
  timeout?: number
}

interface AccessibilityAnnouncerProps {
  announcements: Announcement[]
  onAnnouncementComplete?: (id: string) => void
}

/**
 * AccessibilityAnnouncer Component
 *
 * Provides ARIA live regions for dynamic content announcements.
 * Screen readers will announce messages based on priority:
 * - polite: Waits for current speech to finish
 * - assertive: Interrupts current speech
 * - off: No announcement (silent)
 *
 * @example
 * ```tsx
 * const [announcements, setAnnouncements] = useState<Announcement[]>([])
 *
 * // Success message
 * setAnnouncements([...announcements, {
 *   id: '1',
 *   message: 'Sınav başarıyla kaydedildi',
 *   priority: 'polite',
 *   timeout: 3000
 * }])
 *
 * // Error message (urgent)
 * setAnnouncements([...announcements, {
 *   id: '2',
 *   message: 'Hata: Bağlantı kurulamadı',
 *   priority: 'assertive'
 * }])
 * ```
 */
export const AccessibilityAnnouncer: React.FC<AccessibilityAnnouncerProps> = ({
  announcements,
  onAnnouncementComplete,
}) => {
  const [activeAnnouncements, setActiveAnnouncements] = useState<Announcement[]>([])

  useEffect(() => {
    setActiveAnnouncements(announcements)

    // Auto-remove announcements with timeout
    announcements.forEach((announcement) => {
      if (announcement.timeout) {
        setTimeout(() => {
          setActiveAnnouncements((prev) =>
            prev.filter((a) => a.id !== announcement.id)
          )
          onAnnouncementComplete?.(announcement.id)
        }, announcement.timeout)
      }
    })
  }, [announcements, onAnnouncementComplete])

  // Group announcements by priority
  const politeAnnouncements = activeAnnouncements.filter((a) => a.priority === 'polite')
  const assertiveAnnouncements = activeAnnouncements.filter((a) => a.priority === 'assertive')

  return (
    <>
      {/* Polite announcements - waits for current speech */}
      {politeAnnouncements.length > 0 && (
        <Box
          role="status"
          aria-live="polite"
          aria-atomic="true"
          sx={{
            position: 'absolute',
            left: '-10000px',
            width: '1px',
            height: '1px',
            overflow: 'hidden',
          }}
        >
          {politeAnnouncements.map((announcement) => (
            <span key={announcement.id}>{announcement.message}</span>
          ))}
        </Box>
      )}

      {/* Assertive announcements - interrupts current speech */}
      {assertiveAnnouncements.length > 0 && (
        <Box
          role="alert"
          aria-live="assertive"
          aria-atomic="true"
          sx={{
            position: 'absolute',
            left: '-10000px',
            width: '1px',
            height: '1px',
            overflow: 'hidden',
          }}
        >
          {assertiveAnnouncements.map((announcement) => (
            <span key={announcement.id}>{announcement.message}</span>
          ))}
        </Box>
      )}
    </>
  )
}

export default AccessibilityAnnouncer
