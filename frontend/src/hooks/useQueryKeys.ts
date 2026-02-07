/**
 * React Query Key Factory
 *
 * Centralized query key management for React Query
 * Provides consistent naming and type-safe query keys
 *
 * @see https://tkdodo.eu/blog/effective-react-query-keys
 */

export const queryKeys = {
  // Auth queries
  auth: {
    all: ['auth'] as const,
    user: () => [...queryKeys.auth.all, 'user'] as const,
    profile: (userId: string) => [...queryKeys.auth.all, 'profile', userId] as const,
    permissions: () => [...queryKeys.auth.all, 'permissions'] as const,
  },

  // Exam queries
  exam: {
    all: ['exam'] as const,
    list: (filters?: any) => [...queryKeys.exam.all, 'list', filters] as const,
    detail: (id: string) => [...queryKeys.exam.all, 'detail', id] as const,
    session: (sessionId: string) => [...queryKeys.exam.all, 'session', sessionId] as const,
    question: (sessionId: string, index: number) =>
      [...queryKeys.exam.session(sessionId), 'question', index] as const,
    performance: (sessionId: string) =>
      [...queryKeys.exam.session(sessionId), 'performance'] as const,
    history: (userId?: string) => [...queryKeys.exam.all, 'history', userId] as const,
    results: (examId: string) => [...queryKeys.exam.all, 'results', examId] as const,
  },

  // Dashboard queries
  dashboard: {
    all: ['dashboard'] as const,
    stats: (userId: string) => [...queryKeys.dashboard.all, 'stats', userId] as const,
    recent: (userId: string) => [...queryKeys.dashboard.all, 'recent', userId] as const,
    notifications: (userId: string) => [...queryKeys.dashboard.all, 'notifications', userId] as const,
  },

  // Learning path queries
  learningPath: {
    all: ['learningPath'] as const,
    list: () => [...queryKeys.learningPath.all, 'list'] as const,
    detail: (id: string) => [...queryKeys.learningPath.all, 'detail', id] as const,
    progress: (pathId: string, userId: string) =>
      [...queryKeys.learningPath.all, 'progress', pathId, userId] as const,
  },

  // Study room queries
  studyRoom: {
    all: ['studyRoom'] as const,
    list: (filters?: any) => [...queryKeys.studyRoom.all, 'list', filters] as const,
    detail: (id: string) => [...queryKeys.studyRoom.all, 'detail', id] as const,
    messages: (roomId: string) => [...queryKeys.studyRoom.all, 'messages', roomId] as const,
    participants: (roomId: string) => [...queryKeys.studyRoom.all, 'participants', roomId] as const,
  },

  // Chat/Agent queries
  chat: {
    all: ['chat'] as const,
    agents: () => [...queryKeys.chat.all, 'agents'] as const,
    history: (sessionId?: string) => [...queryKeys.chat.all, 'history', sessionId] as const,
    conversation: (conversationId: string) =>
      [...queryKeys.chat.all, 'conversation', conversationId] as const,
  },

  // Content queries
  content: {
    all: ['content'] as const,
    subjects: () => [...queryKeys.content.all, 'subjects'] as const,
    topics: (subjectId: string) => [...queryKeys.content.all, 'topics', subjectId] as const,
    materials: (topicId: string) => [...queryKeys.content.all, 'materials', topicId] as const,
  },

  // Gamification queries
  gamification: {
    all: ['gamification'] as const,
    achievements: (userId: string) => [...queryKeys.gamification.all, 'achievements', userId] as const,
    leaderboard: (type: string) => [...queryKeys.gamification.all, 'leaderboard', type] as const,
    stats: (userId: string) => [...queryKeys.gamification.all, 'stats', userId] as const,
    badges: () => [...queryKeys.gamification.all, 'badges'] as const,
  },

  // Goals queries
  goals: {
    all: ['goals'] as const,
    list: (userId: string) => [...queryKeys.goals.all, 'list', userId] as const,
    detail: (goalId: string) => [...queryKeys.goals.all, 'detail', goalId] as const,
    progress: (goalId: string) => [...queryKeys.goals.all, 'progress', goalId] as const,
  },

  // Admin queries
  admin: {
    all: ['admin'] as const,
    users: (filters?: any) => [...queryKeys.admin.all, 'users', filters] as const,
    stats: () => [...queryKeys.admin.all, 'stats'] as const,
    reports: (type: string, filters?: any) =>
      [...queryKeys.admin.all, 'reports', type, filters] as const,
  },
} as const;

/**
 * Type-safe query key getter
 * Ensures all query keys follow the factory pattern
 */
export type QueryKeys = typeof queryKeys

/**
 * Helper to get all queries for invalidation
 */
export const getAllQueriesForInvalidation = (category: keyof typeof queryKeys) => {
  return queryKeys[category].all;
};

export default queryKeys;
