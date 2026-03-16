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
const VIDEO_CACHE_TTL = 5 * 60 * 1000; // 5 minutes

// Fallback video type — minimal fields for when external API is unavailable
interface FallbackVideo {
  video_id: string;
  title: string;
  description: string;
  url: string;
  platform: string;
}

const FALLBACK_VIDEOS: Record<string, FallbackVideo[]> = {
  matematik: [
    { video_id: 'mat-temel', title: 'TYT Matematik - Temel Kavramlar', description: 'Hocalara Geldik', url: 'https://www.youtube.com/watch?v=dDxWSnOd5PY', platform: 'youtube' },
    { video_id: 'mat-turev', title: 'AYT Matematik - Turev ve Uygulamalari', description: 'Tonguc Akademi', url: 'https://www.youtube.com/watch?v=0T0z8d0_aY4', platform: 'youtube' },
  ],
  fizik: [
    { video_id: 'fiz-mek', title: 'TYT Fizik - Mekanik', description: 'Hocalara Geldik', url: 'https://www.youtube.com/watch?v=ZM6n5qFsMSo', platform: 'youtube' },
  ],
  kimya: [
    { video_id: 'kim-atom', title: 'TYT Kimya - Atom ve Periyodik Tablo', description: 'Tonguc Akademi', url: 'https://www.youtube.com/watch?v=d0tU18uTMko', platform: 'youtube' },
  ],
  biyoloji: [
    { video_id: 'bio-hucre', title: 'TYT Biyoloji - Hucre', description: 'Hocalara Geldik', url: 'https://www.youtube.com/watch?v=AEOF2gCLaGo', platform: 'youtube' },
  ],
  turkce: [
    { video_id: 'tur-anlatim', title: 'TYT Turkce - Anlatim Bozukluklari', description: 'Tonguc Akademi', url: 'https://www.youtube.com/watch?v=SXkvGzmexBg', platform: 'youtube' },
  ],
  tarih: [
    { video_id: 'tar-ilk', title: 'TYT Tarih - Ilk Uygarliklar', description: 'Hocalara Geldik', url: 'https://www.youtube.com/watch?v=j5b0wJKZ9Kk', platform: 'youtube' },
  ],
  geometri: [
    { video_id: 'geo-ucgen', title: 'TYT Geometri - Ucgenler', description: 'Tonguc Akademi', url: 'https://www.youtube.com/watch?v=bJF3OB2c_k8', platform: 'youtube' },
  ],
  cografya: [
    { video_id: 'cog-iklim', title: 'TYT Cografya - Iklim ve Bitki Ortusu', description: 'Hocalara Geldik', url: 'https://www.youtube.com/watch?v=K2V0zGVP7sI', platform: 'youtube' },
  ],
  edebiyat: [
    { video_id: 'ede-donem', title: 'AYT Edebiyat - Donem Ozellikleri', description: 'Tonguc Akademi', url: 'https://www.youtube.com/watch?v=Ckr8E3BBQOA', platform: 'youtube' },
  ],
};

export interface UseLearningPathVideosReturn {
  videos: VideoResponse[]
  videosLoading: boolean
  videosError: string | null
  loadVideosForPath: (path: any, learningStyle: string, subject?: string) => Promise<void>
  loadVideosForNode: (nodeId: string, nodeTitle: string, nodeDescription: string, nodeDifficulty: string, learningStyle: string) => Promise<void>
  clearCache: () => void
}

export const useLearningPathVideos = (): UseLearningPathVideosReturn => {
  const [videos, setVideos] = useState<VideoResponse[]>([]);
  const [videosLoading, setVideosLoading] = useState(false);
  const [videosError, setVideosError] = useState<string | null>(null);

  /** Load videos for entire learning path */
  const loadVideosForPath = useCallback(async (path: any, learningStyle: string, subject?: string) => {
    try {
      const modules = path?.modules || [];
      const resolvedSubject = subject || (modules.length > 0 ? extractSubject(modules[0]?.title || 'matematik') : 'matematik');
      const cacheKey = `path_${resolvedSubject}_${learningStyle}`;
      const cached = videoCache.get(cacheKey);
      if (cached && Date.now() - cached.timestamp < VIDEO_CACHE_TTL) {
        setVideos(cached.videos);
        return;
      }

      setVideosLoading(true);
      setVideosError(null);

      const result = await searchLearningResources({
        subject: resolvedSubject,
        difficulty: 'orta',
        max_results: 10,
        student_profile: {
          learning_style: learningStyle || 'visual',
          grade: 12,
        },
      });

      if (result.success && result.resources && result.resources.length > 0) {
        videoCache.set(cacheKey, { videos: result.resources, timestamp: Date.now() });
        setVideos(result.resources);
      } else {
        // Use fallback videos when API returns empty
        const fallback = (FALLBACK_VIDEOS[resolvedSubject] || FALLBACK_VIDEOS['matematik']) as unknown as VideoResponse[];
        videoCache.set(cacheKey, { videos: fallback, timestamp: Date.now() });
        setVideos(fallback);
      }
    } catch (err: any) {
      console.error('Error loading videos, using fallback:', err);
      // Use fallback on error too
      const resolvedSubject = subject || 'matematik';
      const fallback = (FALLBACK_VIDEOS[resolvedSubject] || FALLBACK_VIDEOS['matematik']) as unknown as VideoResponse[];
      setVideos(fallback);
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
      const subject = extractSubject(nodeDescription);
      const topic = extractTopic(nodeTitle);
      const difficultyTurkish = difficultyToTurkish(nodeDifficulty as any);

      const cacheKey = `${subject}_${topic || 'all'}_${difficultyTurkish}`;
      const cached = videoCache.get(cacheKey);
      if (cached && Date.now() - cached.timestamp < VIDEO_CACHE_TTL) {
        setVideos(cached.videos);
        return;
      }

      setVideosLoading(true);
      setVideosError(null);

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

      if (result.success && result.resources && result.resources.length > 0) {
        const sorted = result.resources.sort((a, b) => {
          const scoreA = a.scores?.final_score || 0;
          const scoreB = b.scores?.final_score || 0;
          return scoreB - scoreA;
        });
        videoCache.set(cacheKey, { videos: sorted, timestamp: Date.now() });
        setVideos(sorted);
      } else {
        // Use fallback videos when API returns empty or error
        const fallbackKey = subject in FALLBACK_VIDEOS ? subject : 'matematik';
        const fallback = (FALLBACK_VIDEOS[fallbackKey] || FALLBACK_VIDEOS['matematik']) as unknown as VideoResponse[];
        videoCache.set(cacheKey, { videos: fallback, timestamp: Date.now() });
        setVideos(fallback);
        if (result.error) {
          setVideosError(result.error.message);
        }
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
