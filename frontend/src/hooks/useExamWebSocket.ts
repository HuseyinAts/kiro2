/**
 * useExamWebSocket Hook (Migrated to Polling)
 *
 * ⚠️ MIGRATION NOTE:
 * Backend WebSocket endpoints are currently disabled (backend/main.py:2063-2071).
 * This hook now uses polling (periodic API requests) instead of WebSocket for exam updates.
 *
 * Polling interval: 5 seconds
 * Updates: time, performance, exam status
 *
 * Future: When backend WebSocket is re-enabled, this can be reverted to use WebSocket.
 *
 * Custom hook for managing periodic exam updates
 * Handles time tracking, performance updates, and exam status
 */

import { useEffect, useRef, useCallback, useState } from 'react';

import { examService } from '../services/examService';
import { useExamStore } from '../store/examStore';

export interface WebSocketMessage {
  type: 'time_update' | 'time_warning' | 'auto_submit' | 'connection' | 'performance_update'
  data?: any
  remaining_time?: number
  status?: string
}

export interface WebSocketCallbacks {
  onTimeUpdate?: (remainingTime: number) => void
  onTimeWarning?: () => void
  onAutoSubmit?: () => void
  onPerformanceUpdate?: (performance: any) => void
  onConnectionChange?: (connected: boolean) => void
}

export interface UseExamWebSocketReturn {
  connected: boolean
  reconnect: () => void
  disconnect: () => void
}

/**
 * Hook for managing periodic exam updates (polling-based)
 *
 * @param sessionId - Exam session ID
 * @param enabled - Whether polling should be active
 * @param callbacks - Event callbacks
 * @returns Polling connection state and controls
 *
 * @example
 * const { connected } = useExamWebSocket(sessionId, true, {
 *   onTimeUpdate: (time) => console.log('Time:', time),
 *   onAutoSubmit: () => submitExam()
 * })
 */
export const useExamWebSocket = (
  sessionId: string,
  enabled: boolean = true,
  callbacks: WebSocketCallbacks = {},
): UseExamWebSocketReturn => {
  const {
    onTimeUpdate,
    onTimeWarning,
    onAutoSubmit,
    onPerformanceUpdate,
    onConnectionChange,
  } = callbacks;

  // Store state
  const setConnected = useExamStore((state) => state.setConnected);
  const setRemainingTime = useExamStore((state) => state.setRemainingTime);
  const refreshPerformance = useExamStore((state) => state.refreshPerformance);
  const isConnected = useExamStore((state) => state.isConnected);

  // Local state for polling
  const [isPolling, setIsPolling] = useState(false);
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const lastRemainingTimeRef = useRef<number | null>(null);

  /**
   * Fetch exam status and updates from API
   * Replaces WebSocket message handling
   */
  const fetchExamUpdates = useCallback(async () => {
    if (!sessionId) {return;}

    try {
      // Fetch current exam session status
      const session = await examService.getExamSession(sessionId);

      // Calculate remaining time
      if (session.started_at && session.duration_minutes) {
        const startTime = new Date(session.started_at).getTime();
        const durationMs = session.duration_minutes * 60 * 1000;
        const elapsedMs = Date.now() - startTime;
        const remainingMs = Math.max(0, durationMs - elapsedMs);
        const remainingSeconds = Math.floor(remainingMs / 1000);

        // Update remaining time
        setRemainingTime(remainingSeconds);
        if (onTimeUpdate) {
          onTimeUpdate(remainingSeconds);
        }

        // Time warnings
        const lastTime = lastRemainingTimeRef.current;
        lastRemainingTimeRef.current = remainingSeconds;

        // 5 minute warning
        if (lastTime !== null && lastTime > 300 && remainingSeconds <= 300 && onTimeWarning) {
          onTimeWarning();
        }

        // Auto-submit when time expires
        if (remainingSeconds === 0 && session.status === 'in_progress' && onAutoSubmit) {
          onAutoSubmit();
        }
      }

      // Fetch performance updates
      try {
        const performance = await examService.getPerformance(sessionId);
        if (onPerformanceUpdate) {
          onPerformanceUpdate(performance);
        }
        refreshPerformance();
      } catch (perfError) {
        // Performance fetch is optional, don't fail the whole update
        console.debug('Performance fetch skipped:', perfError);
      }

    } catch (error) {
      console.error('Exam status fetch failed:', error);
      setConnected(false);
      if (onConnectionChange) {
        onConnectionChange(false);
      }
    }
  }, [
    sessionId,
    setRemainingTime,
    setConnected,
    refreshPerformance,
    onTimeUpdate,
    onTimeWarning,
    onAutoSubmit,
    onPerformanceUpdate,
    onConnectionChange,
  ]);

  /**
   * Start polling
   */
  const connect = useCallback(() => {
    if (!sessionId || !enabled || isPolling) {return;}

    setIsPolling(true);
    setConnected(true);
    if (onConnectionChange) {
      onConnectionChange(true);
    }

    // Immediate first fetch
    fetchExamUpdates();

    // Set up polling interval (5 seconds)
    pollingIntervalRef.current = setInterval(() => {
      fetchExamUpdates();
    }, 5000);

  }, [sessionId, enabled, isPolling, fetchExamUpdates, setConnected, onConnectionChange]);

  /**
   * Stop polling
   */
  const disconnect = useCallback(() => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
    setIsPolling(false);
    setConnected(false);
    lastRemainingTimeRef.current = null;
    if (onConnectionChange) {
      onConnectionChange(false);
    }
  }, [setConnected, onConnectionChange]);

  /**
   * Auto-start polling on mount
   */
  useEffect(() => {
    if (enabled && sessionId) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [sessionId, enabled, connect, disconnect]);

  return {
    connected: isConnected,
    reconnect: connect,
    disconnect,
  };
};

export default useExamWebSocket;
