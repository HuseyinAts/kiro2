/**
 * LearningPathService Tests
 * Comprehensive test suite for learning path service functionality
 *
 * KIRO2 - YKS Hazirlik Platformu
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import learningPathService from '../learningPathService'
import {
  createStudentProfile,
  assessKnowledge,
  createLearningPath,
  searchResources,
  adaptLearningPath,
} from '../../api'

// Mock API module
vi.mock('../../api', () => ({
  createStudentProfile: vi.fn(),
  assessKnowledge: vi.fn(),
  createLearningPath: vi.fn(),
  searchResources: vi.fn(),
  adaptLearningPath: vi.fn(),
}))

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {}
  return {
    getItem: vi.fn((key: string) => store[key] || null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value
    }),
    removeItem: vi.fn((key: string) => {
      delete store[key]
    }),
    clear: vi.fn(() => {
      store = {}
    }),
    _getStore: () => store,
  }
})()
Object.defineProperty(window, 'localStorage', { value: localStorageMock })

describe('LearningPathService', () => {
  const mockStudentId = 'student-abc-123'
  const mockPathId = 'path-xyz-456'
  const mockProfile = {
    name: 'Test Ogrenci',
    grade: 11,
    subjects: ['matematik', 'fizik'],
    goals: ['YKS hazirlik'],
    learning_style: 'visual',
    available_time: 90,
  }
  const mockPath = {
    path_id: mockPathId,
    student_name: 'Test Ogrenci',
    total_time: 480,
    phases: ['Temel', 'Orta', 'Ileri'],
    resources: [
      {
        resource_id: 'res-1',
        title: 'Matematik Temelleri',
        source: 'youtube',
        url: 'https://youtube.com/watch?v=abc',
        type: 'video',
        estimated_time: 30,
        difficulty: 'kolay',
        description: 'Temel matematik konulari',
      },
    ],
    reasoning: 'AI generated path based on student profile',
  }

  beforeEach(() => {
    vi.clearAllMocks()
    localStorageMock.clear()
    // Reset service state
    learningPathService.clearData()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('createProfile', () => {
    it('creates profile and stores student ID', async () => {
      vi.mocked(createStudentProfile).mockResolvedValue({
        success: true,
        profile: { student_id: mockStudentId, ...mockProfile },
      })

      const result = await learningPathService.createProfile(mockProfile)

      expect(createStudentProfile).toHaveBeenCalledWith(mockProfile)
      expect(result.student_id).toBe(mockStudentId)
      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        'studentId',
        mockStudentId
      )
    })

    it('throws error when API returns failure', async () => {
      vi.mocked(createStudentProfile).mockResolvedValue({
        success: false,
        error: 'Profile creation failed',
      })

      await expect(
        learningPathService.createProfile(mockProfile)
      ).rejects.toThrow('Profile creation failed')
    })

    it('throws error when API call fails', async () => {
      vi.mocked(createStudentProfile).mockRejectedValue(
        new Error('Network error')
      )

      await expect(
        learningPathService.createProfile(mockProfile)
      ).rejects.toThrow('Network error')
    })
  })

  describe('assessStudentKnowledge', () => {
    beforeEach(async () => {
      // Setup student ID
      vi.mocked(createStudentProfile).mockResolvedValue({
        success: true,
        profile: { student_id: mockStudentId },
      })
      await learningPathService.createProfile(mockProfile)
    })

    it('assesses knowledge for a subject', async () => {
      const mockAssessment = {
        level: 'intermediate',
        score: 75,
        weak_areas: ['turev', 'integral'],
      }
      vi.mocked(assessKnowledge).mockResolvedValue({
        success: true,
        assessment: mockAssessment,
      })

      const result = await learningPathService.assessStudentKnowledge(
        'matematik'
      )

      expect(assessKnowledge).toHaveBeenCalledWith({
        student_id: mockStudentId,
        subject: 'matematik',
        questions: undefined,
      })
      expect(result).toEqual(mockAssessment)
    })

    it('passes custom questions when provided', async () => {
      vi.mocked(assessKnowledge).mockResolvedValue({
        success: true,
        assessment: { level: 'beginner' },
      })

      const questions = ['Q1', 'Q2', 'Q3']
      await learningPathService.assessStudentKnowledge('fizik', questions)

      expect(assessKnowledge).toHaveBeenCalledWith({
        student_id: mockStudentId,
        subject: 'fizik',
        questions,
      })
    })

    it('throws error when no student profile exists', async () => {
      learningPathService.clearData()

      await expect(
        learningPathService.assessStudentKnowledge('matematik')
      ).rejects.toThrow('No student profile found')
    })

    it('throws error when API returns failure', async () => {
      vi.mocked(assessKnowledge).mockResolvedValue({
        success: false,
        error: 'Assessment failed',
      })

      await expect(
        learningPathService.assessStudentKnowledge('matematik')
      ).rejects.toThrow('Assessment failed')
    })
  })

  describe('generateLearningPath', () => {
    beforeEach(async () => {
      vi.mocked(createStudentProfile).mockResolvedValue({
        success: true,
        profile: { student_id: mockStudentId },
      })
      await learningPathService.createProfile(mockProfile)
    })

    it('generates learning path and stores it', async () => {
      vi.mocked(createLearningPath).mockResolvedValue({
        success: true,
        learning_path: mockPath,
      })

      const result = await learningPathService.generateLearningPath(
        'matematik',
        4
      )

      expect(createLearningPath).toHaveBeenCalledWith({
        student_id: mockStudentId,
        subject: 'matematik',
        duration_weeks: 4,
        difficulty_level: 'intermediate',
      })
      expect(result).toEqual(mockPath)
      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        'currentPath',
        JSON.stringify(mockPath)
      )
    })

    it('uses default duration of 4 weeks', async () => {
      vi.mocked(createLearningPath).mockResolvedValue({
        success: true,
        learning_path: mockPath,
      })

      await learningPathService.generateLearningPath('fizik')

      expect(createLearningPath).toHaveBeenCalledWith(
        expect.objectContaining({
          duration_weeks: 4,
        })
      )
    })

    it('throws error when no student profile exists', async () => {
      learningPathService.clearData()

      await expect(
        learningPathService.generateLearningPath('matematik')
      ).rejects.toThrow('No student profile found')
    })

    it('throws error when API returns failure', async () => {
      vi.mocked(createLearningPath).mockResolvedValue({
        success: false,
        error: 'Path generation failed',
      })

      await expect(
        learningPathService.generateLearningPath('matematik')
      ).rejects.toThrow('Path generation failed')
    })
  })

  describe('findResources', () => {
    beforeEach(async () => {
      vi.mocked(createStudentProfile).mockResolvedValue({
        success: true,
        profile: { student_id: mockStudentId },
      })
      await learningPathService.createProfile(mockProfile)
    })

    it('searches resources with subject', async () => {
      const mockResources = [
        { resource_id: 'r1', title: 'Matematik Video 1' },
        { resource_id: 'r2', title: 'Matematik Video 2' },
      ]
      vi.mocked(searchResources).mockResolvedValue({
        success: true,
        resources: mockResources,
      })

      const result = await learningPathService.findResources('matematik')

      expect(searchResources).toHaveBeenCalledWith({
        subject: 'matematik',
        topic: undefined,
        difficulty: 'orta',
        max_results: 10,
        student_profile: expect.objectContaining({
          student_id: mockStudentId,
        }),
      })
      expect(result).toEqual(mockResources)
    })

    it('passes all options to API', async () => {
      vi.mocked(searchResources).mockResolvedValue({
        success: true,
        resources: [],
      })

      await learningPathService.findResources('fizik', {
        topic: 'mekanik',
        difficulty: 'zor',
        learning_style: 'auditory',
        grade: 12,
        max_results: 20,
      })

      expect(searchResources).toHaveBeenCalledWith({
        subject: 'fizik',
        topic: 'mekanik',
        difficulty: 'zor',
        max_results: 20,
        student_profile: expect.objectContaining({
          student_id: mockStudentId,
          learning_style: 'auditory',
          grade: 12,
        }),
      })
    })

    it('throws error when API returns failure', async () => {
      vi.mocked(searchResources).mockResolvedValue({
        success: false,
        error: 'Search failed',
      })

      await expect(learningPathService.findResources('matematik')).rejects.toThrow(
        'Search failed'
      )
    })
  })

  describe('updateLearningPath', () => {
    beforeEach(async () => {
      vi.mocked(createStudentProfile).mockResolvedValue({
        success: true,
        profile: { student_id: mockStudentId },
      })
      vi.mocked(createLearningPath).mockResolvedValue({
        success: true,
        learning_path: mockPath,
      })
      await learningPathService.createProfile(mockProfile)
      await learningPathService.generateLearningPath('matematik')
    })

    it('adapts learning path with progress data', async () => {
      const updatedPath = { ...mockPath, phases: ['Yeni Faz'] }
      vi.mocked(adaptLearningPath).mockResolvedValue({
        success: true,
        adapted_path: updatedPath,
      })

      const progressData = { completed_nodes: ['node-1'], score: 85 }
      const result = await learningPathService.updateLearningPath(progressData)

      expect(adaptLearningPath).toHaveBeenCalledWith({
        path_id: mockPathId,
        progress_data: progressData,
      })
      expect(result).toEqual(updatedPath)
    })

    it('throws error when no active path exists', async () => {
      learningPathService.clearData()

      await expect(
        learningPathService.updateLearningPath({ score: 80 })
      ).rejects.toThrow('No active learning path found')
    })

    it('throws error when API returns failure', async () => {
      vi.mocked(adaptLearningPath).mockResolvedValue({
        success: false,
        error: 'Adaptation failed',
      })

      await expect(
        learningPathService.updateLearningPath({ score: 80 })
      ).rejects.toThrow('Adaptation failed')
    })
  })

  describe('getStudentId', () => {
    it('returns student ID after profile creation', async () => {
      vi.mocked(createStudentProfile).mockResolvedValue({
        success: true,
        profile: { student_id: mockStudentId },
      })
      await learningPathService.createProfile(mockProfile)

      expect(learningPathService.getStudentId()).toBe(mockStudentId)
    })

    it('retrieves from localStorage when not in memory', () => {
      learningPathService.clearData()
      localStorageMock.getItem.mockReturnValue(mockStudentId)

      // Create new instance behavior - directly test localStorage retrieval
      const result = learningPathService.getStudentId()

      expect(localStorageMock.getItem).toHaveBeenCalledWith('studentId')
    })

    it('returns null when no student ID exists', () => {
      learningPathService.clearData()
      localStorageMock.getItem.mockReturnValue(null)

      expect(learningPathService.getStudentId()).toBeNull()
    })
  })

  describe('getCurrentPath', () => {
    it('returns current path after generation', async () => {
      vi.mocked(createStudentProfile).mockResolvedValue({
        success: true,
        profile: { student_id: mockStudentId },
      })
      vi.mocked(createLearningPath).mockResolvedValue({
        success: true,
        learning_path: mockPath,
      })
      await learningPathService.createProfile(mockProfile)
      await learningPathService.generateLearningPath('matematik')

      expect(learningPathService.getCurrentPath()).toEqual(mockPath)
    })

    it('retrieves from localStorage when not in memory', () => {
      learningPathService.clearData()
      localStorageMock.getItem.mockReturnValue(JSON.stringify(mockPath))

      const result = learningPathService.getCurrentPath()

      expect(localStorageMock.getItem).toHaveBeenCalledWith('currentPath')
      expect(result).toEqual(mockPath)
    })

    it('returns null when no path exists', () => {
      learningPathService.clearData()
      localStorageMock.getItem.mockReturnValue(null)

      expect(learningPathService.getCurrentPath()).toBeNull()
    })
  })

  describe('clearData', () => {
    it('clears all data from memory and localStorage', async () => {
      vi.mocked(createStudentProfile).mockResolvedValue({
        success: true,
        profile: { student_id: mockStudentId },
      })
      vi.mocked(createLearningPath).mockResolvedValue({
        success: true,
        learning_path: mockPath,
      })
      await learningPathService.createProfile(mockProfile)
      await learningPathService.generateLearningPath('matematik')

      learningPathService.clearData()

      expect(localStorageMock.removeItem).toHaveBeenCalledWith('studentId')
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('currentPath')

      // Reset mock to return null
      localStorageMock.getItem.mockReturnValue(null)
      expect(learningPathService.getStudentId()).toBeNull()
      expect(learningPathService.getCurrentPath()).toBeNull()
    })
  })
})
