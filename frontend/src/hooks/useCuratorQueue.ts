/**
 * Curator Queue Hooks — Faz 3.2
 *
 * Admin-only hooks for the question curation workflow.
 * Backed by /api/v1/curator/* endpoints (Faz 3.1 backend).
 *
 * Auth: httpOnly cookie (credentials: 'include'), no Authorization header.
 *
 * Hooks:
 *   - useCuratorQueue(filters)   : paginated queue list
 *   - useCuratorVerdict()        : submit verify/reject/archive
 *   - useCuratorStats()          : header stats bar
 */

import { useMutation, useQuery, useQueryClient } from 'react-query';

import { apiRequest } from '../utils/apiHelpers';

// ============================================================================
// Types
// ============================================================================

export type CuratorVerdict = 'verify' | 'reject' | 'archive';

export type QueueStatus = 'bronze_clean' | 'pending' | 'unverified';

export interface QueueItem {
  id: string;
  question_text: string;
  options: {
    A?: string;
    B?: string;
    C?: string;
    D?: string;
    E?: string;
  };
  correct_answer: string;
  subject_area: string;
  difficulty_level?: string | null;
  quality_review_status: string;
  image_url?: string | null;
  misconception_tags?: string[] | null;
  solution_steps?: string[] | null;
  similar_question_ids?: string[] | null;
}

export interface QueueResponse {
  items: QueueItem[];
  total: number;
  page: number;
  per_page: number;
}

export interface QueueFilters {
  status: QueueStatus;
  subject?: string;
  has_diagram?: 'yes' | 'no' | 'all';
  page: number;
  per_page?: number;
}

export interface VerdictPayload {
  question_id: string;
  verdict: CuratorVerdict;
  notes?: string;
  reviewer_velocity_seconds?: number;
}

export interface CuratorStats {
  pending_count: number;
  verified_today: number;
  rejected_today: number;
  avg_velocity_sec: number | null;
}

// ============================================================================
// Query keys
// ============================================================================

export const curatorKeys = {
  all: ['curator'] as const,
  queue: (filters: QueueFilters) => ['curator', 'queue', filters] as const,
  stats: () => ['curator', 'stats'] as const,
};

// ============================================================================
// Internal helpers
// ============================================================================

function buildQueueQuery(filters: QueueFilters): string {
  const params = new URLSearchParams();
  params.set('status', filters.status);
  params.set('page', String(filters.page));
  if (filters.per_page) params.set('per_page', String(filters.per_page));
  if (filters.subject) params.set('subject', filters.subject);
  if (filters.has_diagram && filters.has_diagram !== 'all') {
    params.set('has_diagram', filters.has_diagram);
  }
  return params.toString();
}

// ============================================================================
// Hooks
// ============================================================================

/**
 * Paginated curator queue. Auto-refetches when filters change.
 * Uses keepPreviousData so pagination doesn't flicker.
 */
export function useCuratorQueue(filters: QueueFilters) {
  return useQuery<QueueResponse, Error>({
    queryKey: curatorKeys.queue(filters),
    queryFn: () =>
      apiRequest<QueueResponse>(`/api/v1/curator/queue?${buildQueueQuery(filters)}`),
    keepPreviousData: true,
    staleTime: 30 * 1000, // 30s — queue moves fast
    retry: 1,
  });
}

/**
 * Submit a curator verdict for a single question.
 * Invalidates queue + stats so the next item is fresh.
 */
export function useCuratorVerdict() {
  const queryClient = useQueryClient();

  return useMutation<{ ok: boolean }, Error, VerdictPayload>({
    mutationFn: (payload) =>
      apiRequest<{ ok: boolean }>('/api/v1/curator/verdict', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: curatorKeys.all });
    },
    retry: 0, // verdict is non-idempotent — don't auto-retry
  });
}

/**
 * Curator stats for the header bar.
 * Refetches every 60s while the page is open.
 */
export function useCuratorStats() {
  return useQuery<CuratorStats, Error>({
    queryKey: curatorKeys.stats(),
    queryFn: () => apiRequest<CuratorStats>('/api/v1/curator/stats'),
    refetchInterval: 60 * 1000,
    staleTime: 30 * 1000,
    retry: 1,
  });
}
