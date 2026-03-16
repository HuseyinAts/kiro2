/**
 * Learning Path Mutations - React Query based mutations
 *
 * Provides mutation hooks for Learning Path operations
 * with automatic cache management and retry logic.
 */

import { useMutation, useQueryClient } from 'react-query';
import { apiRequest } from '../../utils/apiHelpers';

interface UpdateProgressResponse {
  success: boolean;
  next_node_id?: string;
}

/**
 * Progress update mutation with automatic cache invalidation
 */
export const useUpdateProgress = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      studentId,
      nodeId,
      progress,
      completed,
    }: {
      studentId: string;
      nodeId: string;
      progress?: number;
      completed?: boolean;
    }): Promise<UpdateProgressResponse> => {
      const response = await apiRequest<UpdateProgressResponse>(
        `/api/learning-path/progress/${studentId}/${nodeId}`,
        {
          method: 'PUT',
          body: JSON.stringify({
            progress: progress ?? (completed ? 100 : undefined),
            completed: completed ?? false,
          }),
        },
      );
      return response;
    },
    onSuccess: (_data, variables) => {
      // Invalidate completion status cache
      queryClient.invalidateQueries({
        queryKey: ['learning-path', 'completion', variables.studentId],
      });
      // Invalidate path nodes cache
      queryClient.invalidateQueries({
        queryKey: ['learning-path', 'nodes', variables.studentId],
      });
    },
    retry: 2,
    retryDelay: (attemptIndex: number) => Math.min(1000 * 2 ** attemptIndex, 10000),
  });
};

/**
 * Mark node complete mutation
 * Convenience wrapper around useUpdateProgress
 */
export const useMarkNodeComplete = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      studentId,
      nodeId,
    }: {
      studentId: string;
      nodeId: string;
    }) => {
      const response = await apiRequest<UpdateProgressResponse>(
        `/api/learning-path/progress/${studentId}/${nodeId}`,
        {
          method: 'PUT',
          body: JSON.stringify({
            progress: 100,
            completed: true,
          }),
        },
      );
      return response;
    },
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['learning-path', 'completion', variables.studentId],
      });
    },
    retry: 2,
  });
};

/**
 * Submit quiz result mutation
 */
export const useSubmitQuizResult = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      studentId,
      quizId,
      answers,
      score,
    }: {
      studentId: string;
      quizId: string;
      answers: Record<string, string>;
      score: number;
    }) => {
      const response = await apiRequest<{ success: boolean }>(
        `/api/learning-path/quiz/${quizId}/submit`,
        {
          method: 'POST',
          body: JSON.stringify({
            student_id: studentId,
            answers,
            score,
            completed_at: new Date().toISOString(),
          }),
        },
      );
      return response;
    },
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['learning-path', 'nodes', variables.studentId],
      });
    },
    retry: 1,
  });
};