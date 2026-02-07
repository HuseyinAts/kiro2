/**
 * Exam Store (Zustand)
 *
 * Centralized exam session state management
 * Handles TYT/AYT/YDT exam sessions, questions, answers, and performance tracking
 *
 * Features:
 * - Exam session management (start, pause, resume, submit)
 * - Question navigation and answering
 * - Flagged questions tracking
 * - Real-time performance calculations
 * - Auto-save functionality support
 * - Timer management
 * - WebSocket connection state
 */

import { create } from 'zustand';
import { devtools, persist, createJSONStorage, StateStorage } from 'zustand/middleware';

import {
  examService,
  ExamStatus,
  ExamSessionResponse,
  QuestionResponse,
  PerformanceResponse,
  CreateExamRequest,
  SaveAnswerRequest,
} from '../services/examService';
import { getErrorMessage } from '../types';

/**
 * Custom storage handler for Set<string> serialization
 *
 * Problem: JSON.stringify cannot serialize Set objects
 * Solution: Convert Set to Array for storage, Array to Set on rehydration
 */
const customStorage: StateStorage = {
  getItem: (name: string): string | null => {
    const str = localStorage.getItem(name);
    if (!str) {return null;}

    try {
      const parsed = JSON.parse(str);
      // Convert flaggedQuestions array back to Set
      if (parsed.state?.flaggedQuestions) {
        parsed.state.flaggedQuestions = new Set(parsed.state.flaggedQuestions);
      }
      return JSON.stringify(parsed);
    } catch {
      return str;
    }
  },
  setItem: (name: string, value: string): void => {
    try {
      const parsed = JSON.parse(value);
      // Convert flaggedQuestions Set to Array for storage
      if (parsed.state?.flaggedQuestions instanceof Set) {
        parsed.state.flaggedQuestions = Array.from(parsed.state.flaggedQuestions);
      }
      localStorage.setItem(name, JSON.stringify(parsed));
    } catch {
      localStorage.setItem(name, value);
    }
  },
  removeItem: (name: string): void => {
    localStorage.removeItem(name);
  },
};

interface ExamState {
  // Session data
  session: ExamSessionResponse | null
  currentQuestion: QuestionResponse | null
  performance: PerformanceResponse | null

  // Exam progress
  currentQuestionIndex: number
  answers: Record<string, string> // question_id -> selected_answer
  flaggedQuestions: Set<string> // question_ids

  // Timing
  remainingTime: number // seconds
  startTime: number | null

  // UI state
  loading: boolean
  error: string | null
  saveStatus: 'saved' | 'saving' | 'error' | null
  saveMessage: string

  // WebSocket connection
  isConnected: boolean
  lastSyncTime: number | null
}

interface ExamActions {
  // Session management
  createExam: (request: CreateExamRequest) => Promise<ExamSessionResponse | null>
  loadSession: (sessionId: string) => Promise<void>
  startExam: () => Promise<void>
  pauseExam: () => Promise<void>
  resumeExam: () => Promise<void>
  submitExam: () => Promise<void>
  abandonExam: () => Promise<void>

  // Question management
  loadQuestion: (index: number) => Promise<void>
  navigateToQuestion: (index: number) => Promise<void>
  navigateNext: () => Promise<void>
  navigatePrevious: () => Promise<void>

  // Answer management
  saveAnswer: (questionId: string, selectedAnswer: string, responseTime?: number) => Promise<void>
  clearAnswer: (questionId: string) => Promise<void>

  // Flagged questions
  toggleFlag: (questionId: string) => Promise<void>
  setFlagged: (questionId: string, flagged: boolean) => Promise<void>

  // Performance
  refreshPerformance: () => Promise<void>

  // Timer
  setRemainingTime: (seconds: number) => void
  decrementTime: () => void

  // Connection
  setConnected: (connected: boolean) => void
  updateLastSync: () => void

  // State management
  setSaveStatus: (status: 'saved' | 'saving' | 'error' | null, message?: string) => void
  setError: (error: string | null) => void
  setLoading: (loading: boolean) => void

  // Reset
  resetExam: () => void
}

type ExamStore = ExamState & ExamActions

const initialState: ExamState = {
  session: null,
  currentQuestion: null,
  performance: null,
  currentQuestionIndex: 0,
  answers: {},
  flaggedQuestions: new Set(),
  remainingTime: 0,
  startTime: null,
  loading: false,
  error: null,
  saveStatus: null,
  saveMessage: '',
  isConnected: false,
  lastSyncTime: null,
};

export const useExamStore = create<ExamStore>()(
  devtools(
    persist(
      (set, get) => ({
        ...initialState,

        // Create new exam session
      createExam: async (request: CreateExamRequest) => {
        try {
          set({ loading: true, error: null });

          const session = await examService.createExam(request);

          set({
            session,
            remainingTime: session.duration_minutes * 60,
            loading: false,
          });

          return session;
        } catch (error: unknown) {
          set({
            error: getErrorMessage(error) || 'Sınav oluşturulamadı',
            loading: false,
          });
          return null;
        }
      },

      // Load existing session
      loadSession: async (sessionId: string) => {
        try {
          set({ loading: true, error: null });

          const session = await examService.getSessionInfo(sessionId);
          const performance = await examService.getPerformance(sessionId);

          // Load current question
          const currentQuestion = await examService.getQuestion(
            sessionId,
            session.current_question_index,
          );

          // Calculate remaining time if session is active
          let remainingTime = session.duration_minutes * 60;
          if (session.started_at && session.status === ExamStatus.IN_PROGRESS) {
            const startTime = new Date(session.started_at).getTime();
            const elapsed = (Date.now() - startTime) / 1000;
            remainingTime = Math.max(0, remainingTime - elapsed);
          }

          set({
            session,
            currentQuestion,
            performance,
            currentQuestionIndex: session.current_question_index,
            remainingTime,
            loading: false,
          });
        } catch (error: unknown) {
          set({
            error: getErrorMessage(error) || 'Sınav yüklenemedi',
            loading: false,
          });
        }
      },

      // Start exam
      startExam: async () => {
        const { session } = get();
        if (!session) {return;}

        try {
          set({ loading: true });

          const updatedSession = await examService.startExam(session.session_id);

          set({
            session: updatedSession,
            startTime: Date.now(),
            loading: false,
          });
        } catch (error: unknown) {
          set({
            error: getErrorMessage(error) || 'Sınav başlatılamadı',
            loading: false,
          });
        }
      },

      // Pause exam
      pauseExam: async () => {
        const { session } = get();
        if (!session) {return;}

        try {
          await examService.pauseExam(session.session_id);
          set({ session: { ...session, status: ExamStatus.NOT_STARTED } });
        } catch (error: unknown) {
          set({ error: getErrorMessage(error) || 'Sınav durdurulamadı' });
        }
      },

      // Resume exam
      resumeExam: async () => {
        const { session } = get();
        if (!session) {return;}

        try {
          const updatedSession = await examService.startExam(session.session_id);
          set({ session: updatedSession });
        } catch (error: unknown) {
          set({ error: getErrorMessage(error) || 'Sınav devam ettirilemedi' });
        }
      },

      // Submit exam
      submitExam: async () => {
        const { session } = get();
        if (!session) {return;}

        try {
          set({ loading: true });

          await examService.submitExam(session.session_id);

          set({
            session: { ...session, status: ExamStatus.COMPLETED },
            loading: false,
          });
        } catch (error: unknown) {
          set({
            error: getErrorMessage(error) || 'Sınav gönderilemedi',
            loading: false,
          });
        }
      },

      // Abandon exam
      abandonExam: async () => {
        const { session } = get();
        if (!session) {return;}

        try {
          await examService.abandonExam(session.session_id);
          set({ session: { ...session, status: ExamStatus.ABANDONED } });
        } catch (error: unknown) {
          set({ error: getErrorMessage(error) || 'Sınav terk edilemedi' });
        }
      },

      // Load specific question
      loadQuestion: async (index: number) => {
        const { session } = get();
        if (!session) {return;}

        try {
          set({ loading: true });

          const question = await examService.getQuestion(session.session_id, index);

          set({
            currentQuestion: question,
            currentQuestionIndex: index,
            loading: false,
          });
        } catch (error: unknown) {
          set({
            error: getErrorMessage(error) || 'Soru yüklenemedi',
            loading: false,
          });
        }
      },

      // Navigate to question
      navigateToQuestion: async (index: number) => {
        const { session } = get();
        if (!session) {return;}

        try {
          await examService.navigateToQuestion(session.session_id, { question_index: index });
          await get().loadQuestion(index);
        } catch (error: unknown) {
          set({ error: getErrorMessage(error) || 'Soruya gidilemedi' });
        }
      },

      // Navigate to next question
      navigateNext: async () => {
        const { currentQuestionIndex, session } = get();
        if (!session) {return;}

        const nextIndex = Math.min(currentQuestionIndex + 1, session.total_questions - 1);
        if (nextIndex !== currentQuestionIndex) {
          await get().navigateToQuestion(nextIndex);
        }
      },

      // Navigate to previous question
      navigatePrevious: async () => {
        const { currentQuestionIndex } = get();
        const prevIndex = Math.max(currentQuestionIndex - 1, 0);

        if (prevIndex !== currentQuestionIndex) {
          await get().navigateToQuestion(prevIndex);
        }
      },

      // Save answer
      saveAnswer: async (questionId: string, selectedAnswer: string, responseTime?: number) => {
        const { session, answers } = get();
        if (!session) {return;}

        try {
          set({ saveStatus: 'saving' });

          const request: SaveAnswerRequest = {
            question_id: questionId,
            selected_answer: selectedAnswer,
            response_time: responseTime,
          };

          await examService.saveAnswer(session.session_id, request);

          set({
            answers: { ...answers, [questionId]: selectedAnswer },
            saveStatus: 'saved',
            saveMessage: 'Cevap kaydedildi',
          });

          // Refresh performance after saving
          await get().refreshPerformance();

          // Clear save status after 2 seconds
          setTimeout(() => set({ saveStatus: null }), 2000);
        } catch (error: unknown) {
          set({
            saveStatus: 'error',
            saveMessage: getErrorMessage(error) || 'Cevap kaydedilemedi',
          });

          setTimeout(() => set({ saveStatus: null }), 5000);
        }
      },

      // Clear answer
      clearAnswer: async (questionId: string) => {
        await get().saveAnswer(questionId, '', 0);
      },

      // Toggle flag
      toggleFlag: async (questionId: string) => {
        const { flaggedQuestions } = get();
        const newSet = new Set(flaggedQuestions);

        if (newSet.has(questionId)) {
          newSet.delete(questionId);
          await get().setFlagged(questionId, false);
        } else {
          newSet.add(questionId);
          await get().setFlagged(questionId, true);
        }

        set({ flaggedQuestions: newSet });
      },

      // Set flagged status
      setFlagged: async (questionId: string, flagged: boolean) => {
        const { session } = get();
        if (!session) {return;}

        try {
          await examService.flagQuestion(session.session_id, { question_id: questionId, flagged });
        } catch (error: unknown) {
          console.error('Flag update failed:', error);
        }
      },

      // Refresh performance
      refreshPerformance: async () => {
        const { session } = get();
        if (!session) {return;}

        try {
          const performance = await examService.getPerformance(session.session_id);
          set({ performance });
        } catch (error: unknown) {
          console.error('Performance refresh failed:', error);
        }
      },

      // Timer management
      setRemainingTime: (seconds: number) => {
        set({ remainingTime: seconds });
      },

      decrementTime: () => {
        const { remainingTime } = get();
        if (remainingTime > 0) {
          set({ remainingTime: remainingTime - 1 });
        }
      },

      // Connection management
      setConnected: (connected: boolean) => {
        set({ isConnected: connected });
      },

      updateLastSync: () => {
        set({ lastSyncTime: Date.now() });
      },

      // State setters
      setSaveStatus: (status: 'saved' | 'saving' | 'error' | null, message = '') => {
        set({ saveStatus: status, saveMessage: message });
      },

      setError: (error: string | null) => {
        set({ error });
      },

      setLoading: (loading: boolean) => {
        set({ loading });
      },

      // Reset exam state
      resetExam: () => {
        set(initialState);
      },
      }),
      {
        name: 'exam-storage',
        storage: createJSONStorage(() => customStorage),
        // Only persist essential exam progress data
        partialize: (state) => ({
          session: state.session,
          currentQuestionIndex: state.currentQuestionIndex,
          answers: state.answers,
          flaggedQuestions: state.flaggedQuestions,
          remainingTime: state.remainingTime,
        }),
        // Convert flaggedQuestions back to Set after rehydration
        onRehydrateStorage: () => (state) => {
          if (state && !(state.flaggedQuestions instanceof Set)) {
            state.flaggedQuestions = new Set(state.flaggedQuestions as unknown as string[]);
          }
        },
      },
    ),
    { name: 'ExamStore' },
  ),
);

/**
 * Selector hooks for better performance
 */
export const useExamSession = () => useExamStore((state) => state.session);
export const useCurrentQuestion = () => useExamStore((state) => state.currentQuestion);
export const useExamPerformance = () => useExamStore((state) => state.performance);
export const useExamTimer = () => useExamStore((state) => state.remainingTime);
export const useExamLoading = () => useExamStore((state) => state.loading);
export const useExamAnswers = () => useExamStore((state) => state.answers);
export const useFlaggedQuestions = () => useExamStore((state) => state.flaggedQuestions);

export default useExamStore;
