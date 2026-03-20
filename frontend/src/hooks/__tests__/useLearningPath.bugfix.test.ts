/**
 * useLearningPath — Bug Fix Tests
 *
 * Tests for Fix 5: updateProgress/markNodeComplete return
 * { success: boolean, allCompleted: boolean } instead of boolean.
 *
 * These tests verify the quiz completion flow changes.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor, act } from '@testing-library/react'

// --- Mock state (mutable so tests can override) ---
const mockAuthState = {
  user: { id: 'user-1', ad: 'Test' } as any,
  isAuthenticated: true,
}

// --- Mock modules ---
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
    data: {
      confidence: { score: 0.8 },
      data_points_used: 10,
      hybrid_code: 'V-ASVS',
      vark_profile: { dominant: 'V' },
    },
  }),
  submitQuestionnaire: vi.fn(),
}))

const mockApiRequest = vi.fn()
vi.mock('../../utils/apiHelpers', () => ({
  apiRequest: (...args: any[]) => mockApiRequest(...args),
}))

const mockConvert = vi.fn()
vi.mock('../../utils/learningPathHelpers', () => ({
  convertPathToNodes: (...args: any[]) => mockConvert(...args),
}))

import { useLearningPath } from '../useLearningPath'

// --- Test data ---
const makeNodes = (statuses: Array<'completed' | 'current' | 'available'>) =>
  statuses.map((status, i) => ({
    id: `n${i + 1}`,
    title: `Node ${i + 1}`,
    status,
    progress: status === 'completed' ? 100 : status === 'current' ? 50 : 0,
  }))

describe('useLearningPath — Fix 5: updateProgress return type', () => {
  beforeEach(() => {
    vi.clearAllMocks()

    // Reset auth state
    mockAuthState.user = { id: 'user-1', ad: 'Test' }
    mockAuthState.isAuthenticated = true

    // Default API mocks for loadPath to succeed
    mockApiRequest.mockImplementation(async (url: string) => {
      if (url.includes('/my-profile')) return { student_id: 'sid-1' }
      if (url.includes('/completion/')) return { data: {} }
      if (url.includes('/progress/')) return {}
      return {}
    })

    // Default: 3 nodes, middle one is current
    mockConvert.mockReturnValue(makeNodes(['completed', 'current', 'available']))
  })

  /** Helper: render hook and wait for initial load to complete */
  const setup = async () => {
    const hook = renderHook(() => useLearningPath())
    await waitFor(() => expect(hook.result.current.loading).toBe(false))
    return hook
  }

  it('updateProgress returns { success: true, allCompleted: false } for partial progress', async () => {
    const { result } = await setup()

    let res: any
    await act(async () => {
      res = await result.current.updateProgress({ nodeId: 'n2', progress: 75 })
    })

    expect(res).toEqual({ success: true, allCompleted: false })
  })

  it('markNodeComplete returns { success: true, allCompleted: false } when other nodes remain', async () => {
    const { result } = await setup()

    let res: any
    await act(async () => {
      res = await result.current.markNodeComplete('n2')
    })

    // n3 is still 'available', not all completed
    expect(res).toEqual({ success: true, allCompleted: false })
  })

  it('markNodeComplete returns { success: true, allCompleted: true } when last node completed', async () => {
    // All nodes completed except n3 (current)
    mockConvert.mockReturnValue(makeNodes(['completed', 'completed', 'current']))

    const { result } = await setup()

    let res: any
    await act(async () => {
      res = await result.current.markNodeComplete('n3')
    })

    expect(res).toEqual({ success: true, allCompleted: true })
  })

  it('updateProgress returns { success: false, allCompleted: false } on API error', async () => {
    const { result } = await setup()

    // Make progress API fail
    mockApiRequest.mockImplementation(async (url: string) => {
      if (url.includes('/progress/')) throw new Error('Server error')
      if (url.includes('/my-profile')) return { student_id: 'sid-1' }
      if (url.includes('/completion/')) return { data: {} }
      return {}
    })

    let res: any
    await act(async () => {
      res = await result.current.updateProgress({ nodeId: 'n2', progress: 80 })
    })

    expect(res).toEqual({ success: false, allCompleted: false })
  })

  it('updateProgress returns { success: false, allCompleted: false } when no user', async () => {
    // Start with no auth — loadPath will set error but not studentId
    mockAuthState.user = null
    mockAuthState.isAuthenticated = false

    const hook = renderHook(() => useLearningPath())
    await waitFor(() => expect(hook.result.current.loading).toBe(false))

    let res: any
    await act(async () => {
      res = await hook.result.current.updateProgress({ nodeId: 'n1', progress: 50 })
    })

    expect(res).toEqual({ success: false, allCompleted: false })
  })

  it('allCompleted is false when node is not being completed (partial progress)', async () => {
    // Even if all other nodes are completed, partial progress should NOT trigger allCompleted
    mockConvert.mockReturnValue(makeNodes(['completed', 'completed', 'current']))

    const { result } = await setup()

    let res: any
    await act(async () => {
      // 60% progress, NOT completed
      res = await result.current.updateProgress({ nodeId: 'n3', progress: 60 })
    })

    // progress !== 100 and completed is not set → allCompleted should be false
    expect(res).toEqual({ success: true, allCompleted: false })
  })
})
