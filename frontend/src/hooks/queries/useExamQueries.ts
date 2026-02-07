/**
 * Exam-related React Query Hooks
 *
 * Provides React Query hooks for exam operations
 * Integrates with examStore for state management
 */

import { useQuery, useMutation, useQueryClient } from 'react-query';

import { queryConfig } from '../../config/reactQuery';
import { examService, CreateExamRequest } from '../../services/examService';
import { useExamStore } from '../../store';
import { queryKeys } from '../useQueryKeys';

/**
 * Query: Get exam session info
 */
export const useExamSession = (sessionId: string) => {
  const loadSession = useExamStore((state) => state.loadSession);

  return useQuery(
    queryKeys.exam.session(sessionId),
    async () => {
      const session = await examService.getSessionInfo(sessionId);
      return session;
    },
    {
      enabled: !!sessionId,
      ...queryConfig.session,
      onSuccess: () => {
        // Sync with examStore
        loadSession(sessionId);
      },
    },
  );
};

/**
 * Query: Get exam question
 */
export const useExamQuestion = (sessionId: string, questionIndex: number) => {
  return useQuery(
    queryKeys.exam.question(sessionId, questionIndex),
    async () => {
      const question = await examService.getQuestion(sessionId, questionIndex);
      return question;
    },
    {
      enabled: !!sessionId && questionIndex >= 0,
      ...queryConfig.session,
      staleTime: 0, // Always fresh - questions might change
    },
  );
};

/**
 * Query: Get exam performance
 */
export const useExamPerformance = (sessionId: string) => {
  const refreshPerformance = useExamStore((state) => state.refreshPerformance);

  return useQuery(
    queryKeys.exam.performance(sessionId),
    async () => {
      const performance = await examService.getPerformance(sessionId);
      return performance;
    },
    {
      enabled: !!sessionId,
      ...queryConfig.realtime, // Frequent updates
      onSuccess: () => {
        refreshPerformance();
      },
    },
  );
};

/**
 * Query: Get exam history
 */
export const useExamHistory = (userId?: string) => {
  return useQuery(
    queryKeys.exam.history(userId),
    async () => {
      // userId is for cache key, service uses token-based auth
      const history = await examService.getExamHistory();
      return history;
    },
    {
      ...queryConfig.moderate,
    },
  );
};

/**
 * Query: Get exam results
 */
export const useExamResults = (examId: string) => {
  return useQuery(
    queryKeys.exam.results(examId),
    async () => {
      // Service expects array of session IDs
      const results = await examService.getExamResults([examId]);
      return results[0]; // Return first result for single examId
    },
    {
      enabled: !!examId,
      ...queryConfig.static, // Results don't change
    },
  );
};

/**
 * Mutation: Create new exam
 */
export const useCreateExamMutation = () => {
  const createExam = useExamStore((state) => state.createExam);
  const queryClient = useQueryClient();

  return useMutation(
    async (request: CreateExamRequest) => {
      const session = await createExam(request);
      return session;
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries(queryKeys.exam.all);
      },
    },
  );
};

/**
 * Mutation: Start exam
 */
export const useStartExamMutation = (sessionId: string) => {
  const startExam = useExamStore((state) => state.startExam);
  const queryClient = useQueryClient();

  return useMutation(
    async () => {
      await startExam();
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries(queryKeys.exam.session(sessionId));
      },
    },
  );
};

/**
 * Mutation: Save answer
 */
export const useSaveAnswerMutation = (sessionId: string) => {
  const saveAnswer = useExamStore((state) => state.saveAnswer);
  const queryClient = useQueryClient();

  return useMutation(
    async ({
      questionId,
      selectedAnswer,
      responseTime,
    }: {
      questionId: string
      selectedAnswer: string
      responseTime?: number
    }) => {
      await saveAnswer(questionId, selectedAnswer, responseTime);
    },
    {
      onSuccess: () => {
        // Invalidate performance to get updated stats
        queryClient.invalidateQueries(queryKeys.exam.performance(sessionId));
      },
    },
  );
};

/**
 * Mutation: Submit exam
 */
export const useSubmitExamMutation = (sessionId: string) => {
  const submitExam = useExamStore((state) => state.submitExam);
  const queryClient = useQueryClient();

  return useMutation(
    async () => {
      await submitExam();
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries(queryKeys.exam.session(sessionId));
        queryClient.invalidateQueries(queryKeys.exam.history());
      },
    },
  );
};

/**
 * Mutation: Flag question
 */
export const useFlagQuestionMutation = (_sessionId: string) => {
  const toggleFlag = useExamStore((state) => state.toggleFlag);

  return useMutation(
    async (questionId: string) => {
      await toggleFlag(questionId);
    },
  );
};
