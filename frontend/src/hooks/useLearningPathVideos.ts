/**
 * useLearningPathVideos Hook
 *
 * Manages video loading for learning path.
 * Simplified: no VideoLoadingManager singleton, no subscription pattern.
 * Uses apiRequest (httpOnly cookie auth).
 *
 * Features:
 * - Video Cache: Memoized results by subject/difficulty
 * - Error Handling: User-friendly Turkish messages
 */

import { useState, useCallback } from 'react';

import { VideoResponse, searchLearningResources } from '../api';
import { difficultyToTurkish } from '../utils/difficultyTranslation';
import { extractSubject, extractTopic } from '../utils/learningPathHelpers';

// Video cache - prevents duplicate API calls
const videoCache = new Map<string, { videos: VideoResponse[]; timestamp: number }>();

export interface UseLearningPathVideosReturn {
  videos: VideoResponse[]
  videosLoading: boolean
  videosError: string | null
  loadVideosForPath: (path: any, learningStyle: string) => Promise<void>
  loadVideosForNode: (nodeId: string, nodeTitle: string, nodeDescription: string, nodeDifficulty: string, learningStyle: string) => Promise<void>
  clearCache: () => void
}

export const useLearningPathVideos = (): UseLearningPathVideosReturn => {
  const [videos, setVideos] = useState<VideoResponse[]>([]);
  const [videosLoading, setVideosLoading] = useState(false);
  const [videosError, setVideosError] = useState<string | null>(null);

  /** Load videos for entire learning path */
  const loadVideosForPath = useCallback(async (path: any, learningStyle: string) => {
    try {
      setVideosLoading(true);
      setVideosError(null);

      const modules = path?.modules || [];
      if (modules.length === 0) return;

      // Use first module's subject for initial video load
      const subject = extractSubject(modules[0]?.title || 'matematik');

      const result = await searchLearningResources({
        subject,
        difficulty: 'orta',
        max_results: 10,
        student_profile: {
          learning_style: learningStyle || 'visual',
          grade: 12,
        },
      });

      if (result.success && result.resources) {
        setVideos(result.resources);
      }
    } catch (err: any) {
      console.error('Error loading videos:', err);
      setVideosError(err.message || 'Video yüklenirken hata oluştu');
    } finally {
      setVideosLoading(false);
    }
  }, []);

  /** Load videos for a specific node */
  const loadVideosForNode = useCallback(async (
    _nodeId: string,
    nodeTitle: string,
    nodeDescription: string,
    nodeDifficulty: string,
    learningStyle: string,
  ) => {
    try {
      setVideosLoading(true);
      setVideosError(null);

      const subject = extractSubject(nodeDescription);
      const topic = extractTopic(nodeTitle);
      const difficultyTurkish = difficultyToTurkish(nodeDifficulty as any);

      const result = await searchLearningResources({
        subject,
        topic,
        difficulty: difficultyTurkish,
        max_results: 10,
        student_profile: {
          learning_style: learningStyle,
          grade: 12,
        },
      });

      if (result.success && result.resources) {
        // Sort by score
        const sorted = result.resources.sort((a, b) => {
          const scoreA = a.scores?.final_score || 0;
          const scoreB = b.scores?.final_score || 0;
          return scoreB - scoreA;
        });
        setVideos(sorted);
      } else if (result.error) {
        setVideosError(result.error.message);
      }
    } catch (error: any) {
      console.error('Error loading node resources:', error);
      setVideosError(error.message || 'Kaynaklar yüklenirken hata oluştu');
    } finally {
      setVideosLoading(false);
    }
  }, []);

  /** Clear video cache */
  const clearCache = useCallback(() => {
    videoCache.clear();
    setVideos([]);
  }, []);

  return {
    videos,
    videosLoading,
    videosError,
    loadVideosForPath,
    loadVideosForNode,
    clearCache,
  };
};

export default useLearningPathVideos;
