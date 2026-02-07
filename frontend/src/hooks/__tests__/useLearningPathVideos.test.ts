/**
 * useLearningPathVideos Hook Tests
 * Comprehensive test suite for video loading hook functionality
 *
 * KIRO2 - YKS Hazirlik Platformu
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, waitFor, act } from '@testing-library/react'
import { useLearningPathVideos } from '../useLearningPathVideos'
import { VideoLoadingManager } from '../../services/VideoLoadingManager'

// Mock VideoLoadingManager - must use inline factory since vi.mock is hoisted
vi.mock('../../services/VideoLoadingManager', () => {
  // Create mock functions that can be reused
  const createMockInstance = () => ({
    subscribe: vi.fn(() => vi.fn()), // Returns unsubscribe function
    loadVideos: vi.fn().mockResolvedValue([]),
    retryLoad: vi.fn().mockResolvedValue([]),
    cancelLoad: vi.fn(),
    getState: vi.fn(() => ({
      status: 'idle',
      videos: [],
      error: null,
      loadingProgress: 0,
      retryCount: 0,
      requestId: '',
      loadingTime: 0,
    })),
    reset: vi.fn(),
  })

  // Mock constructor function
  const MockVideoLoadingManager = vi.fn(() => createMockInstance())

  return {
    VideoLoadingManager: MockVideoLoadingManager,
  }
})

// Mock VideoErrorHandler
vi.mock('../../services/VideoErrorHandler', () => ({
  VideoErrorHandler: vi.fn().mockImplementation(() => ({
    logError: vi.fn(),
  })),
}))

// Mock config
vi.mock('../../config', () => ({
  default: {
    api: {
      baseURL: 'http://localhost:8000',
    },
  },
}))

// Mock API
vi.mock('../../api', () => ({
  searchLearningResources: vi.fn().mockResolvedValue({
    success: true,
    resources: [],
  }),
}))

// Mock helpers
vi.mock('../../utils/learningPathHelpers', () => ({
  extractSubject: vi.fn((title) => 'matematik'),
  extractTopic: vi.fn((title) => 'türev'),
}))

vi.mock('../../utils/difficultyTranslation', () => ({
  difficultyToTurkish: vi.fn((diff) => 'orta'),
}))

// Mock fetch for fallback videos
const mockFetch = vi.fn()
global.fetch = mockFetch

describe('useLearningPathVideos', () => {
  const mockPath = {
    modules: [
      { title: 'Matematik - Türev', description: 'Türev konusu' },
      { title: 'Fizik - Hareket', description: 'Hareket konusu' },
    ],
  }

  const mockVideos = [
    {
      video_id: 'video-1',
      title: 'Türev Konu Anlatımı',
      channel: 'TonguçAkademi',
      quality_score: 0.85,
      subject: 'matematik',
    },
    {
      video_id: 'video-2',
      title: 'Hareket Soruları',
      channel: 'Khan Academy',
      quality_score: 0.78,
      subject: 'fizik',
    },
  ]

  beforeEach(() => {
    vi.clearAllMocks()
    mockFetch.mockReset()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('Initial State', () => {
    it('starts with empty videos array', () => {
      const { result } = renderHook(() => useLearningPathVideos())

      expect(result.current.videos).toEqual([])
    })

    it('starts with videosLoading false', () => {
      const { result } = renderHook(() => useLearningPathVideos())

      expect(result.current.videosLoading).toBe(false)
    })

    it('starts with no error', () => {
      const { result } = renderHook(() => useLearningPathVideos())

      expect(result.current.videosError).toBeNull()
    })

    it('starts with empty loading subjects', () => {
      const { result } = renderHook(() => useLearningPathVideos())

      expect(result.current.loadingSubjects).toEqual([])
    })

    it('initializes video loading state with idle status', () => {
      const { result } = renderHook(() => useLearningPathVideos())

      expect(result.current.videoLoadingState.status).toBe('idle')
      expect(result.current.videoLoadingState.loadingProgress).toBe(0)
    })
  })

  describe('VideoLoadingManager Initialization', () => {
    it('creates VideoLoadingManager with correct config', () => {
      renderHook(() => useLearningPathVideos())

      expect(VideoLoadingManager).toHaveBeenCalledWith(
        'http://localhost:8000',
        20000,
        2
      )
    })

    it('subscribes to state changes', () => {
      renderHook(() => useLearningPathVideos())

      const mockInstance = vi.mocked(VideoLoadingManager).mock.results[0].value
      expect(mockInstance.subscribe).toHaveBeenCalled()
    })

    it('unsubscribes on unmount', () => {
      const unsubscribeMock = vi.fn()
      const mockSubscribe = vi.fn().mockReturnValue(unsubscribeMock)

      vi.mocked(VideoLoadingManager).mockImplementationOnce(() => ({
        subscribe: mockSubscribe,
        loadVideos: vi.fn(),
        retryLoad: vi.fn(),
        cancelLoad: vi.fn(),
        getState: vi.fn().mockReturnValue({ status: 'idle', videos: [] }),
        reset: vi.fn(),
      }))

      const { unmount } = renderHook(() => useLearningPathVideos())
      unmount()

      expect(unsubscribeMock).toHaveBeenCalled()
    })
  })

  describe('loadVideosForPath', () => {
    it('calls VideoLoadingManager.loadVideos with student profile', async () => {
      const { result } = renderHook(() => useLearningPathVideos())

      const mockInstance = vi.mocked(VideoLoadingManager).mock.results[0].value

      await act(async () => {
        await result.current.loadVideosForPath(mockPath, 'visual')
      })

      expect(mockInstance.loadVideos).toHaveBeenCalledWith(
        expect.objectContaining({
          goals: expect.any(Array),
          current_level: expect.any(Object),
          learning_style: 'visual',
        })
      )
    })

    it('extracts subjects from path modules', async () => {
      const { result } = renderHook(() => useLearningPathVideos())

      await act(async () => {
        await result.current.loadVideosForPath(mockPath, 'visual')
      })

      expect(result.current.loadingSubjects.length).toBeGreaterThan(0)
    })

    it('handles load error gracefully', async () => {
      const mockInstance = vi.mocked(VideoLoadingManager).mock.results[0]?.value
      if (mockInstance) {
        mockInstance.loadVideos.mockRejectedValueOnce(new Error('Load failed'))
      }

      const { result } = renderHook(() => useLearningPathVideos())

      await act(async () => {
        await result.current.loadVideosForPath(mockPath, 'visual')
      })

      // Should not throw, error handled internally
      expect(result.current.videos).toEqual([])
    })
  })

  describe('loadVideosForNode', () => {
    it('calls searchLearningResources with node details', async () => {
      const { searchLearningResources } = await import('../../api')

      const { result } = renderHook(() => useLearningPathVideos())

      await act(async () => {
        await result.current.loadVideosForNode(
          'node-1',
          'Türev Hesabı',
          'Matematik türev konusu',
          'intermediate',
          'visual'
        )
      })

      expect(searchLearningResources).toHaveBeenCalledWith(
        expect.objectContaining({
          subject: 'matematik',
          topic: 'türev',
          difficulty: 'orta',
          max_results: 10,
        })
      )
    })

    it('sets videosLoading to true during load', async () => {
      const { searchLearningResources } = await import('../../api')
      vi.mocked(searchLearningResources).mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve({ success: true, resources: [] }), 100))
      )

      const { result } = renderHook(() => useLearningPathVideos())

      act(() => {
        result.current.loadVideosForNode(
          'node-1',
          'Türev',
          'Matematik',
          'intermediate',
          'visual'
        )
      })

      expect(result.current.videosLoading).toBe(true)
    })

    it('sorts resources by final_score', async () => {
      const { searchLearningResources } = await import('../../api')
      vi.mocked(searchLearningResources).mockResolvedValue({
        success: true,
        resources: [
          { video_id: 'v1', scores: { final_score: 0.5 } },
          { video_id: 'v2', scores: { final_score: 0.9 } },
          { video_id: 'v3', scores: { final_score: 0.7 } },
        ],
      })

      const { result } = renderHook(() => useLearningPathVideos())

      await act(async () => {
        await result.current.loadVideosForNode(
          'node-1',
          'Türev',
          'Matematik',
          'intermediate',
          'visual'
        )
      })

      // Should be sorted by score descending
      expect(result.current.videos[0].scores?.final_score).toBe(0.9)
      expect(result.current.videos[1].scores?.final_score).toBe(0.7)
      expect(result.current.videos[2].scores?.final_score).toBe(0.5)
    })

    it('handles API error', async () => {
      const { searchLearningResources } = await import('../../api')
      vi.mocked(searchLearningResources).mockResolvedValue({
        success: false,
        error: { message: 'API Error' },
      })

      const { result } = renderHook(() => useLearningPathVideos())

      await act(async () => {
        await result.current.loadVideosForNode(
          'node-1',
          'Türev',
          'Matematik',
          'intermediate',
          'visual'
        )
      })

      expect(result.current.videosError).toBe('API Error')
    })
  })

  describe('retryLoad', () => {
    it('calls VideoLoadingManager.retryLoad', async () => {
      const { result } = renderHook(() => useLearningPathVideos())

      const mockInstance = vi.mocked(VideoLoadingManager).mock.results[0].value

      await act(async () => {
        await result.current.retryLoad()
      })

      expect(mockInstance.retryLoad).toHaveBeenCalled()
    })
  })

  describe('cancelLoad', () => {
    it('calls VideoLoadingManager.cancelLoad', () => {
      const { result } = renderHook(() => useLearningPathVideos())

      const mockInstance = vi.mocked(VideoLoadingManager).mock.results[0].value

      act(() => {
        result.current.cancelLoad()
      })

      expect(mockInstance.cancelLoad).toHaveBeenCalled()
    })
  })

  describe('showFallback', () => {
    it('fetches fallback videos from API', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          success: true,
          videos: [
            {
              resource_id: 'fallback-1',
              title: 'Fallback Video',
              url: 'https://youtube.com/watch?v=fallback1',
            },
          ],
        }),
      })

      const { result } = renderHook(() => useLearningPathVideos())

      // Set loading subjects first
      await act(async () => {
        await result.current.loadVideosForPath(mockPath, 'visual')
      })

      await act(async () => {
        await result.current.showFallback()
      })

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/learning-path/fallback-videos/'),
        expect.any(Object)
      )
    })

    it('handles fallback API error', async () => {
      mockFetch.mockRejectedValue(new Error('Network error'))

      const { result } = renderHook(() => useLearningPathVideos())

      await act(async () => {
        await result.current.showFallback()
      })

      expect(result.current.videosError).toBe('Örnek video yükleme hatası')
    })

    it('handles empty fallback response', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          success: true,
          videos: [],
        }),
      })

      const { result } = renderHook(() => useLearningPathVideos())

      await act(async () => {
        await result.current.showFallback()
      })

      expect(result.current.videosError).toBe('Örnek video bulunamadı')
    })
  })

  describe('State Subscription', () => {
    it('updates videosLoading when state changes to loading', () => {
      let stateCallback: ((state: any) => void) | null = null

      vi.mocked(VideoLoadingManager).mockImplementationOnce(() => ({
        subscribe: vi.fn((cb) => {
          stateCallback = cb
          return vi.fn()
        }),
        loadVideos: vi.fn(),
        retryLoad: vi.fn(),
        cancelLoad: vi.fn(),
        getState: vi.fn(),
        reset: vi.fn(),
      }))

      const { result } = renderHook(() => useLearningPathVideos())

      // Simulate state change
      act(() => {
        stateCallback?.({
          status: 'loading',
          videos: [],
          error: null,
          loadingProgress: 50,
          retryCount: 0,
          requestId: 'req-1',
          loadingTime: 0,
        })
      })

      expect(result.current.videosLoading).toBe(true)
    })

    it('updates videos when state changes to success', () => {
      let stateCallback: ((state: any) => void) | null = null

      vi.mocked(VideoLoadingManager).mockImplementationOnce(() => ({
        subscribe: vi.fn((cb) => {
          stateCallback = cb
          return vi.fn()
        }),
        loadVideos: vi.fn(),
        retryLoad: vi.fn(),
        cancelLoad: vi.fn(),
        getState: vi.fn(),
        reset: vi.fn(),
      }))

      const { result } = renderHook(() => useLearningPathVideos())

      // Simulate success state
      act(() => {
        stateCallback?.({
          status: 'success',
          videos: [
            {
              subject_exam: 'matematik-yks',
              videos: mockVideos,
            },
          ],
          error: null,
          loadingProgress: 100,
          retryCount: 0,
          requestId: 'req-1',
          loadingTime: 500,
        })
      })

      expect(result.current.videosLoading).toBe(false)
      expect(result.current.videosError).toBeNull()
      expect(result.current.videos.length).toBe(2)
    })

    it('updates error when state changes to error', () => {
      let stateCallback: ((state: any) => void) | null = null

      vi.mocked(VideoLoadingManager).mockImplementationOnce(() => ({
        subscribe: vi.fn((cb) => {
          stateCallback = cb
          return vi.fn()
        }),
        loadVideos: vi.fn(),
        retryLoad: vi.fn(),
        cancelLoad: vi.fn(),
        getState: vi.fn(),
        reset: vi.fn(),
      }))

      const { result } = renderHook(() => useLearningPathVideos())

      // Simulate error state
      act(() => {
        stateCallback?.({
          status: 'error',
          videos: [],
          error: new Error('Load failed'),
          errorMessage: 'Video yükleme başarısız',
          loadingProgress: 0,
          retryCount: 2,
          requestId: 'req-1',
          loadingTime: 0,
        })
      })

      expect(result.current.videosError).toBe('Video yükleme başarısız')
    })
  })

  describe('Return Interface', () => {
    it('returns all expected properties', () => {
      const { result } = renderHook(() => useLearningPathVideos())

      // Data
      expect(result.current).toHaveProperty('videos')
      expect(result.current).toHaveProperty('videoLoadingState')
      expect(result.current).toHaveProperty('loadingSubjects')

      // Legacy state
      expect(result.current).toHaveProperty('videosLoading')
      expect(result.current).toHaveProperty('videosError')

      // Actions
      expect(result.current).toHaveProperty('loadVideosForPath')
      expect(result.current).toHaveProperty('loadVideosForNode')
      expect(result.current).toHaveProperty('retryLoad')
      expect(result.current).toHaveProperty('showFallback')
      expect(result.current).toHaveProperty('cancelLoad')

      // Types
      expect(typeof result.current.loadVideosForPath).toBe('function')
      expect(typeof result.current.loadVideosForNode).toBe('function')
      expect(typeof result.current.retryLoad).toBe('function')
      expect(typeof result.current.showFallback).toBe('function')
      expect(typeof result.current.cancelLoad).toBe('function')
    })
  })
})
