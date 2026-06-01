/**
 * Student Feedback Service — Faz 7.2
 *
 * Beta öğrencilerinin hatalı/tuhaf soru raporlaması için API client.
 * Backend: /api/v1/quality/feedback/*
 */

import { apiClient } from './apiClient';

export type FlagType =
  | 'wrong_answer'
  | 'wrong_topic'
  | 'solution_visible'
  | 'incomplete_text'
  | 'circular'
  | 'figure_needed'
  | 'other';

export interface FlagCreatePayload {
  question_id: string;
  flag_type: FlagType;
  note?: string;
}

export interface FlagResponse {
  id: string;
  user_id: string;
  question_id: string;
  flag_type: FlagType;
  note: string | null;
  created_at: string;
  resolved_at: string | null;
  resolution: string | null;
}

const BASE = '/api/v1/quality/feedback';

export const feedbackService = {
  async submitFlag(payload: FlagCreatePayload): Promise<FlagResponse> {
    const response = await apiClient.post<FlagResponse>(`${BASE}/flag`, payload);
    return response.data;
  },

  async listMyFlags(limit = 50): Promise<FlagResponse[]> {
    const response = await apiClient.get<FlagResponse[]>(`${BASE}/my-flags`, {
      params: { limit },
    });
    return response.data;
  },
};
