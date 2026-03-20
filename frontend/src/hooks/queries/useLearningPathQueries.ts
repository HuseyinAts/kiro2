/**
 * Learning Path Queries - React Query based queries
 *
 * Provides query hooks for Learning Path data fetching
 * with automatic caching and background refetch.
 */

import { useQuery, useQueryClient } from 'react-query';
import { apiRequest } from '../../utils/apiHelpers';
import { createLearningPath } from '../../api';
import { convertPathToNodes } from '../../utils/learningPathHelpers';
import { PathNodeData } from '../../components/LearningPath/PathNode';

// ============================================================================
// Query Keys
// ============================================================================

export const learningPathKeys = {
  all: ['learning-path'] as const,
  profile: (studentId: string) => [...learningPathKeys.all, 'profile', studentId] as const,
  path: (studentId: string, subject: string) => [...learningPathKeys.all, 'path', studentId, subject] as const,
  nodes: (studentId: string) => [...learningPathKeys.all, 'nodes', studentId] as const,
  completion: (studentId: string) => [...learningPathKeys.all, 'completion', studentId] as const,
  learningStyle: (studentId: string) => [...learningPathKeys.all, 'learning-style', studentId] as const,
};

// ============================================================================
// Queries
// ============================================================================

interface StudentProfile {
  student_id: string;
  learning_style: string;
  vark_profile?: {
    dominant: string;
    scores: Record<string, number>;
  };
}

interface LearningPath {
  path_id: string;
  subject: string;
  modules: Array<{
    module_id: string;
    title: string;
    topics: Array<{
      topic_id: string;
      title: string;
      difficulty: string;
    }>;
  }>;
}

interface CompletionStatus {
  data: Record<string, boolean>;
}

/**
 * Fetch student profile
 */
export const useStudentProfile = (studentId: string | null) => {
  return useQuery({
    queryKey: learningPathKeys.profile(studentId || ''),
    queryFn: async (): Promise<StudentProfile> => {
      const response = await apiRequest<StudentProfile>('/api/v1/learning-path/my-profile');
      return response;
    },
    enabled: !!studentId,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 2,
  });
};

/**
 * Fetch learning path for student
 */
export const useLearningPath = (studentId: string | null, subject: string) => {
  return useQuery({
    queryKey: learningPathKeys.path(studentId || '', subject),
    queryFn: async (): Promise<LearningPath> => {
      const response = await createLearningPath({
        student_id: studentId || '',
        subject,
      });
      return response as unknown as LearningPath;
    },
    enabled: !!studentId && !!subject,
    staleTime: 10 * 60 * 1000, // 10 minutes
    retry: 2,
  });
};

/**
 * Fetch path nodes with completion status
 */
export const usePathNodes = (studentId: string | null) => {
  return useQuery({
    queryKey: learningPathKeys.nodes(studentId || ''),
    queryFn: async (): Promise<PathNodeData[]> => {
      if (!studentId) return [];

      const [pathResponse, completionResponse] = await Promise.all([
        createLearningPath({ student_id: studentId, subject: 'matematik' }) as unknown as Promise<LearningPath>,
        apiRequest<CompletionStatus>(`/api/v1/learning-path/completion/${studentId}`),
      ]);

      const nodes = convertPathToNodes(pathResponse);
      const completion = completionResponse.data || {};

      // Apply completion status to nodes
      return nodes.map(node => ({
        ...node,
        status: completion[node.id] ? 'completed' : node.status,
      }));
    },
    enabled: !!studentId,
    staleTime: 2 * 60 * 1000, // 2 minutes
    retry: 2,
  });
};

/**
 * Fetch completion status
 */
export const useCompletionStatus = (studentId: string | null) => {
  return useQuery({
    queryKey: learningPathKeys.completion(studentId || ''),
    queryFn: async (): Promise<Record<string, boolean>> => {
      if (!studentId) return {};
      const response = await apiRequest<CompletionStatus>(`/api/v1/learning-path/completion/${studentId}`);
      return response.data || {};
    },
    enabled: !!studentId,
    staleTime: 60 * 1000, // 1 minute
    retry: 1,
  });
};

/**
 * Fetch learning style
 */
export const useLearningStyle = (studentId: string | null) => {
  return useQuery({
    queryKey: learningPathKeys.learningStyle(studentId || ''),
    queryFn: async (): Promise<string> => {
      if (!studentId) return 'mixed';
      const response = await apiRequest<{ data: { hybrid_code?: string; vark_profile?: { dominant: string } } }>(
        `/api/v1/learning-path/learning-style/${studentId}`,
      );
      return response.data?.hybrid_code || response.data?.vark_profile?.dominant || 'mixed';
    },
    enabled: !!studentId,
    staleTime: 30 * 60 * 1000, // 30 minutes
    retry: 2,
  });
};

// ============================================================================
// Query Client Helpers
// ============================================================================

export const useInvalidateLearningPath = () => {
  const queryClient = useQueryClient();

  return (studentId: string) => {
    queryClient.invalidateQueries({
      queryKey: learningPathKeys.profile(studentId),
    });
    queryClient.invalidateQueries({
      queryKey: learningPathKeys.nodes(studentId),
    });
    queryClient.invalidateQueries({
      queryKey: learningPathKeys.completion(studentId),
    });
  };
};