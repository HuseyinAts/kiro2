/**
 * useStudyRooms + useStudyRoom hook unit tests
 *
 * Mocks studyRoomService; verifies state transitions for
 * list fetch, create, join, leave, delete.
 */

import { renderHook, act, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';

import { useStudyRooms } from '../useStudyRooms';
import { useStudyRoom } from '../useStudyRoom';
import { studyRoomService } from '../../services/studyRoomService';
import type { StudyRoom, StudyRoomListResponse } from '../../services/studyRoomService';

// ─── Mocks ────────────────────────────────────────────────────────────────────

vi.mock('../../services/studyRoomService', () => ({
  studyRoomService: {
    getMyRooms: vi.fn(),
    getRoom: vi.fn(),
    createRoom: vi.fn(),
    joinRoom: vi.fn(),
    leaveRoom: vi.fn(),
    deleteRoom: vi.fn(),
  },
}));

const mockRoom: StudyRoom = {
  id: 'room-1',
  name: 'Test Odası',
  description: 'Açıklama',
  topic: 'Matematik',
  owner_id: 'user-1',
  status: 'active',
  visibility: 'public',
  max_members: 50,
  current_member_count: 1,
  tags: ['TYT'],
  created_at: '2026-05-27T00:00:00Z',
  user_role: 'owner',
};

const mockListResponse: StudyRoomListResponse = {
  rooms: [mockRoom],
  total: 1,
};

// ─── useStudyRooms ────────────────────────────────────────────────────────────

describe('useStudyRooms', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (studyRoomService.getMyRooms as ReturnType<typeof vi.fn>).mockResolvedValue(mockListResponse);
  });

  it('fetches rooms on mount and populates state', async () => {
    const { result } = renderHook(() => useStudyRooms());

    expect(result.current.isLoading).toBe(true);

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.rooms).toHaveLength(1);
    expect(result.current.rooms[0].id).toBe('room-1');
    expect(result.current.total).toBe(1);
    expect(result.current.error).toBeNull();
  });

  it('sets error state on fetch failure', async () => {
    (studyRoomService.getMyRooms as ReturnType<typeof vi.fn>).mockRejectedValue(
      new Error('Network error'),
    );

    const { result } = renderHook(() => useStudyRooms());

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.error).toBe('Network error');
    expect(result.current.rooms).toHaveLength(0);
  });

  it('createRoom prepends new room to list', async () => {
    const newRoom: StudyRoom = { ...mockRoom, id: 'room-2', name: 'Yeni Oda', user_role: 'owner' };
    (studyRoomService.createRoom as ReturnType<typeof vi.fn>).mockResolvedValue(newRoom);

    const { result } = renderHook(() => useStudyRooms());
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    await act(async () => {
      await result.current.createRoom({ name: 'Yeni Oda', visibility: 'public' });
    });

    expect(result.current.rooms[0].id).toBe('room-2');
    expect(result.current.total).toBe(2);
    expect(result.current.isCreating).toBe(false);
  });
});

// ─── useStudyRoom ─────────────────────────────────────────────────────────────

describe('useStudyRoom', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (studyRoomService.getRoom as ReturnType<typeof vi.fn>).mockResolvedValue(mockRoom);
  });

  it('fetches room detail on mount', async () => {
    const { result } = renderHook(() => useStudyRoom('room-1'));

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.room?.id).toBe('room-1');
    expect(result.current.error).toBeNull();
  });

  it('joinRoom updates room state', async () => {
    const joinedRoom: StudyRoom = { ...mockRoom, current_member_count: 2, user_role: 'member' };
    (studyRoomService.joinRoom as ReturnType<typeof vi.fn>).mockResolvedValue(joinedRoom);

    const { result } = renderHook(() => useStudyRoom('room-1'));
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    await act(async () => {
      await result.current.joinRoom();
    });

    expect(result.current.room?.current_member_count).toBe(2);
    expect(result.current.room?.user_role).toBe('member');
    expect(result.current.isActionPending).toBe(false);
  });

  it('leaveRoom clears room state', async () => {
    (studyRoomService.leaveRoom as ReturnType<typeof vi.fn>).mockResolvedValue(undefined);

    const { result } = renderHook(() => useStudyRoom('room-1'));
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    await act(async () => {
      await result.current.leaveRoom();
    });

    expect(result.current.room).toBeNull();
  });

  it('deleteRoom clears room state', async () => {
    (studyRoomService.deleteRoom as ReturnType<typeof vi.fn>).mockResolvedValue(undefined);

    const { result } = renderHook(() => useStudyRoom('room-1'));
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    await act(async () => {
      await result.current.deleteRoom();
    });

    expect(result.current.room).toBeNull();
  });
});
