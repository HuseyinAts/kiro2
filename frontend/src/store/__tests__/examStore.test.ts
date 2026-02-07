/**
 * examStore Tests
 *
 * Comprehensive tests for the Zustand exam session store.
 * Covers session lifecycle, question navigation, answer management,
 * flagging, timer, connection state, and reset behavior.
 */

import { describe, it, expect, beforeEach, vi, type Mock } from 'vitest'
import { act } from '@testing-library/react'
import { useExamStore } from '../examStore'
import {
  examService,
  ExamStatus,
  type ExamSessionResponse,
  type QuestionResponse,
  type PerformanceResponse,
} from '../../services/examService'

// Mock examService
vi.mock('../../services/examService', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../../services/examService')>()
  return {
    ...actual,
    examService: {
      createExam: vi.fn(),
      getSessionInfo: vi.fn(),
      getPerformance: vi.fn(),
      getQuestion: vi.fn(),
      startExam: vi.fn(),
      pauseExam: vi.fn(),
      submitExam: vi.fn(),
      abandonExam: vi.fn(),
      navigateToQuestion: vi.fn(),
      saveAnswer: vi.fn(),
      flagQuestion: vi.fn(),
    },
  }
})

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {}
  return {
    getItem: vi.fn((key: string) => store[key] ?? null),
    setItem: vi.fn((key: string, value: string) => { store[key] = value }),
    removeItem: vi.fn((key: string) => { delete store[key] }),
    clear: vi.fn(() => { store = {} }),
  }
})()
Object.defineProperty(globalThis, 'localStorage', { value: localStorageMock })

function createMockSession(overrides: Partial<ExamSessionResponse> = {}): ExamSessionResponse {
  return {
    session_id: 'session-1',
    student_id: 'student-1',
    exam_type: 'TYT',
    status: ExamStatus.NOT_STARTED,
    total_questions: 40,
    duration_minutes: 135,
    current_question_index: 0,
    ...overrides,
  }
}

function createMockQuestion(overrides: Partial<QuestionResponse> = {}): QuestionResponse {
  return {
    id: 'q-1',
    question_text: '2 + 2 = ?',
    option_a: '3',
    option_b: '4',
    option_c: '5',
    option_d: '6',
    subject_area: 'Matematik',
    topic: 'Aritmetik',
    konu: 'Matematik',
    difficulty: 'EASY',
    zorluk_seviyesi: 'KOLAY',
    question_order: 0,
    ...overrides,
  }
}

function createMockPerformance(overrides: Partial<PerformanceResponse> = {}): PerformanceResponse {
  return {
    total_questions: 40,
    answered_questions: 10,
    correct_answers: 7,
    wrong_answers: 3,
    empty_answers: 30,
    net_score: 6.25,
    net_sayisi: 6.25,
    raw_score: 7,
    estimated_ability: 0.5,
    confidence_level: 0.8,
    konu_performanslari: [],
    calisma_onerileri: [],
    ...overrides,
  }
}

describe('examStore', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorageMock.clear()
    // Reset to initial state
    act(() => {
      useExamStore.getState().resetExam()
    })
  })

  describe('Initial State', () => {
    it('should have no active session', () => {
      expect(useExamStore.getState().session).toBeNull()
    })

    it('should have empty answers', () => {
      expect(useExamStore.getState().answers).toEqual({})
    })

    it('should have empty flagged questions set', () => {
      expect(useExamStore.getState().flaggedQuestions).toBeInstanceOf(Set)
      expect(useExamStore.getState().flaggedQuestions.size).toBe(0)
    })

    it('should have currentQuestionIndex at 0', () => {
      expect(useExamStore.getState().currentQuestionIndex).toBe(0)
    })

    it('should have remainingTime at 0', () => {
      expect(useExamStore.getState().remainingTime).toBe(0)
    })

    it('should not be loading', () => {
      expect(useExamStore.getState().loading).toBe(false)
    })

    it('should have no error', () => {
      expect(useExamStore.getState().error).toBeNull()
    })

    it('should not be connected', () => {
      expect(useExamStore.getState().isConnected).toBe(false)
    })
  })

  describe('Create Exam', () => {
    it('should set session and calculate remaining time', async () => {
      const mockSession = createMockSession({ duration_minutes: 135 })
      ;(examService.createExam as Mock).mockResolvedValue(mockSession)

      let result: ExamSessionResponse | null
      await act(async () => {
        result = await useExamStore.getState().createExam({ exam_type: 'TYT' as any })
      })

      const state = useExamStore.getState()
      expect(result!).toEqual(mockSession)
      expect(state.session).toEqual(mockSession)
      expect(state.remainingTime).toBe(135 * 60)
      expect(state.loading).toBe(false)
    })

    it('should return null and set error on failure', async () => {
      ;(examService.createExam as Mock).mockRejectedValue(new Error('Server error'))

      let result: ExamSessionResponse | null
      await act(async () => {
        result = await useExamStore.getState().createExam({ exam_type: 'TYT' as any })
      })

      expect(result!).toBeNull()
      expect(useExamStore.getState().error).toBeTruthy()
      expect(useExamStore.getState().loading).toBe(false)
    })
  })

  describe('Start Exam', () => {
    it('should update session and set startTime', async () => {
      const session = createMockSession()
      const startedSession = { ...session, status: ExamStatus.IN_PROGRESS }
      useExamStore.setState({ session })
      ;(examService.startExam as Mock).mockResolvedValue(startedSession)

      await act(async () => {
        await useExamStore.getState().startExam()
      })

      const state = useExamStore.getState()
      expect(state.session?.status).toBe(ExamStatus.IN_PROGRESS)
      expect(state.startTime).toBeGreaterThan(0)
      expect(state.loading).toBe(false)
    })

    it('should do nothing when no session exists', async () => {
      await act(async () => {
        await useExamStore.getState().startExam()
      })

      expect(examService.startExam).not.toHaveBeenCalled()
    })

    it('should set error on failure', async () => {
      useExamStore.setState({ session: createMockSession() })
      ;(examService.startExam as Mock).mockRejectedValue(new Error('Failed'))

      await act(async () => {
        await useExamStore.getState().startExam()
      })

      expect(useExamStore.getState().error).toBeTruthy()
    })
  })

  describe('Answer Question', () => {
    it('should store answer correctly', async () => {
      useExamStore.setState({ session: createMockSession() })
      ;(examService.saveAnswer as Mock).mockResolvedValue({})
      ;(examService.getPerformance as Mock).mockResolvedValue(createMockPerformance())

      await act(async () => {
        await useExamStore.getState().saveAnswer('q-1', 'B', 15)
      })

      expect(useExamStore.getState().answers['q-1']).toBe('B')
      expect(useExamStore.getState().saveStatus).toBe('saved')
      expect(examService.saveAnswer).toHaveBeenCalledWith('session-1', {
        question_id: 'q-1',
        selected_answer: 'B',
        response_time: 15,
      })
    })

    it('should set saveStatus to error on failure', async () => {
      useExamStore.setState({ session: createMockSession() })
      ;(examService.saveAnswer as Mock).mockRejectedValue(new Error('Save failed'))

      await act(async () => {
        await useExamStore.getState().saveAnswer('q-1', 'A')
      })

      expect(useExamStore.getState().saveStatus).toBe('error')
    })

    it('should do nothing without a session', async () => {
      await act(async () => {
        await useExamStore.getState().saveAnswer('q-1', 'A')
      })

      expect(examService.saveAnswer).not.toHaveBeenCalled()
    })
  })

  describe('Flag Question', () => {
    it('should add question to flagged set', async () => {
      useExamStore.setState({ session: createMockSession() })
      ;(examService.flagQuestion as Mock).mockResolvedValue({})

      await act(async () => {
        await useExamStore.getState().toggleFlag('q-5')
      })

      expect(useExamStore.getState().flaggedQuestions.has('q-5')).toBe(true)
      expect(examService.flagQuestion).toHaveBeenCalledWith('session-1', {
        question_id: 'q-5',
        flagged: true,
      })
    })

    it('should remove question from flagged set on second toggle', async () => {
      useExamStore.setState({
        session: createMockSession(),
        flaggedQuestions: new Set(['q-5']),
      })
      ;(examService.flagQuestion as Mock).mockResolvedValue({})

      await act(async () => {
        await useExamStore.getState().toggleFlag('q-5')
      })

      expect(useExamStore.getState().flaggedQuestions.has('q-5')).toBe(false)
      expect(examService.flagQuestion).toHaveBeenCalledWith('session-1', {
        question_id: 'q-5',
        flagged: false,
      })
    })
  })

  describe('Navigate Questions', () => {
    beforeEach(() => {
      useExamStore.setState({
        session: createMockSession({ total_questions: 10 }),
        currentQuestionIndex: 3,
      })
      ;(examService.navigateToQuestion as Mock).mockResolvedValue({})
      ;(examService.getQuestion as Mock).mockResolvedValue(createMockQuestion())
    })

    it('navigateNext should increment index', async () => {
      await act(async () => {
        await useExamStore.getState().navigateNext()
      })

      expect(useExamStore.getState().currentQuestionIndex).toBe(4)
    })

    it('navigatePrevious should decrement index', async () => {
      await act(async () => {
        await useExamStore.getState().navigatePrevious()
      })

      expect(useExamStore.getState().currentQuestionIndex).toBe(2)
    })

    it('navigateNext should not exceed total_questions - 1', async () => {
      useExamStore.setState({ currentQuestionIndex: 9 })

      await act(async () => {
        await useExamStore.getState().navigateNext()
      })

      // Should not have called navigateToQuestion since we're at the last question
      expect(examService.navigateToQuestion).not.toHaveBeenCalled()
    })

    it('navigatePrevious should not go below 0', async () => {
      useExamStore.setState({ currentQuestionIndex: 0 })

      await act(async () => {
        await useExamStore.getState().navigatePrevious()
      })

      expect(examService.navigateToQuestion).not.toHaveBeenCalled()
    })

    it('navigateToQuestion should jump to specific index', async () => {
      await act(async () => {
        await useExamStore.getState().navigateToQuestion(7)
      })

      expect(examService.navigateToQuestion).toHaveBeenCalledWith('session-1', {
        question_index: 7,
      })
      expect(useExamStore.getState().currentQuestionIndex).toBe(7)
    })
  })

  describe('Timer', () => {
    it('setRemainingTime should set the time', () => {
      act(() => {
        useExamStore.getState().setRemainingTime(3600)
      })

      expect(useExamStore.getState().remainingTime).toBe(3600)
    })

    it('decrementTime should decrease by 1 second', () => {
      useExamStore.setState({ remainingTime: 100 })

      act(() => {
        useExamStore.getState().decrementTime()
      })

      expect(useExamStore.getState().remainingTime).toBe(99)
    })

    it('decrementTime should not go below 0', () => {
      useExamStore.setState({ remainingTime: 0 })

      act(() => {
        useExamStore.getState().decrementTime()
      })

      expect(useExamStore.getState().remainingTime).toBe(0)
    })

    it('decrementTime from 1 should reach 0', () => {
      useExamStore.setState({ remainingTime: 1 })

      act(() => {
        useExamStore.getState().decrementTime()
      })

      expect(useExamStore.getState().remainingTime).toBe(0)
    })
  })

  describe('Submit Exam', () => {
    it('should set status to COMPLETED on success', async () => {
      const session = createMockSession({ status: ExamStatus.IN_PROGRESS })
      useExamStore.setState({ session })
      ;(examService.submitExam as Mock).mockResolvedValue({})

      await act(async () => {
        await useExamStore.getState().submitExam()
      })

      expect(useExamStore.getState().session?.status).toBe(ExamStatus.COMPLETED)
      expect(useExamStore.getState().loading).toBe(false)
    })

    it('should set error on submit failure', async () => {
      useExamStore.setState({ session: createMockSession() })
      ;(examService.submitExam as Mock).mockRejectedValue(new Error('Submit failed'))

      await act(async () => {
        await useExamStore.getState().submitExam()
      })

      expect(useExamStore.getState().error).toBeTruthy()
      expect(useExamStore.getState().loading).toBe(false)
    })

    it('should do nothing without session', async () => {
      await act(async () => {
        await useExamStore.getState().submitExam()
      })

      expect(examService.submitExam).not.toHaveBeenCalled()
    })
  })

  describe('Abandon Exam', () => {
    it('should set status to ABANDONED', async () => {
      useExamStore.setState({ session: createMockSession() })
      ;(examService.abandonExam as Mock).mockResolvedValue({})

      await act(async () => {
        await useExamStore.getState().abandonExam()
      })

      expect(useExamStore.getState().session?.status).toBe(ExamStatus.ABANDONED)
    })
  })

  describe('Reset State', () => {
    it('should restore all fields to initial values', () => {
      useExamStore.setState({
        session: createMockSession(),
        currentQuestionIndex: 15,
        answers: { 'q-1': 'A', 'q-2': 'B' },
        flaggedQuestions: new Set(['q-1']),
        remainingTime: 5000,
        startTime: Date.now(),
        loading: true,
        error: 'some error',
        saveStatus: 'saving',
        isConnected: true,
      })

      act(() => {
        useExamStore.getState().resetExam()
      })

      const state = useExamStore.getState()
      expect(state.session).toBeNull()
      expect(state.currentQuestionIndex).toBe(0)
      expect(state.answers).toEqual({})
      expect(state.flaggedQuestions.size).toBe(0)
      expect(state.remainingTime).toBe(0)
      expect(state.startTime).toBeNull()
      expect(state.loading).toBe(false)
      expect(state.error).toBeNull()
      expect(state.isConnected).toBe(false)
    })
  })

  describe('Connection State', () => {
    it('setConnected should update isConnected', () => {
      act(() => {
        useExamStore.getState().setConnected(true)
      })
      expect(useExamStore.getState().isConnected).toBe(true)

      act(() => {
        useExamStore.getState().setConnected(false)
      })
      expect(useExamStore.getState().isConnected).toBe(false)
    })

    it('updateLastSync should set lastSyncTime', () => {
      const before = Date.now()

      act(() => {
        useExamStore.getState().updateLastSync()
      })

      const { lastSyncTime } = useExamStore.getState()
      expect(lastSyncTime).toBeGreaterThanOrEqual(before)
      expect(lastSyncTime).toBeLessThanOrEqual(Date.now())
    })
  })

  describe('Save Status', () => {
    it('setSaveStatus should update saveStatus and saveMessage', () => {
      act(() => {
        useExamStore.getState().setSaveStatus('saving', 'Kaydediliyor...')
      })

      expect(useExamStore.getState().saveStatus).toBe('saving')
      expect(useExamStore.getState().saveMessage).toBe('Kaydediliyor...')
    })

    it('setSaveStatus with null should clear status', () => {
      act(() => {
        useExamStore.getState().setSaveStatus(null)
      })

      expect(useExamStore.getState().saveStatus).toBeNull()
      expect(useExamStore.getState().saveMessage).toBe('')
    })
  })

  describe('Load Session', () => {
    it('should load session, performance, and current question', async () => {
      const session = createMockSession({ current_question_index: 5 })
      const perf = createMockPerformance()
      const question = createMockQuestion({ id: 'q-5' })

      ;(examService.getSessionInfo as Mock).mockResolvedValue(session)
      ;(examService.getPerformance as Mock).mockResolvedValue(perf)
      ;(examService.getQuestion as Mock).mockResolvedValue(question)

      await act(async () => {
        await useExamStore.getState().loadSession('session-1')
      })

      const state = useExamStore.getState()
      expect(state.session).toEqual(session)
      expect(state.performance).toEqual(perf)
      expect(state.currentQuestion).toEqual(question)
      expect(state.currentQuestionIndex).toBe(5)
      expect(state.loading).toBe(false)
    })

    it('should calculate remaining time for in-progress session', async () => {
      const fiveMinutesAgo = new Date(Date.now() - 5 * 60 * 1000).toISOString()
      const session = createMockSession({
        status: ExamStatus.IN_PROGRESS,
        started_at: fiveMinutesAgo,
        duration_minutes: 135,
      })

      ;(examService.getSessionInfo as Mock).mockResolvedValue(session)
      ;(examService.getPerformance as Mock).mockResolvedValue(createMockPerformance())
      ;(examService.getQuestion as Mock).mockResolvedValue(createMockQuestion())

      await act(async () => {
        await useExamStore.getState().loadSession('session-1')
      })

      const { remainingTime } = useExamStore.getState()
      // Should be approximately (135*60 - 5*60) = 7800 seconds, with some tolerance
      expect(remainingTime).toBeGreaterThan(7700)
      expect(remainingTime).toBeLessThanOrEqual(7800)
    })

    it('should set error on load failure', async () => {
      ;(examService.getSessionInfo as Mock).mockRejectedValue(new Error('Not found'))

      await act(async () => {
        await useExamStore.getState().loadSession('bad-id')
      })

      expect(useExamStore.getState().error).toBeTruthy()
      expect(useExamStore.getState().loading).toBe(false)
    })
  })

  describe('State Setters', () => {
    it('setError should update error', () => {
      act(() => { useExamStore.getState().setError('Test error') })
      expect(useExamStore.getState().error).toBe('Test error')

      act(() => { useExamStore.getState().setError(null) })
      expect(useExamStore.getState().error).toBeNull()
    })

    it('setLoading should update loading', () => {
      act(() => { useExamStore.getState().setLoading(true) })
      expect(useExamStore.getState().loading).toBe(true)
    })
  })

  describe('Refresh Performance', () => {
    it('should update performance data', async () => {
      const perf = createMockPerformance({ correct_answers: 20 })
      useExamStore.setState({ session: createMockSession() })
      ;(examService.getPerformance as Mock).mockResolvedValue(perf)

      await act(async () => {
        await useExamStore.getState().refreshPerformance()
      })

      expect(useExamStore.getState().performance?.correct_answers).toBe(20)
    })

    it('should do nothing without session', async () => {
      await act(async () => {
        await useExamStore.getState().refreshPerformance()
      })

      expect(examService.getPerformance).not.toHaveBeenCalled()
    })
  })
})
