/**
 * useLearningPathVideos Hook Tests
 * Minimal adaptation for the current hook contract.
 *
 * KIRO2 - YKS Hazirlik Platformu
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';

import { searchLearningResources } from '../../api';
import { useLearningPathVideos } from '../useLearningPathVideos';

vi.mock('../../api', () => ({
  searchLearningResources: vi.fn().mockResolvedValue({
    success: true,
    resources: [],
  }),
}));

vi.mock('../../utils/learningPathHelpers', () => ({
  extractSubject: vi.fn((title: string) => {
    if (title.includes('Türkçe') || title.includes('Turkce')) {return 'turkce';}
    return 'matematik';
  }),
  extractTopic: vi.fn(() => 'türev'),
}));

vi.mock('../../utils/difficultyTranslation', () => ({
  difficultyToTurkish: vi.fn(() => 'orta'),
}));

describe('useLearningPathVideos', () => {
  const mockPath = {
    modules: [
      { title: 'Matematik - Türev', description: 'Türev konusu' },
      { title: 'Fizik - Hareket', description: 'Hareket konusu' },
    ],
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    const { result } = renderHook(() => useLearningPathVideos());
    act(() => {
      result.current.clearCache();
    });
  });

  describe('Initial State', () => {
    it('starts with empty videos array', () => {
      const { result } = renderHook(() => useLearningPathVideos());

      expect(result.current.videos).toEqual([]);
    });

    it('starts with videosLoading false', () => {
      const { result } = renderHook(() => useLearningPathVideos());

      expect(result.current.videosLoading).toBe(false);
    });

    it('starts with no error', () => {
      const { result } = renderHook(() => useLearningPathVideos());

      expect(result.current.videosError).toBeNull();
    });
  });

  describe('loadVideosForPath', () => {
    it('calls searchLearningResources with resolved subject', async () => {
      const { result } = renderHook(() => useLearningPathVideos());

      await act(async () => {
        await result.current.loadVideosForPath(mockPath, 'visual');
      });

      expect(searchLearningResources).toHaveBeenCalledWith(
        expect.objectContaining({
          subject: 'matematik',
          difficulty: 'orta',
          max_results: 10,
          student_profile: expect.objectContaining({
            learning_style: 'visual',
            grade: 12,
          }),
        }),
      );
    });

    it('uses API videos and caches them', async () => {
      vi.mocked(searchLearningResources).mockResolvedValueOnce({
        success: true,
        resources: [
          {
            video_id: 'v1',
            title: 'TYT Matematik',
            channel: 'Kanal',
            channel_id: '',
            duration: 'PT10M',
            view_count: 10,
            upload_date: '',
            thumbnail: '',
            quality_score: 0.8,
            subject: 'matematik',
            difficulty: 'orta',
            exam_type: 'TYT',
            url: 'https://example.com/1',
            is_turkish: true,
            description: 'aciklama',
          },
        ],
      } as any);

      const { result } = renderHook(() => useLearningPathVideos());

      await act(async () => {
        await result.current.loadVideosForPath(mockPath, 'visual');
      });

      expect(result.current.videos).toHaveLength(1);
      expect(result.current.videosError).toBeNull();

      await act(async () => {
        await result.current.loadVideosForPath(mockPath, 'visual');
      });

      expect(searchLearningResources).toHaveBeenCalledTimes(1);
    });

    it('falls back to built-in videos when API returns empty', async () => {
      vi.mocked(searchLearningResources).mockResolvedValueOnce({
        success: true,
        resources: [],
      } as any);

      const { result } = renderHook(() => useLearningPathVideos());

      await act(async () => {
        await result.current.loadVideosForPath({ modules: [{ title: 'Türkçe' }] }, 'visual', 'turkce');
      });

      expect(result.current.videos.length).toBeGreaterThan(0);
      expect(result.current.videosError).toContain('Önbellekteki öneriler');
    });
  });

  describe('loadVideosForNode', () => {
    it('calls searchLearningResources with node details', async () => {
      const { result } = renderHook(() => useLearningPathVideos());

      await act(async () => {
        await result.current.loadVideosForNode(
          'node-1',
          'Türev Hesabı',
          'Matematik türev konusu',
          'intermediate',
          'visual',
        );
      });

      expect(searchLearningResources).toHaveBeenCalledWith(
        expect.objectContaining({
          subject: 'matematik',
          topic: 'türev',
          difficulty: 'orta',
          max_results: 10,
        }),
      );
    });

    it('sorts resources by final_score', async () => {
      vi.mocked(searchLearningResources).mockResolvedValueOnce({
        success: true,
        resources: [
          { video_id: 'v1', scores: { final_score: 0.5 } },
          { video_id: 'v2', scores: { final_score: 0.9 } },
          { video_id: 'v3', scores: { final_score: 0.7 } },
        ],
      } as any);

      const { result } = renderHook(() => useLearningPathVideos());

      await act(async () => {
        await result.current.loadVideosForNode(
          'node-1',
          'Türev',
          'Matematik',
          'intermediate',
          'visual',
        );
      });

      expect(result.current.videos[0].scores?.final_score).toBe(0.9);
      expect(result.current.videos[1].scores?.final_score).toBe(0.7);
      expect(result.current.videos[2].scores?.final_score).toBe(0.5);
    });

    it('handles API error with fallback videos', async () => {
      vi.mocked(searchLearningResources).mockResolvedValueOnce({
        success: false,
        resources: [],
        error: { message: 'API Error' },
      } as any);

      const { result } = renderHook(() => useLearningPathVideos());

      await act(async () => {
        await result.current.loadVideosForNode(
          'node-1',
          'Türev',
          'Matematik',
          'intermediate',
          'visual',
        );
      });

      expect(result.current.videos.length).toBeGreaterThan(0);
      expect(result.current.videosError).toBe('API Error');
    });
  });

  describe('clearCache', () => {
    it('clears cache and current videos', async () => {
      vi.mocked(searchLearningResources).mockResolvedValueOnce({
        success: true,
        resources: [
          {
            video_id: 'v1',
            title: 'TYT Matematik',
            channel: 'Kanal',
            channel_id: '',
            duration: 'PT10M',
            view_count: 10,
            upload_date: '',
            thumbnail: '',
            quality_score: 0.8,
            subject: 'matematik',
            difficulty: 'orta',
            exam_type: 'TYT',
            url: 'https://example.com/1',
            is_turkish: true,
            description: 'aciklama',
          },
        ],
      } as any);

      const { result } = renderHook(() => useLearningPathVideos());

      await act(async () => {
        await result.current.loadVideosForPath(mockPath, 'visual');
      });

      act(() => {
        result.current.clearCache();
      });

      expect(result.current.videos).toEqual([]);
    });
  });

  describe('Return Interface', () => {
    it('returns the current hook contract', () => {
      const { result } = renderHook(() => useLearningPathVideos());

      expect(result.current).toHaveProperty('videos');
      expect(result.current).toHaveProperty('videosLoading');
      expect(result.current).toHaveProperty('videosError');
      expect(result.current).toHaveProperty('loadVideosForPath');
      expect(result.current).toHaveProperty('loadVideosForNode');
      expect(result.current).toHaveProperty('clearCache');

      expect(typeof result.current.loadVideosForPath).toBe('function');
      expect(typeof result.current.loadVideosForNode).toBe('function');
      expect(typeof result.current.clearCache).toBe('function');
    });
  });
});
