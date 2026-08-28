/**
 * useLearningPath — API path-prefix regression tests
 *
 * S200 frontend-backend integration audit (docs/audits/2026-07-05_frontend_backend_integration_audit.md)
 * found every apiRequest() call in this hook missing the /v1/ segment
 * (e.g. '/api/learning-path/my-profile' instead of '/api/v1/learning-path/my-profile'),
 * which 404s against every registered backend router and silently re-creates
 * the student profile on every page load. This file locks in the fix.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor, act } from '@testing-library/react'

const mockAuthState = {
  user: { id: 'user-1', ad: 'Test' } as any,
  isAuthenticated: true,
}

vi.mock('../../store/authStore', () => ({
  useAuthStore: vi.fn((selector: (state: any) => any) => selector(mockAuthState)),
}))

vi.mock('../../api', () => ({
  createStudentProfile: vi.fn(),
  createLearningPath: vi.fn().mockResolvedValue({
    success: true,
    learning_path: { id: 'path-1', subject: 'matematik', nodes: [] },
  }),
  detectLearningStyle: vi.fn().mockResolvedValue({
    success: true,
    data: { confidence: { score: 0.8 }, data_points_used: 10, hybrid_code: 'V-ASVS' },
  }),
  submitQuestionnaire: vi.fn(),
}))

const mockApiRequest = vi.fn()
vi.mock('../../utils/apiHelpers', () => ({
  apiRequest: (...args: any[]) => mockApiRequest(...args),
}))

vi.mock('../../utils/learningPathHelpers', () => ({
  convertPathToNodes: vi.fn().mockReturnValue([]),
}))

import { useLearningPath } from '../useLearningPath'

describe('useLearningPath — API path prefix (S200 audit fix)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockAuthState.user = { id: 'user-1', ad: 'Test' }
    mockAuthState.isAuthenticated = true

    mockApiRequest.mockImplementation(async (url: string) => {
      if (url.includes('/my-profile')) {return { student_id: 'sid-1' }}
      if (url.includes('/completion/')) {return { data: {} }}
      if (url.includes('/progress/')) {return {}}
      if (url.includes('/study-sessions/start')) {
        return { success: true, data: { session_id: 'sess-1', session_type: 'regular', started_at: '2026-07-05T00:00:00Z' } }
      }
      if (url.includes('/study-sessions/') && url.includes('/end')) {
        return { success: true, data: { session_id: 'sess-1', duration_minutes: 12 } }
      }
      if (url.includes('/streak')) {return { daily_streak: 3, best_streak: 7, last_study_date: '2026-07-04' }}
      return {}
    })
  })

  const setup = async () => {
    const hook = renderHook(() => useLearningPath())
    await waitFor(() => expect(hook.result.current.loading).toBe(false))
    return hook
  }

  it('ensureProfile calls the v1-prefixed my-profile endpoint', async () => {
    await setup()
    expect(mockApiRequest).toHaveBeenCalledWith('/api/v1/learning-path/my-profile')
  })

  it('loadCompletionStatus calls the v1-prefixed completion endpoint', async () => {
    await setup()
    expect(mockApiRequest).toHaveBeenCalledWith('/api/v1/learning-path/completion/sid-1')
  })

  it('updateProgress calls the v1-prefixed progress endpoint', async () => {
    const { result } = await setup()
    await act(async () => {
      await result.current.updateProgress({ nodeId: 'n1', progress: 50 })
    })
    expect(mockApiRequest).toHaveBeenCalledWith(
      '/api/v1/learning-path/progress/sid-1/n1',
      expect.objectContaining({ method: 'PUT' }),
    )
  })

  it('loadStreak calls the v1-prefixed streak endpoint', async () => {
    await setup()
    expect(mockApiRequest).toHaveBeenCalledWith('/api/v1/learning-path/streak')
  })

  it('startSession calls the real registered FSRS endpoint and unwraps the data envelope', async () => {
    const { result } = await setup()
    await act(async () => {
      await result.current.startSession()
    })
    expect(mockApiRequest).toHaveBeenCalledWith(
      '/api/v1/fsrs/study-sessions/start',
      expect.objectContaining({ method: 'POST' }),
    )
    expect(result.current.studySession.sessionId).toBe('sess-1')
    expect(result.current.studySession.isActive).toBe(true)
  })

  it('endSession puts session_id in the path (not the body) and refreshes streak afterwards', async () => {
    const { result } = await setup()
    await act(async () => {
      await result.current.startSession()
    })
    mockApiRequest.mockClear()

    await act(async () => {
      await result.current.endSession()
    })

    expect(mockApiRequest).toHaveBeenCalledWith(
      '/api/v1/fsrs/study-sessions/sess-1/end',
      expect.objectContaining({ method: 'POST' }),
    )
    // FSRS end response has no daily_streak/best_streak — hook must re-fetch streak separately
    expect(mockApiRequest).toHaveBeenCalledWith('/api/v1/learning-path/streak')
    expect(result.current.studySession.isActive).toBe(false)
  })
})
