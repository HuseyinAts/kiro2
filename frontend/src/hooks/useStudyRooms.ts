/**
 * useStudyRooms — fetches the caller's study rooms (owned + joined).
 *
 * Backed by GET /api/v1/study-rooms/my-rooms (real DB, S197).
 */

import { useState, useEffect, useCallback } from 'react';

import {
  studyRoomService,
  StudyRoom,
  CreateStudyRoomPayload,
} from '../services/studyRoomService';

interface UseStudyRoomsReturn {
  rooms: StudyRoom[];
  total: number;
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  createRoom: (payload: CreateStudyRoomPayload) => Promise<StudyRoom>;
  isCreating: boolean;
}

export function useStudyRooms(): UseStudyRoomsReturn {
  const [rooms, setRooms] = useState<StudyRoom[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);

  const refetch = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await studyRoomService.getMyRooms();
      setRooms(data.rooms);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Odalar yüklenemedi');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refetch();
  }, [refetch]);

  const createRoom = useCallback(
    async (payload: CreateStudyRoomPayload): Promise<StudyRoom> => {
      setIsCreating(true);
      try {
        const room = await studyRoomService.createRoom(payload);
        setRooms((prev) => [room, ...prev]);
        setTotal((prev) => prev + 1);
        return room;
      } finally {
        setIsCreating(false);
      }
    },
    [],
  );

  return { rooms, total, isLoading, error, refetch, createRoom, isCreating };
}
