/**
 * useLearningPath Hook Tests
 *
 * Rewritten 2026-06-12 for the cookie-auth architecture (apiRequest +
 * useAuthStore + createStudentProfile/createLearningPath). The previous
 * suite mocked the removed `learningPathService` and was obsolete.
 *
 * KIRO2 - YKS Hazirlik Platformu
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor, act } from '@testing-library/react'

// --- Mutable auth state ---
const mockAuthState = {
  user: { id: 'user-1', ad: 'Test' } as any,
  isAuthenticated: true,
}

vi.mock('../../store/authStore', () => ({
  useAuthStore: vi.fn((selector: (state: any) => any) => selector(mockAuthState)),
}))

const mockCreateStudentProfile = vi.fn()
const mockCreateLearningPath = vi.fn()
const mockDetectLearningStyle = vi.fn()
const mockSubmitQuestionnaire = vi.fn()
vi.mock('../../api', () => ({
  createStudentProfile: (...a: any[]) => mockCreateStudentProfile(...a),
  createLearningPath: (...a: any[]) => mockCreateLearningPath(...a),
  detectLearningStyle: (...a: any[]) => mockDetectLearningStyle(...a),
  submitQuestionnaire: (...a: any[]) => mockSubmitQuestionnaire(...a),
}))

const mockApiRequest = vi.fn()
vi.mock('../../utils/apiHelpers', () => ({
  apiRequest: (...a: any[]) => mockApiRequest(...a),
}))

const mockConvert = vi.fn()
vi.mock('../../utils/learningPathHelpers', () => ({
  convertPathToNodes: (...a: any[]) => mockConvert(...a),
}))

import { useLearningPath } from '../useLearningPath'

const makeNodes = (statuses: Array<'completed' | 'current' | 'available'>) =>
  statuses.map((status, i) => ({
    id: `n${i + 1}`,
    title: `Node ${i + 1}`,
    status,
    progress: status === 'completed' ? 100 : status === 'current' ? 50 : 0,
  }))

describe('useLearningPath', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockAuthState.user = { id: 'user-1', ad: 'Test' }
    mockAuthState.isAuthenticated = true

    // /my-profile resolves (existing profile) + completion empty
    mockApiRequest.mockImplementation(async (url: string) => {
      if (url.includes('/my-profile')) return { student_id: 'sid-1' }
      if (url.includes('/completion/')) return { data: {} }
      if (url.includes('/streak')) return { daily_streak: 0, best_streak: 0, last_study_date: null }
      return {}
    })

    // Real VARK data exists → no onboarding, learningStyle set
    mockDetectLearningStyle.mockResolvedValue({
      success: true,
      data: {
        confidence: { score: 0.8 },
        data_points_used: 10,
        hybrid_code: 'V-ASVS',
        vark_profile: { dominant: 'V' },
      },
    })
    mockCreateLearningPath.mockResolvedValue({
      success: true,
      learning_path: { id: 'path-1', subject: 'matematik', nodes: [] },
    })
    mockConvert.mockReturnValue(makeNodes(['completed', 'current', 'available']))
  })

  describe('Initial State', () => {
    it('starts with loading true then resolves to false', async () => {
      const { result } = renderHook(() => useLearningPath())
      expect(result.current.loading).toBe(true)
      await waitFor(() => expect(result.current.loading).toBe(false))
    })

    it('starts with no error on success', async () => {
      const { result } = renderHook(() => useLearningPath())
      await waitFor(() => expect(result.current.loading).toBe(false))
      expect(result.current.error).toBeNull()
    })
  })

  describe('Loading Path Data', () => {
    it('loads path nodes on mount', async () => {
      const { result } = renderHook(() => useLearningPath())
      await waitFor(() => expect(result.current.loading).toBe(false))
      expect(result.current.pathNodes).toEqual(makeNodes(['completed', 'current', 'available']))
    })

    it('sets current node ID from the node with status "current"', async () => {
      const { result } = renderHook(() => useLearningPath())
      await waitFor(() => expect(result.current.loading).toBe(false))
      expect(result.current.currentNodeId).toBe('n2')
    })

    it('sets learning style from detection', async () => {
      const { result } = renderHook(() => useLearningPath())
      await waitFor(() => expect(result.current.loading).toBe(false))
      expect(result.current.learningStyle).toBe('V-ASVS')
    })

    it('fetches completion status from backend', async () => {
      renderHook(() => useLearningPath())
      await waitFor(() =>
        expect(mockApiRequest).toHaveBeenCalledWith(
          expect.stringContaining('/api/learning-path/completion/'),
        ),
      )
    })
  })

  describe('Onboarding', () => {
    it('requests onboarding when no real VARK data exists', async () => {
      // Low confidence / no data points → quiz needed
      mockDetectLearningStyle.mockResolvedValue({
        success: true,
        data: { confidence: { score: 0.3 }, data_points_used: 0 },
      })
      const { result } = renderHook(() => useLearningPath())
      await waitFor(() => expect(result.current.loading).toBe(false))
      expect(result.current.needsOnboarding).toBe(true)
      expect(result.current.pathNodes).toEqual([])
    })

    it('creates a profile when none exists yet', async () => {
      mockApiRequest.mockImplementation(async (url: string) => {
        if (url.includes('/my-profile')) throw new Error('404 not found')
        if (url.includes('/completion/')) return { data: {} }
        if (url.includes('/streak')) return { daily_streak: 0, best_streak: 0, last_study_date: null }
        return {}
      })
      mockCreateStudentProfile.mockResolvedValue({ student_id: 'sid-new' })
      const { result } = renderHook(() => useLearningPath())
      await waitFor(() => expect(result.current.loading).toBe(false))
      expect(mockCreateStudentProfile).toHaveBeenCalled()
    })
  })

  describe('Error Handling', () => {
    it('sets error when user is not authenticated', async () => {
      mockAuthState.user = null
      mockAuthState.isAuthenticated = false
      const { result } = renderHook(() => useLearningPath())
      await waitFor(() => expect(result.current.loading).toBe(false))
      expect(result.current.error).toBe('Giriş yapmanız gerekiyor')
    })

    it('handles completion fetch failure gracefully', async () => {
      mockApiRequest.mockImplementation(async (url: string) => {
        if (url.includes('/my-profile')) return { student_id: 'sid-1' }
        if (url.includes('/completion/')) throw new Error('Fetch failed')
        if (url.includes('/streak')) return { daily_streak: 0, best_streak: 0, last_study_date: null }
        return {}
      })
      const { result } = renderHook(() => useLearningPath())
      await waitFor(() => expect(result.current.loading).toBe(false))
      // Path still loads (completion failure is non-fatal)
      expect(result.current.pathNodes).toEqual(makeNodes(['completed', 'current', 'available']))
    })
  })

  describe('Actions', () => {
    it('reload() re-triggers a path load', async () => {
      const { result } = renderHook(() => useLearningPath())
      await waitFor(() => expect(result.current.loading).toBe(false))
      mockCreateLearningPath.mockClear()
      await act(async () => {
        result.current.reload()
      })
      await waitFor(() => expect(mockCreateLearningPath).toHaveBeenCalled())
    })

    it('setCurrentNode() updates current node ID', async () => {
      const { result } = renderHook(() => useLearningPath())
      await waitFor(() => expect(result.current.loading).toBe(false))
      act(() => {
        result.current.setCurrentNode('n3')
      })
      expect(result.current.currentNodeId).toBe('n3')
    })

    it('changeSubject() reloads the path for the new subject', async () => {
      const { result } = renderHook(() => useLearningPath())
      await waitFor(() => expect(result.current.loading).toBe(false))
      mockCreateLearningPath.mockClear()
      await act(async () => {
        result.current.changeSubject('fizik')
      })
      await waitFor(() =>
        expect(mockCreateLearningPath).toHaveBeenCalledWith(
          expect.objectContaining({ subject: 'fizik' }),
        ),
      )
      expect(result.current.selectedSubject).toBe('fizik')
    })
  })

  describe('Return Interface', () => {
    it('returns all expected properties', async () => {
      const { result } = renderHook(() => useLearningPath())
      await waitFor(() => expect(result.current.loading).toBe(false))

      for (const key of [
        'pathNodes', 'learningStyle', 'currentNodeId', 'loading', 'error',
        'needsOnboarding', 'studentId', 'selectedSubject', 'loadPath',
        'reload', 'setCurrentNode', 'updateProgress', 'markNodeComplete',
        'changeSubject', 'startSession', 'endSession',
      ]) {
        expect(result.current).toHaveProperty(key)
      }
      expect(typeof result.current.reload).toBe('function')
      expect(typeof result.current.changeSubject).toBe('function')
    })
  })
})
