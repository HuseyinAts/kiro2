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
const VIDEO_CACHE_MAX_SIZE = 50;

/** Evict oldest entry when cache exceeds max size */
function setCacheEntry(key: string, videos: VideoResponse[]) {
  if (videoCache.size >= VIDEO_CACHE_MAX_SIZE) {
    let oldestKey = '';
    let oldestTime = Infinity;
    for (const [k, v] of videoCache) {
      if (v.timestamp < oldestTime) {
        oldestTime = v.timestamp;
        oldestKey = k;
      }
    }
    if (oldestKey) videoCache.delete(oldestKey);
  }
  videoCache.set(key, { videos, timestamp: Date.now() });
}

/** Create a properly typed fallback video entry */
function makeFallback(
  id: string, title: string, channel: string, url: string,
  subject: string, exam_type: string = 'TYT', duration: string = 'PT15M',
): VideoResponse {
  return {
    video_id: id, title, channel, channel_id: '', duration,
    view_count: 0, upload_date: '', thumbnail: '', quality_score: 0,
    subject, difficulty: 'orta', exam_type, url,
    is_turkish: true, description: title,
  };
}

const FALLBACK_VIDEOS: Record<string, VideoResponse[]> = {
  matematik: [
    makeFallback('mat-temel', 'TYT Matematik - Temel Kavramlar', 'Hocalara Geldik', 'https://www.youtube.com/watch?v=dDxWSnOd5PY', 'matematik'),
    makeFallback('mat-turev', 'AYT Matematik - Turev ve Uygulamalari', 'Tonguc Akademi', 'https://www.youtube.com/watch?v=0T0z8d0_aY4', 'matematik', 'AYT'),
    makeFallback('mat-problem', 'TYT Matematik - Problem Cozme Teknikleri', 'Matematik Kafasi', 'https://www.youtube.com/watch?v=3qM9GNb5k7A', 'matematik'),
  ],
  fizik: [
    makeFallback('fiz-mek', 'TYT Fizik - Mekanik', 'Hocalara Geldik', 'https://www.youtube.com/watch?v=ZM6n5qFsMSo', 'fizik'),
    makeFallback('fiz-elektrik', 'TYT Fizik - Elektrik ve Manyetizma', 'Tonguc Akademi', 'https://www.youtube.com/watch?v=mPwBMY5GnKo', 'fizik'),
    makeFallback('fiz-dalga', 'AYT Fizik - Dalga Mekani\u011fi', 'Hocalara Geldik', 'https://www.youtube.com/watch?v=vy1U6sDjcIY', 'fizik', 'AYT'),
  ],
  kimya: [
    makeFallback('kim-atom', 'TYT Kimya - Atom ve Periyodik Tablo', 'Tonguc Akademi', 'https://www.youtube.com/watch?v=d0tU18uTMko', 'kimya'),
    makeFallback('kim-baglar', 'TYT Kimya - Kimyasal Baglar', 'Hocalara Geldik', 'https://www.youtube.com/watch?v=B5cVz0hCFIg', 'kimya'),
    makeFallback('kim-organik', 'AYT Kimya - Organik Kimya', 'Tonguc Akademi', 'https://www.youtube.com/watch?v=QkJT3u0bFnU', 'kimya', 'AYT'),
  ],
  biyoloji: [
    makeFallback('bio-hucre', 'TYT Biyoloji - Hucre', 'Hocalara Geldik', 'https://www.youtube.com/watch?v=AEOF2gCLaGo', 'biyoloji'),
    makeFallback('bio-kalitim', 'AYT Biyoloji - Kalitim', 'Tonguc Akademi', 'https://www.youtube.com/watch?v=dF2GDSchmGE', 'biyoloji', 'AYT'),
    makeFallback('bio-ekoloji', 'TYT Biyoloji - Ekoloji', 'Hocalara Geldik', 'https://www.youtube.com/watch?v=8HYzpBqr7Vs', 'biyoloji'),
  ],
  turkce: [
    makeFallback('tur-anlatim', 'TYT Turkce - Anlatim Bozukluklari', 'Tonguc Akademi', 'https://www.youtube.com/watch?v=SXkvGzmexBg', 'turkce'),
    makeFallback('tur-paragraf', 'TYT Turkce - Paragraf Sorulari', 'Hocalara Geldik', 'https://www.youtube.com/watch?v=xM4vbsFL2kA', 'turkce'),
    makeFallback('tur-dil', 'TYT Turkce - Dil Bilgisi Konu Anlatimi', 'Tonguc Akademi', 'https://www.youtube.com/watch?v=yP6BOqbCmFQ', 'turkce'),
  ],
  tarih: [
    makeFallback('tar-ilk', 'TYT Tarih - Ilk Uygarliklar', 'Hocalara Geldik', 'https://www.youtube.com/watch?v=j5b0wJKZ9Kk', 'tarih'),
    makeFallback('tar-osmanli', 'TYT Tarih - Osmanli Devleti', 'Tonguc Akademi', 'https://www.youtube.com/watch?v=rENgXbC6tDY', 'tarih'),
    makeFallback('tar-cumhuriyet', 'TYT Tarih - Cumhuriyet Donemi', 'Hocalara Geldik', 'https://www.youtube.com/watch?v=3cYmV8Pq7WI', 'tarih'),
  ],
  geometri: [
    makeFallback('geo-ucgen', 'TYT Geometri - Ucgenler', 'Tonguc Akademi', 'https://www.youtube.com/watch?v=bJF3OB2c_k8', 'geometri'),
    makeFallback('geo-daire', 'TYT Geometri - Daire ve Cember', 'Hocalara Geldik', 'https://www.youtube.com/watch?v=YW_6FGNPHM4', 'geometri'),
    makeFallback('geo-katicicisim', 'AYT Geometri - Kati Cisimler', 'Tonguc Akademi', 'https://www.youtube.com/watch?v=S8UqkJXj6VE', 'geometri', 'AYT'),
  ],
  cografya: [
    makeFallback('cog-iklim', 'TYT Cografya - Iklim ve Bitki Ortusu', 'Hocalara Geldik', 'https://www.youtube.com/watch?v=K2V0zGVP7sI', 'cografya'),
    makeFallback('cog-turkiye', 'TYT Cografya - Turkiye Fiziki Cografyasi', 'Tonguc Akademi', 'https://www.youtube.com/watch?v=d4TrIE5gDws', 'cografya'),
    makeFallback('cog-nufus', 'TYT Cografya - Nufus ve Yerlesme', 'Hocalara Geldik', 'https://www.youtube.com/watch?v=Ht0V8UCLtN4', 'cografya'),
  ],
  edebiyat: [
    makeFallback('ede-donem', 'AYT Edebiyat - Donem Ozellikleri', 'Tonguc Akademi', 'https://www.youtube.com/watch?v=Ckr8E3BBQOA', 'edebiyat', 'AYT'),
    makeFallback('ede-siir', 'AYT Edebiyat - Siir Bilgisi', 'Hocalara Geldik', 'https://www.youtube.com/watch?v=z6f4HjF4zYE', 'edebiyat', 'AYT'),
    makeFallback('ede-roman', 'AYT Edebiyat - Roman Turleri', 'Tonguc Akademi', 'https://www.youtube.com/watch?v=fVGpkX8K6Vk', 'edebiyat', 'AYT'),
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
          learning_style: learningStyle || 'mixed',
          grade: 12,
        },
      });

      if (result.success && result.resources && result.resources.length > 0) {
        setCacheEntry(cacheKey, result.resources);
        setVideos(result.resources);
      } else {
        // Use fallback videos when API returns empty
        const fallback = FALLBACK_VIDEOS[resolvedSubject] || FALLBACK_VIDEOS['matematik'];
        setCacheEntry(cacheKey, fallback);
        setVideos(fallback);
      }
    } catch (err: any) {
      console.error('Error loading videos, using fallback:', err);
      // Use fallback on error too
      const resolvedSubject = subject || 'matematik';
      const fallback = FALLBACK_VIDEOS[resolvedSubject] || FALLBACK_VIDEOS['matematik'];
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
        setCacheEntry(cacheKey, sorted);
        setVideos(sorted);
      } else {
        // Use fallback videos when API returns empty or error
        const fallbackKey = subject in FALLBACK_VIDEOS ? subject : 'matematik';
        const fallback = FALLBACK_VIDEOS[fallbackKey] || FALLBACK_VIDEOS['matematik'];
        setCacheEntry(cacheKey, fallback);
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
