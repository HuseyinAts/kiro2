/**
 * useLearningPath Hook Tests
 * Comprehensive test suite for learning path hook functionality
 *
 * KIRO2 - YKS Hazirlik Platformu
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, waitFor, act } from '@testing-library/react'
import { useLearningPath } from '../useLearningPath'
import learningPathService from '../../services/learningPathService'
import { detectLearningStyle } from '../../api'
import { convertPathToNodes } from '../../utils/learningPathHelpers'

// Mock dependencies
vi.mock('../../services/learningPathService', () => ({
  default: {
    getStudentId: vi.fn(),
    createProfile: vi.fn(),
    getCurrentPath: vi.fn(),
    generateLearningPath: vi.fn(),
  },
}))

vi.mock('../../api', () => ({
  detectLearningStyle: vi.fn(),
}))

vi.mock('../../utils/learningPathHelpers', () => ({
  convertPathToNodes: vi.fn(),
}))

vi.mock('../../config', () => ({
  default: {
    api: {
      baseURL: 'http://localhost:8000',
    },
  },
}))

// Mock fetch
const mockFetch = vi.fn()
global.fetch = mockFetch

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(() => 'mock-token'),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
}
Object.defineProperty(window, 'localStorage', { value: localStorageMock })

describe('useLearningPath', () => {
  const mockStudentId = 'student-123'
  const mockPath = {
    id: 'path-1',
    subject: 'matematik',
    nodes: [
      { id: 'node-1', title: 'Temel Matematik', status: 'completed' },
      { id: 'node-2', title: 'Denklemler', status: 'current' },
      { id: 'node-3', title: 'Fonksiyonlar', status: 'available' },
    ],
  }
  const mockNodes = [
    {
      id: 'node-1',
      title: 'Temel Matematik',
      status: 'completed',
      progress: 100,
    },
    { id: 'node-2', title: 'Denklemler', status: 'current', progress: 50 },
    { id: 'node-3', title: 'Fonksiyonlar', status: 'available', progress: 0 },
  ]
  const mockLearningStyle = 'V-ASVS'

  beforeEach(() => {
    vi.clearAllMocks()

    // Default mock implementations
    vi.mocked(learningPathService.getStudentId).mockReturnValue(mockStudentId)
    vi.mocked(learningPathService.getCurrentPath).mockReturnValue(mockPath)
    vi.mocked(convertPathToNodes).mockReturnValue(mockNodes)
    vi.mocked(detectLearningStyle).mockResolvedValue({
      success: true,
      learning_style: { hybrid_code: mockLearningStyle },
    })
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({ data: { 'node-1': true } }),
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('Initial State', () => {
    it('starts with loading true', async () => {
      const { result } = renderHook(() => useLearningPath())

      // Initially loading
      expect(result.current.loading).toBe(true)

      // Wait for loading to complete
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
    })

    it('starts with no error', async () => {
      const { result } = renderHook(() => useLearningPath())

      expect(result.current.error).toBeNull()

      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
    })

    it('starts with empty path nodes', async () => {
      // Temporarily return empty
      vi.mocked(convertPathToNodes).mockReturnValueOnce([])

      const { result } = renderHook(() => useLearningPath())

      // Nodes should be empty initially
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
    })
  })

  describe('Loading Path Data', () => {
    it('loads path nodes on mount', async () => {
      const { result } = renderHook(() => useLearningPath())

      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })

      expect(result.current.pathNodes).toEqual(mockNodes)
    })

    it('sets current node ID from path data', async () => {
      const { result } = renderHook(() => useLearningPath())

      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })

      // node-2 has status 'current'
      expect(result.current.currentNodeId).toBe('node-2')
    })

    it('loads learning style', async () => {
      const { result } = renderHook(() => useLearningPath())

      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })

      expect(result.current.learningStyle).toBe(mockLearningStyle)
    })

    it('fetches completion status from backend', async () => {
      renderHook(() => useLearningPath())

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/learning-path/completion/'),
          expect.objectContaining({
            headers: expect.objectContaining({
              Authorization: 'Bearer mock-token',
            }),
          })
        )
      })
    })
  })

  describe('Creating Demo Profile', () => {
    it('creates demo profile when no student ID exists', async () => {
      vi.mocked(learningPathService.getStudentId)
        .mockReturnValueOnce(null)
        .mockReturnValue(mockStudentId)

      vi.mocked(learningPathService.createProfile).mockResolvedValue({
        student_id: mockStudentId,
      })

      const { result } = renderHook(() => useLearningPath())

      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })

      expect(learningPathService.createProfile).toHaveBeenCalledWith({
        name: 'Demo Öğrenci',
        grade: 12,
        subjects: ['matematik', 'fizik', 'kimya'],
        goals: ['YKS hazırlık', 'Matematik geliştirme'],
        learning_style: 'visual',
        available_time: 120,
      })
    })
  })

  describe('Generating Learning Path', () => {
    it('generates path when no current path exists', async () => {
      vi.mocked(learningPathService.getCurrentPath).mockReturnValue(null)
      vi.mocked(learningPathService.generateLearningPath).mockResolvedValue(
        mockPath
      )

      const { result } = renderHook(() => useLearningPath())

      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })

      expect(learningPathService.generateLearningPath).toHaveBeenCalledWith(
        'matematik',
        4
      )
    })
  })

  describe('Error Handling', () => {
    it('sets error when path loading fails', async () => {
      const errorMessage = 'Network error'
      vi.mocked(learningPathService.getCurrentPath).mockImplementation(() => {
        throw new Error(errorMessage)
      })

      const { result } = renderHook(() => useLearningPath())

      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })

      expect(result.current.error).toBe(errorMessage)
    })

    it('handles completion status fetch failure gracefully', async () => {
      mockFetch.mockRejectedValue(new Error('Fetch failed'))

      const { result } = renderHook(() => useLearningPath())

      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })

      // Should not throw, just log warning
      expect(result.current.error).toBeNull()
      expect(result.current.pathNodes).toEqual(mockNodes)
    })

    it('uses default learning style when detection fails', async () => {
      vi.mocked(detectLearningStyle).mockRejectedValue(new Error('API error'))

      const { result } = renderHook(() => useLearningPath())

      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })

      expect(result.current.learningStyle).toBe('V-ASVS')
    })
  })

  describe('Actions', () => {
    it('reload() triggers path reload', async () => {
      const { result } = renderHook(() => useLearningPath())

      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })

      // Clear mocks to track new calls
      vi.clearAllMocks()

      // Trigger reload
      await act(async () => {
        result.current.reload()
      })

      await waitFor(() => {
        expect(learningPathService.getCurrentPath).toHaveBeenCalled()
      })
    })

    it('setCurrentNode() updates current node ID', async () => {
      const { result } = renderHook(() => useLearningPath())

      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })

      act(() => {
        result.current.setCurrentNode('node-3')
      })

      expect(result.current.currentNodeId).toBe('node-3')
    })

    it('loadPath() can be called manually', async () => {
      const { result } = renderHook(() => useLearningPath())

      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })

      vi.clearAllMocks()

      await act(async () => {
        await result.current.loadPath()
      })

      expect(learningPathService.getCurrentPath).toHaveBeenCalled()
    })
  })

  describe('Learning Style Detection', () => {
    it('extracts hybrid_code from response', async () => {
      vi.mocked(detectLearningStyle).mockResolvedValue({
        success: true,
        learning_style: { hybrid_code: 'A-KVRS' },
      })

      const { result } = renderHook(() => useLearningPath())

      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })

      expect(result.current.learningStyle).toBe('A-KVRS')
    })

    it('uses default when response has no learning_style', async () => {
      vi.mocked(detectLearningStyle).mockResolvedValue({
        success: true,
        learning_style: {},
      })

      const { result } = renderHook(() => useLearningPath())

      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })

      expect(result.current.learningStyle).toBe('V-ASVS')
    })

    it('uses default when detection returns success: false', async () => {
      vi.mocked(detectLearningStyle).mockResolvedValue({
        success: false,
      })

      const { result } = renderHook(() => useLearningPath())

      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })

      expect(result.current.learningStyle).toBe('V-ASVS')
    })
  })

  describe('Completion Status', () => {
    it('passes completion status to node converter', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          data: { 'node-1': true, 'node-2': false },
        }),
      })

      renderHook(() => useLearningPath())

      await waitFor(() => {
        expect(convertPathToNodes).toHaveBeenCalledWith(mockPath, {
          'node-1': true,
          'node-2': false,
        })
      })
    })

    it('uses empty object when fetch returns non-ok response', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 404,
      })

      renderHook(() => useLearningPath())

      await waitFor(() => {
        expect(convertPathToNodes).toHaveBeenCalledWith(mockPath, {})
      })
    })
  })

  describe('Return Interface', () => {
    it('returns all expected properties', async () => {
      const { result } = renderHook(() => useLearningPath())

      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })

      // Data
      expect(result.current).toHaveProperty('pathNodes')
      expect(result.current).toHaveProperty('learningStyle')
      expect(result.current).toHaveProperty('currentNodeId')

      // State
      expect(result.current).toHaveProperty('loading')
      expect(result.current).toHaveProperty('error')

      // Actions
      expect(result.current).toHaveProperty('loadPath')
      expect(result.current).toHaveProperty('reload')
      expect(result.current).toHaveProperty('setCurrentNode')

      // Types
      expect(typeof result.current.loadPath).toBe('function')
      expect(typeof result.current.reload).toBe('function')
      expect(typeof result.current.setCurrentNode).toBe('function')
    })
  })
})
