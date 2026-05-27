/**
 * Study Room Service — thin API wrapper over backend/api/study_rooms.py (S197)
 *
 * Endpoints backed by real DB (PostgreSQL 5434):
 *   POST   /api/v1/study-rooms/create        — create room
 *   GET    /api/v1/study-rooms/my-rooms      — owned + joined rooms
 *   GET    /api/v1/study-rooms/{id}          — room detail
 *   DELETE /api/v1/study-rooms/{id}          — soft delete (owner only)
 *   POST   /api/v1/study-rooms/{id}/join     — join public room
 *   POST   /api/v1/study-rooms/{id}/leave    — leave room
 */

import axios from 'axios';

// ─── Types aligned with backend StudyRoomResponse / StudyRoomCreate ──────────

export interface StudyRoom {
  id: string;
  name: string;
  description: string | null;
  topic: string | null;
  owner_id: string;
  status: 'active' | 'archived' | 'deleted';
  visibility: 'public' | 'private';
  max_members: number;
  current_member_count: number;
  tags: string[];
  created_at: string;
  user_role: string | null;
}

export interface StudyRoomListResponse {
  rooms: StudyRoom[];
  total: number;
}

export interface CreateStudyRoomPayload {
  name: string;
  description?: string;
  topic?: string;
  visibility?: 'public' | 'private';
  max_members?: number;
  tags?: string[];
}

// ─── Service ──────────────────────────────────────────────────────────────────

export const studyRoomService = {
  /** GET /api/v1/study-rooms/my-rooms — owned + joined active rooms */
  async getMyRooms(): Promise<StudyRoomListResponse> {
    const response = await axios.get<StudyRoomListResponse>(
      '/api/v1/study-rooms/my-rooms',
    );
    return response.data;
  },

  /** GET /api/v1/study-rooms/{id} — room detail (member or PUBLIC) */
  async getRoom(id: string): Promise<StudyRoom> {
    const response = await axios.get<StudyRoom>(`/api/v1/study-rooms/${id}`);
    return response.data;
  },

  /** POST /api/v1/study-rooms/create — create room, caller becomes OWNER */
  async createRoom(payload: CreateStudyRoomPayload): Promise<StudyRoom> {
    const response = await axios.post<StudyRoom>(
      '/api/v1/study-rooms/create',
      payload,
    );
    return response.data;
  },

  /** DELETE /api/v1/study-rooms/{id} — soft delete, owner only */
  async deleteRoom(id: string): Promise<void> {
    await axios.delete(`/api/v1/study-rooms/${id}`);
  },

  /** POST /api/v1/study-rooms/{id}/join — join PUBLIC room */
  async joinRoom(id: string): Promise<StudyRoom> {
    const response = await axios.post<StudyRoom>(
      `/api/v1/study-rooms/${id}/join`,
    );
    return response.data;
  },

  /** POST /api/v1/study-rooms/{id}/leave — leave room (non-owner) */
  async leaveRoom(id: string): Promise<void> {
    await axios.post(`/api/v1/study-rooms/${id}/leave`);
  },
};
