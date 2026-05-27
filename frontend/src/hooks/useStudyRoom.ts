/**
 * useStudyRoom(id) — fetches a single study room and provides join/leave actions.
 *
 * Backed by:
 *   GET  /api/v1/study-rooms/{id}       — room detail
 *   POST /api/v1/study-rooms/{id}/join  — join PUBLIC room
 *   POST /api/v1/study-rooms/{id}/leave — leave room
 */

import { useState, useEffect, useCallback } from 'react';

import { studyRoomService, StudyRoom } from '../services/studyRoomService';

interface UseStudyRoomReturn {
  room: StudyRoom | null;
  isLoading: boolean;
  error: string | null;
  joinRoom: () => Promise<void>;
  leaveRoom: () => Promise<void>;
  deleteRoom: () => Promise<void>;
  isActionPending: boolean;
  refetch: () => Promise<void>;
}

export function useStudyRoom(id: string): UseStudyRoomReturn {
  const [room, setRoom] = useState<StudyRoom | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isActionPending, setIsActionPending] = useState(false);

  const refetch = useCallback(async () => {
    if (!id) return;
    setIsLoading(true);
    setError(null);
    try {
      const data = await studyRoomService.getRoom(id);
      setRoom(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Oda yüklenemedi');
    } finally {
      setIsLoading(false);
    }
  }, [id]);

  useEffect(() => {
    refetch();
  }, [refetch]);

  const joinRoom = useCallback(async () => {
    setIsActionPending(true);
    try {
      const updated = await studyRoomService.joinRoom(id);
      setRoom(updated);
    } catch (err) {
      throw err instanceof Error ? err : new Error('Odaya katılınamadı');
    } finally {
      setIsActionPending(false);
    }
  }, [id]);

  const leaveRoom = useCallback(async () => {
    setIsActionPending(true);
    try {
      await studyRoomService.leaveRoom(id);
      setRoom(null);
    } catch (err) {
      throw err instanceof Error ? err : new Error('Odadan ayrılınamadı');
    } finally {
      setIsActionPending(false);
    }
  }, [id]);

  const deleteRoom = useCallback(async () => {
    setIsActionPending(true);
    try {
      await studyRoomService.deleteRoom(id);
      setRoom(null);
    } catch (err) {
      throw err instanceof Error ? err : new Error('Oda silinemedi');
    } finally {
      setIsActionPending(false);
    }
  }, [id]);

  return { room, isLoading, error, joinRoom, leaveRoom, deleteRoom, isActionPending, refetch };
}
