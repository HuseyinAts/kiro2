/**
 * useLearningPath Hook
 *
 * Manages learning path data and state.
 * Uses httpOnly cookie auth (apiRequest) + useAuthStore for user identity.
 *
 * Flow:
 * 1. Get/create student profile
 * 2. Check if VARK questionnaire completed → if not, show quiz
 * 3. After quiz → create learning path with real style
 * 4. Load path nodes + completion status
 */

import { useState, useEffect, useCallback } from 'react';

import { createStudentProfile, createLearningPath, detectLearningStyle, submitQuestionnaire } from '../api';
import { PathNodeData } from '../components/LearningPath/PathNode';
import { QuizResult } from '../components/LearningPath/LearningStyleQuiz';
import { useAuthStore } from '../store/authStore';
import { apiRequest } from '../utils/apiHelpers';
import { convertPathToNodes } from '../utils/learningPathHelpers';

export interface ProgressUpdate {
  nodeId: string
  progress?: number  // 0-100
  completed?: boolean
}

export interface UseLearningPathReturn {
  pathNodes: PathNodeData[]
  learningStyle: string
  currentNodeId: string
  loading: boolean
  error: string | null
  needsQuiz: boolean
  studentId: string | null
  loadPath: () => Promise<void>
  reload: () => void
  setCurrentNode: (nodeId: string) => void
  updateProgress: (update: ProgressUpdate) => Promise<boolean>
  markNodeComplete: (nodeId: string) => Promise<boolean>
  submitQuizResult: (result: QuizResult) => Promise<void>
  skipQuiz: () => void
}

export const useLearningPath = (): UseLearningPathReturn => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pathNodes, setPathNodes] = useState<PathNodeData[]>([]);
  const [learningStyle, setLearningStyle] = useState<string>('');
  const [currentNodeId, setCurrentNodeId] = useState<string>('');
  const [needsQuiz, setNeedsQuiz] = useState(false);
  const [studentId, setStudentId] = useState<string | null>(null);

  const user = useAuthStore(state => state.user);
  const isAuthenticated = useAuthStore(state => state.isAuthenticated);

  /** Load completion status from backend (cookie auth automatic) */
  const loadCompletionStatus = useCallback(async (sid: string): Promise<Record<string, boolean>> => {
    try {
      const data = await apiRequest<{ data: Record<string, boolean> }>(
        `/api/learning-path/completion/${sid}`,
      );
      return data.data || {};
    } catch {
      console.warn('Could not load completion status');
      return {};
    }
  }, []);

  /** Check if student has real VARK data (not just defaults) */
  const checkQuizCompleted = useCallback(async (sid: string): Promise<boolean> => {
    try {
      const styleResponse = await detectLearningStyle(sid);
      if (styleResponse.success && styleResponse.data) {
        const confidence = styleResponse.data.confidence?.score ?? 0;
        const dataPoints = styleResponse.data.data_points_used ?? 0;

        // Real questionnaire/behavioral data exists if confidence > 0.4 AND data points > 3
        // Default profiles have confidence=0.3 and data_points=0
        if (confidence > 0.4 && dataPoints > 3) {
          setLearningStyle(styleResponse.data.hybrid_code || styleResponse.data.vark_profile?.dominant || 'mixed');
          return true;
        }
      }
    } catch {
      // Detection failed — quiz needed
    }
    return false;
  }, []);

  /** Load or create student profile, returns studentId */
  const ensureProfile = useCallback(async (): Promise<string> => {
    try {
      const myProfile = await apiRequest<{ student_id: string }>(
        '/api/learning-path/my-profile',
      );
      return myProfile.student_id;
    } catch (profileErr: any) {
      if (profileErr.message?.includes('401') || profileErr.message?.includes('Oturum')) {
        throw profileErr;
      }
      // Profile doesn't exist yet — create with default style (will be updated after quiz)
      const profile = await createStudentProfile({
        name: user?.ad || 'Öğrenci',
        grade: 12,
        subjects: ['matematik', 'fizik', 'kimya'],
        goals: ['YKS hazırlık'],
        learning_style: 'mixed',
        available_time: 120,
      });
      return profile.student_id;
    }
  }, [user]);

  /** Create learning path and load nodes */
  const createAndLoadPath = useCallback(async (sid: string) => {
    let path = null;
    try {
      const pathResponse = await createLearningPath({
        student_id: sid,
        subject: 'matematik',
        duration_weeks: 4,
      });
      if (pathResponse.success) {
        path = pathResponse.learning_path;
      }
    } catch (err: any) {
      console.warn('Could not create/load learning path:', err);
      setError(err.message || 'Öğrenme yolu oluşturulamadı');
      return;
    }

    // Load completion status
    const completionStatus = await loadCompletionStatus(sid);

    // Convert path to nodes
    if (path) {
      const nodes = convertPathToNodes(path, completionStatus);
      setPathNodes(nodes);

      const current = nodes.find(n => n.status === 'current');
      if (current) {
        setCurrentNodeId(current.id);
      }
    }
  }, [loadCompletionStatus]);

  /** Main load function */
  const loadPath = useCallback(async () => {
    if (!isAuthenticated || !user) {
      setError('Giriş yapmanız gerekiyor');
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      // 1. Get or create student profile
      const sid = await ensureProfile();
      setStudentId(sid);

      // 2. Check if VARK questionnaire completed
      const quizDone = await checkQuizCompleted(sid);
      if (!quizDone) {
        // Show quiz UI — don't create path yet
        setNeedsQuiz(true);
        setLoading(false);
        return;
      }

      // 3. Create/load learning path with real style
      await createAndLoadPath(sid);

    } catch (err: any) {
      console.error('Error loading learning path:', err);
      setError(err.message || 'Öğrenme yolu yüklenirken hata oluştu');
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated, user, ensureProfile, checkQuizCompleted, createAndLoadPath]);

  /** Submit quiz result → send to backend → create path */
  const submitQuizResult = useCallback(async (result: QuizResult) => {
    if (!studentId) return;

    try {
      setLoading(true);
      setError(null);

      // 1. Send questionnaire responses to backend
      await submitQuestionnaire(studentId, {
        questionnaire_type: 'VARK',
        responses: result.responses,
        completion_time: result.completion_time,
      });

      // 2. Detect learning style with fresh data
      const styleResponse = await detectLearningStyle(studentId, true);
      if (styleResponse.success) {
        setLearningStyle(styleResponse.data?.hybrid_code || result.dominant_style);
      } else {
        setLearningStyle(result.dominant_style);
      }

      // 3. Quiz done — create path
      setNeedsQuiz(false);
      await createAndLoadPath(studentId);

    } catch (err: any) {
      console.error('Error submitting quiz:', err);
      setError(err.message || 'Anket sonuçları gönderilemedi');
    } finally {
      setLoading(false);
    }
  }, [studentId, createAndLoadPath]);

  /** Skip quiz — use default style */
  const skipQuiz = useCallback(() => {
    setNeedsQuiz(false);
    setLearningStyle('mixed');
    if (studentId) {
      setLoading(true);
      createAndLoadPath(studentId).finally(() => setLoading(false));
    }
  }, [studentId, createAndLoadPath]);

  /** Reload path data */
  const reload = useCallback(() => {
    loadPath();
  }, [loadPath]);

  /** Set current node ID */
  const setCurrentNode = useCallback((nodeId: string) => {
    setCurrentNodeId(nodeId);
  }, []);

  /** Update progress for a node — syncs with backend */
  const updateProgress = useCallback(async (update: ProgressUpdate): Promise<boolean> => {
    const { nodeId, progress, completed } = update;

    if (!user) {
      console.error('Not authenticated');
      return false;
    }

    const sid = studentId || String(user.id);

    try {
      await apiRequest(`/api/learning-path/progress/${sid}/${nodeId}`, {
        method: 'PUT',
        body: JSON.stringify({
          progress: progress ?? (completed ? 100 : undefined),
          completed: completed ?? false,
        }),
      });

      // Update local state
      setPathNodes(prevNodes =>
        prevNodes.map(node => {
          if (node.id !== nodeId) return node;
          const newProgress = progress ?? (completed ? 100 : node.progress);
          const isCompleted = completed || newProgress === 100;
          return {
            ...node,
            progress: newProgress,
            status: isCompleted ? 'completed' : node.status,
          };
        }),
      );

      // If completed, advance to next node
      if (completed || progress === 100) {
        const currentIndex = pathNodes.findIndex(n => n.id === nodeId);
        if (currentIndex >= 0 && currentIndex < pathNodes.length - 1) {
          const nextNode = pathNodes[currentIndex + 1];
          if (nextNode && nextNode.status !== 'completed') {
            setCurrentNodeId(nextNode.id);
            setPathNodes(prevNodes =>
              prevNodes.map(node =>
                node.id === nextNode.id ? { ...node, status: 'current' } : node,
              ),
            );
          }
        }
      }

      return true;
    } catch (error) {
      console.error('Error updating progress:', error);
      return false;
    }
  }, [user, studentId, pathNodes]);

  /** Mark a node as complete */
  const markNodeComplete = useCallback(async (nodeId: string): Promise<boolean> => {
    return updateProgress({ nodeId, completed: true, progress: 100 });
  }, [updateProgress]);

  /** Auto-load on mount */
  useEffect(() => {
    loadPath();
  }, [loadPath]);

  return {
    pathNodes,
    learningStyle,
    currentNodeId,
    loading,
    error,
    needsQuiz,
    studentId,
    loadPath,
    reload,
    setCurrentNode,
    updateProgress,
    markNodeComplete,
    submitQuizResult,
    skipQuiz,
  };
};

export default useLearningPath;
