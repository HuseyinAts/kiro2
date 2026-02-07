/**
 * useLearningPathVideos Hook
 *
 * Custom hook for managing video loading with VideoLoadingManager
 * Extracted from LearningPathPage.tsx
 */

import { useState, useEffect, useRef, useCallback } from 'react';

import { VideoResponse, searchLearningResources } from '../api';
import config from '../config';
import { VideoErrorHandler } from '../services/VideoErrorHandler';
import { VideoLoadingManager, VideoLoadingState } from '../services/VideoLoadingManager';
import { difficultyToTurkish } from '../utils/difficultyTranslation';
import { extractSubject, extractTopic } from '../utils/learningPathHelpers';

export interface UseLearningPathVideosReturn {
  // Data
  videos: VideoResponse[]
  videoLoadingState: VideoLoadingState
  loadingSubjects: string[]

  // Legacy state (for compatibility)
  videosLoading: boolean
  videosError: string | null

  // Actions
  loadVideosForPath: (path: any, learningStyle: string) => Promise<void>
  loadVideosForNode: (nodeId: string, nodeTitle: string, nodeDescription: string, nodeDifficulty: string, learningStyle: string) => Promise<void>
  retryLoad: () => Promise<void>
  showFallback: () => Promise<void>
  cancelLoad: () => void
}

/**
 * Hook for managing video loading in learning path
 *
 * @returns Video loading state and actions
 *
 * @example
 * const { videos, videosLoading, loadVideosForPath } = useLearningPathVideos()
 */
export const useLearningPathVideos = (): UseLearningPathVideosReturn => {
  const [videos, setVideos] = useState<VideoResponse[]>([]);
  const [videosLoading, setVideosLoading] = useState(false);
  const [videosError, setVideosError] = useState<string | null>(null);
  const [loadingSubjects, setLoadingSubjects] = useState<string[]>([]);

  const [videoLoadingState, setVideoLoadingState] = useState<VideoLoadingState>({
    status: 'idle',
    videos: [],
    error: null,
    loadingProgress: 0,
    retryCount: 0,
    requestId: '',
    loadingTime: 0,
    cacheHit: false,
    errorMessage: undefined,
  });

  // Refs for managers
  const videoManagerRef = useRef<VideoLoadingManager | null>(null);
  const videoErrorHandlerRef = useRef<VideoErrorHandler | null>(null);

  // Ref for current loading subjects (to avoid dependency loop)
  const loadingSubjectsRef = useRef<string[]>([]);

  /**
   * Initialize VideoLoadingManager and VideoErrorHandler
   */
  useEffect(() => {
    // Initialize VideoLoadingManager with 20s timeout and 2 retries
    videoManagerRef.current = new VideoLoadingManager(config.api.baseURL, 20000, 2);

    // Initialize VideoErrorHandler
    videoErrorHandlerRef.current = new VideoErrorHandler(false, true); // Sentry disabled, console enabled

    // Subscribe to state changes
    const unsubscribe = videoManagerRef.current.subscribe((state) => {
      setVideoLoadingState(state);

      // Update legacy state for compatibility
      setVideosLoading(state.status === 'loading');
      if (state.status === 'error' || state.status === 'fallback') {
        setVideosError(state.errorMessage || state.error?.message || 'Video yükleme hatası');
      } else if (state.status === 'success') {
        setVideosError(null);
        // Convert SubjectVideos to VideoResponse format
        const allVideos: VideoResponse[] = [];
        state.videos.forEach(subjectVideo => {
          if (subjectVideo.videos) {
            // Cast to VideoResponse[] - VideoRecommendation is compatible
            allVideos.push(...(subjectVideo.videos as unknown as VideoResponse[]));
          }
        });
        setVideos(allVideos);
      }
    });

    return () => {
      unsubscribe();
    };
  }, []);

  /**
   * Load videos for entire learning path
   */
  const loadVideosForPath = useCallback(async (path: any, learningStyle: string) => {
    if (!videoManagerRef.current) {
      console.error('VideoLoadingManager not initialized');
      return;
    }

    try {
      // Extract subjects from path modules
      const subjects = (path.modules || []).map((module: any) => extractSubject(module.title));

      // Update both state and ref
      setLoadingSubjects(subjects);
      loadingSubjectsRef.current = subjects;

      // Build student profile for video recommendations
      const subjectLevels = subjects.reduce((acc: any, s: string) => {
        acc[s] = 50; // Default level
        return acc;
      }, {}) as Record<string, number>;

      const studentProfile = {
        name: 'anonymous',
        goals: subjects.map((s: string) => `${s} öğrenme`),
        current_level: subjectLevels,
        currentLevel: subjectLevels,
        learning_style: learningStyle || 'visual',
        learningStyle: learningStyle || 'visual',
        preferences: {
          grade: 12,
          exam_type: 'YKS',
        },
      };

      // Use VideoLoadingManager to load videos
      console.log('Loading videos with VideoLoadingManager...', studentProfile);
      await videoManagerRef.current.loadVideos(studentProfile as any);

      // State updates are handled by the subscription
    } catch (err: any) {
      console.error('Error loading videos:', err);

      // Error handling is managed by VideoLoadingManager
      if (videoErrorHandlerRef.current) {
        const errorContext = {
          component: 'useLearningPathVideos',
          action: 'loadVideosForPath',
          subjects: loadingSubjectsRef.current,  // Use ref instead of state
        } as any;  // ErrorContext has different required fields
        videoErrorHandlerRef.current.logError(err, errorContext);
      }
    }
  }, []);  // Empty dependency array - no state dependencies

  /**
   * Load videos for specific node
   */
  const loadVideosForNode = useCallback(async (
    nodeId: string,
    nodeTitle: string,
    nodeDescription: string,
    nodeDifficulty: string,
    learningStyle: string,
  ) => {
    try {
      setVideosLoading(true);
      setVideosError(null);

      // Extract subject from node description
      const subject = extractSubject(nodeDescription);
      const topic = extractTopic(nodeTitle);

      // Convert English difficulty to Turkish for backend API
      const difficultyTurkish = difficultyToTurkish(nodeDifficulty as any);

      console.log(`Loading resources for node: ${nodeId}, subject: ${subject}, topic: ${topic}, difficulty: ${difficultyTurkish}`);

      const result = await searchLearningResources({
        subject: subject,
        topic: topic,
        difficulty: difficultyTurkish,
        max_results: 10,
        student_profile: {
          learning_style: learningStyle,
          grade: 12,
        },
      });

      if (result.success && result.resources) {
        console.log(`Loaded ${result.resources.length} resources for node ${nodeId}`);

        // Sort by score
        const sortedResources = result.resources.sort((a, b) => {
          const scoreA = a.scores?.final_score || 0;
          const scoreB = b.scores?.final_score || 0;
          return scoreB - scoreA;
        });

        setVideos(sortedResources);
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

  /**
   * Retry video loading
   */
  const retryLoad = useCallback(async () => {
    if (!videoManagerRef.current) {return;}
    // Create a minimal profile for retry - the manager uses its cached state
    const defaultProfile = { name: 'retry', goals: [], current_level: {}, learning_style: 'visual', preferences: {} } as any;
    await videoManagerRef.current.retryLoad(defaultProfile);
  }, []);

  /**
   * Show fallback videos
   */
  const showFallback = useCallback(async () => {
    if (!videoManagerRef.current) {
      console.error('VideoLoadingManager not initialized');
      return;
    }

    try {
      setVideosLoading(true);
      setVideosError(null);

      // Get subject from current path (use ref to avoid dependency loop)
      const subject = loadingSubjectsRef.current[0] || 'matematik';

      // Call fallback video API
      const response = await fetch(`${config.api.baseURL}/api/learning-path/fallback-videos/${subject}?limit=10`, {
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success && data.videos && data.videos.length > 0) {
          // Convert fallback videos to VideoResponse format
          const fallbackVideos = data.videos.map((v: any) => ({
            video_id: v.resource_id,
            title: v.title,
            description: v.description,
            url: v.url,
            thumbnail_url: v.thumbnail,
            duration: v.duration,
            duration_minutes: v.duration_minutes,
            channel_name: v.channel_name,
            scores: v.scores,
            is_accessible: v.is_accessible,
            is_turkish: true,
            is_example: v.is_example,
            tags: v.tags,
          }));

          setVideos(fallbackVideos);
          setVideosError(null);

          console.log(`✅ Loaded ${fallbackVideos.length} fallback videos for ${subject}`);
          alert(`✅ ${fallbackVideos.length} örnek video yüklendi! ${subject} için kaliteli eğitim videoları gösteriliyor.`);
        } else {
          setVideosError('Örnek video bulunamadı');
          alert('⚠️ Henüz bu konu için örnek video eklenmemiş.');
        }
      } else {
        throw new Error('Fallback video API failed');
      }
    } catch (error: any) {
      console.error('Error loading fallback videos:', error);
      setVideosError('Örnek video yükleme hatası');
      alert('❌ Örnek videolar yüklenirken hata oluştu. Lütfen daha sonra tekrar deneyin.');
    } finally {
      setVideosLoading(false);
    }
  }, []);  // Empty dependency array - uses ref instead of state

  /**
   * Cancel ongoing video load
   */
  const cancelLoad = useCallback(() => {
    if (!videoManagerRef.current) {return;}
    videoManagerRef.current.cancelLoad();
    console.log('Video loading cancelled by user');
  }, []);

  return {
    videos,
    videoLoadingState,
    loadingSubjects,
    videosLoading,
    videosError,
    loadVideosForPath,
    loadVideosForNode,
    retryLoad,
    showFallback,
    cancelLoad,
  };
};

export default useLearningPathVideos;
