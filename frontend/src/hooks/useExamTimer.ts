/**
 * useExamTimer Hook
 *
 * Custom hook for managing exam countdown timer
 * Handles time updates, warnings, and auto-submit on time expiration
 */

import { useEffect, useCallback, useRef } from 'react';

import { examService } from '../services/examService';
import { useExamStore } from '../store/examStore';

export interface ExamTimerCallbacks {
  onTimeWarning?: (type: 'halfway' | 'final' | 'critical') => void
  onTimeUp?: () => void
  onAutoSubmit?: () => void
}

export interface UseExamTimerReturn {
  remainingTime: number
  isRunning: boolean
  warnings: {
    halfway: boolean
    final: boolean
    critical: boolean
  }
}

/**
 * Hook for managing exam timer with automatic updates and warnings
 *
 * @param sessionId - Exam session ID
 * @param callbacks - Callback functions for timer events
 * @returns Timer state and controls
 *
 * @example
 * const { remainingTime, warnings } = useExamTimer(sessionId, {
 *   onTimeWarning: (type) => showWarning(type),
 *   onTimeUp: () => submitExam()
 * })
 */
export const useExamTimer = (
  sessionId: string,
  callbacks: ExamTimerCallbacks = {},
): UseExamTimerReturn => {
  const { onTimeWarning, onTimeUp, onAutoSubmit } = callbacks;

  // Get timer state from examStore
  const remainingTime = useExamStore((state) => state.remainingTime);
  const session = useExamStore((state) => state.session);
  const setRemainingTime = useExamStore((state) => state.setRemainingTime);
  const decrementTime = useExamStore((state) => state.decrementTime);

  // Track warnings to avoid duplicates
  const warningsShownRef = useRef({
    halfway: false,
    final: false,
    critical: false,
  });

  // Calculate total duration
  const totalDuration = session?.duration_minutes ? session.duration_minutes * 60 : 0;

  // Determine if timer is running
  const isRunning = session?.status === 'in_progress' && remainingTime > 0;

  /**
   * Check and trigger time warnings
   */
  const checkWarnings = useCallback(() => {
    if (!totalDuration || !onTimeWarning) {return;}

    const halfwayPoint = totalDuration / 2;
    const finalWarning = 300; // 5 minutes
    const criticalWarning = 60; // 1 minute

    // Halfway warning (50% time remaining)
    if (remainingTime <= halfwayPoint && !warningsShownRef.current.halfway) {
      warningsShownRef.current.halfway = true;
      onTimeWarning('halfway');
    }

    // Final warning (5 minutes remaining)
    if (remainingTime <= finalWarning && !warningsShownRef.current.final) {
      warningsShownRef.current.final = true;
      onTimeWarning('final');
    }

    // Critical warning (1 minute remaining)
    if (remainingTime <= criticalWarning && !warningsShownRef.current.critical) {
      warningsShownRef.current.critical = true;
      onTimeWarning('critical');
    }
  }, [remainingTime, totalDuration, onTimeWarning]);

  /**
   * Handle time expiration
   */
  const handleTimeUp = useCallback(() => {
    if (onTimeUp) {
      onTimeUp();
    }
    if (onAutoSubmit) {
      onAutoSubmit();
    }
  }, [onTimeUp, onAutoSubmit]);

  /**
   * Timer countdown effect
   */
  useEffect(() => {
    if (!isRunning) {return;}

    // Decrement timer every second
    const interval = setInterval(() => {
      decrementTime();
      checkWarnings();

      // Check if time is up — read from store to avoid stale closure
      const currentTime = useExamStore.getState().remainingTime;
      if (currentTime <= 1) {
        handleTimeUp();
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [isRunning, decrementTime, checkWarnings, handleTimeUp]);

  /**
   * Sync with server periodically (every 30 seconds)
   */
  useEffect(() => {
    if (!isRunning || !sessionId) {return;}

    const syncInterval = setInterval(async () => {
      try {
        const timeData = await examService.getRemainingTime(sessionId);
        setRemainingTime(timeData.remaining_seconds);
      } catch (error) {
        console.error('Failed to sync timer with server:', error);
      }
    }, 30000); // 30 seconds

    return () => clearInterval(syncInterval);
  }, [isRunning, sessionId, setRemainingTime]);

  return {
    remainingTime,
    isRunning,
    warnings: warningsShownRef.current,
  };
};

/**
 * Format seconds to MM:SS or HH:MM:SS
 *
 * @param seconds - Total seconds
 * @returns Formatted time string
 */
export const formatTime = (seconds: number): string => {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;

  if (hours > 0) {
    return `${hours.toString().padStart(2, '0')}:${minutes
      .toString()
      .padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }

  return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
};

/**
 * Get timer color based on remaining time
 *
 * @param remainingSeconds - Seconds remaining
 * @param totalSeconds - Total exam duration in seconds
 * @returns MUI color
 */
export const getTimerColor = (
  remainingSeconds: number,
  totalSeconds: number,
): 'success' | 'warning' | 'error' => {
  const percentage = (remainingSeconds / totalSeconds) * 100;

  if (percentage > 50) {return 'success';}
  if (percentage > 10) {return 'warning';}
  return 'error';
};

export default useExamTimer;
