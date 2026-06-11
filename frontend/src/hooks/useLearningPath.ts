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
import type { OnboardingResult } from '../components/LearningPath/OnboardingWizard';
import { useAuthStore } from '../store/authStore';
import { apiRequest } from '../utils/apiHelpers';
import { convertPathToNodes } from '../utils/learningPathHelpers';

export interface ProgressUpdate {
  nodeId: string
  progress?: number  // 0-100
  completed?: boolean
}

export interface StudySessionInfo {
  sessionId: string | null
  startedAt: Date | null
  isActive: boolean
}

export interface StreakInfo {
  dailyStreak: number
  bestStreak: number
  lastStudyDate: string | null
}

export interface UseLearningPathReturn {
  pathNodes: PathNodeData[]
  learningStyle: string
  currentNodeId: string
  loading: boolean
  error: string | null
<<<<<<< Updated upstream
  setError: (error: string | null) => void
  needsQuiz: boolean
  studentId: string | null
  studySession: StudySessionInfo
  streak: StreakInfo
  loadPath: () => Promise<void>
  reload: () => void
  setCurrentNode: (nodeId: string) => void
  updateProgress: (update: ProgressUpdate) => Promise<boolean>
  markNodeComplete: (nodeId: string) => Promise<boolean>
  submitOnboardingResult: (result: OnboardingResult) => Promise<void>
  /** @alias submitOnboardingResult — accepts QuizResult or OnboardingResult */
  submitQuizResult: (result: any) => Promise<void>
  skipOnboarding: () => void
  /** @alias skipOnboarding */
  skipQuiz: () => void
=======
  needsOnboarding: boolean
  studentId: string | null
  studySession: StudySessionInfo
  streak: StreakInfo
  loadPath: () => Promise<void>
  reload: () => void
  setCurrentNode: (nodeId: string) => void
  updateProgress: (update: ProgressUpdate) => Promise<boolean>
  markNodeComplete: (nodeId: string) => Promise<boolean>
  submitOnboardingResult: (result: OnboardingResult) => Promise<void>
  skipOnboarding: () => void
  startSession: () => Promise<void>
  endSession: (topics?: string[], questionsAnswered?: number, correctCount?: number) => Promise<void>
>>>>>>> Stashed changes
}

export const useLearningPath = (): UseLearningPathReturn => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pathNodes, setPathNodes] = useState<PathNodeData[]>([]);
  const [learningStyle, setLearningStyle] = useState<string>('');
  const [currentNodeId, setCurrentNodeId] = useState<string>('');
<<<<<<< Updated upstream
  const [needsQuiz, setNeedsQuiz] = useState(false);
  const quizSubmittedRef = useRef(false);
=======
  const [needsOnboarding, setNeedsOnboarding] = useState(false);
>>>>>>> Stashed changes
  const [studentId, setStudentId] = useState<string | null>(null);

  // B1: Study session
  const [studySession, setStudySession] = useState<StudySessionInfo>({
    sessionId: null, startedAt: null, isActive: false,
  });

  // B2: Streak
  const [streak, setStreak] = useState<StreakInfo>({
    dailyStreak: 0, bestStreak: 0, lastStudyDate: null,
  });

  // B1: Study session
  const [studySession, setStudySession] = useState<StudySessionInfo>({
    sessionId: null, startedAt: null, isActive: false,
  });

  // B2: Streak
  const [streak, setStreak] = useState<StreakInfo>({
    dailyStreak: 0, bestStreak: 0, lastStudyDate: null,
  });

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
<<<<<<< Updated upstream
  const createAndLoadPath = useCallback(async (sid: string, subject?: string) => {
    const subjectToUse = subject || selectedSubject;
=======
  const createAndLoadPath = useCallback(async (
    sid: string,
    subject = 'matematik',
    durationWeeks = 4,
    difficultyLevel?: string,
  ) => {
>>>>>>> Stashed changes
    let path = null;
    try {
      const pathResponse = await createLearningPath({
        student_id: sid,
<<<<<<< Updated upstream
        subject: subjectToUse,
        duration_weeks: 4,
=======
        subject,
        duration_weeks: durationWeeks,
        difficulty_level: difficultyLevel,
>>>>>>> Stashed changes
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

<<<<<<< Updated upstream
      // 2. Check if VARK questionnaire completed (skip if just submitted in this session)
      if (!quizSubmittedRef.current) {
        const quizDone = await checkQuizCompleted(sid);
        if (!quizDone) {
          // Show quiz UI — don't create path yet
          setNeedsQuiz(true);
          setLoading(false);
          return;
        }
=======
      // 2. Check if VARK questionnaire completed
      const quizDone = await checkQuizCompleted(sid);
      if (!quizDone) {
        // Show quiz UI — don't create path yet
        setNeedsOnboarding(true);
        setLoading(false);
        return;
>>>>>>> Stashed changes
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

  /** Submit onboarding result → update profile → send VARK → create path with real params */
  const submitOnboardingResult = useCallback(async (result: OnboardingResult) => {
    if (!studentId) return;

    try {
      setLoading(true);
      setError(null);

<<<<<<< Updated upstream
      // 1. Send questionnaire responses to backend
      await submitQuestionnaire(studentId, {
        questionnaire_type: 'VARK',
        responses: result.responses,
        completion_time: result.completion_time,
      });

      // 2. Detect learning style with fresh data (non-blocking — must not prevent path creation)
      try {
        await createStudentProfile({
          name: user?.ad || 'Öğrenci',
          grade: 12,
          subjects: result.subjects,
          goals: [`${result.examType} hazırlık`],
          learning_style: result.learningPreference,
          available_time: result.availableTime,
        });
      } catch {
        // Profile may already exist — continue
      }

      // 3. Quiz done — create path (ALWAYS runs even if detect fails)
      quizSubmittedRef.current = true;
      // Persist in localStorage to prevent re-show on page refresh
      lpCache.set(CACHE_KEYS.QUIZ_COMPLETED, true, CACHE_TTL);
      setNeedsQuiz(false);
      await createAndLoadPath(studentId);
=======
      // 1. Update student profile with real data from wizard
      try {
        await createStudentProfile({
          name: user?.ad || 'Öğrenci',
          grade: 12,
          subjects: result.subjects,
          goals: [`${result.examType} hazırlık`],
          learning_style: result.learningPreference,
          available_time: result.availableTime,
        });
      } catch {
        // Profile may already exist — continue
      }

      // 2. Send VARK questionnaire responses
      await submitQuestionnaire(studentId, {
        questionnaire_type: 'VARK',
        responses: result.varkResponses,
        completion_time: result.completionTime,
      });

      // 3. Detect learning style with fresh data
      const styleResponse = await detectLearningStyle(studentId, true);
      if (styleResponse.success) {
        setLearningStyle(styleResponse.data?.hybrid_code || result.learningPreference);
      } else {
        setLearningStyle(result.learningPreference);
      }

      // 4. Create path with REAL parameters from wizard
      setNeedsOnboarding(false);
      const durationWeeks = Math.ceil(result.durationMonths * 4.3);
      await createAndLoadPath(
        studentId,
        result.subjects[0] || 'matematik',
        durationWeeks,
        result.knowledgeLevel,
      );
>>>>>>> Stashed changes

    } catch (err: any) {
      console.error('Error submitting onboarding:', err);
      setError(err.message || 'Onboarding sonuçları gönderilemedi');
    } finally {
      setLoading(false);
    }
  }, [studentId, user, createAndLoadPath]);

  /** Skip onboarding — use default style */
  const skipOnboarding = useCallback(() => {
    setNeedsOnboarding(false);
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

<<<<<<< Updated upstream
  /** Auto-load on mount and auth changes (NOT on internal callback ref changes) */
  useEffect(() => {
    loadPath();
    // Dependencies: auth state only — prevents re-triggering after quiz submission
    // when createAndLoadPath/loadPath refs change due to state updates.
    // Manual reload available via reload() button.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated, user?.id]);
=======
  // B1: Start study session
  const startSession = useCallback(async () => {
    try {
      const data = await apiRequest<{ session_id: string; started_at: string }>(
        '/api/learning-path/study-session/start',
        { method: 'POST' },
      );
      setStudySession({
        sessionId: data.session_id,
        startedAt: new Date(data.started_at),
        isActive: true,
      });
    } catch (err) {
      console.error('Oturum başlatılamadı:', err);
    }
  }, []);

  // B1: End study session
  const endSession = useCallback(async (
    topics: string[] = [],
    questionsAnswered = 0,
    correctCount = 0,
  ) => {
    if (!studySession.sessionId) return;
    try {
      const data = await apiRequest<{
        duration_minutes: number;
        daily_streak: number;
        best_streak: number;
      }>('/api/learning-path/study-session/end', {
        method: 'POST',
        body: JSON.stringify({
          session_id: studySession.sessionId,
          topics_studied: topics,
          questions_answered: questionsAnswered,
          correct_count: correctCount,
        }),
      });
      setStudySession({ sessionId: null, startedAt: null, isActive: false });
      setStreak(prev => ({
        ...prev,
        dailyStreak: data.daily_streak,
        bestStreak: data.best_streak,
      }));
    } catch (err) {
      console.error('Oturum sonlandırılamadı:', err);
    }
  }, [studySession.sessionId]);

  // B2: Load streak on mount
  const loadStreak = useCallback(async () => {
    try {
      const data = await apiRequest<{
        daily_streak: number;
        best_streak: number;
        last_study_date: string | null;
      }>('/api/learning-path/streak');
      setStreak({
        dailyStreak: data.daily_streak,
        bestStreak: data.best_streak,
        lastStudyDate: data.last_study_date,
      });
    } catch {
      // Not critical
    }
  }, []);

  /** Auto-load on mount */
  useEffect(() => {
    loadPath();
    loadStreak();
  }, [loadPath, loadStreak]);
>>>>>>> Stashed changes

  return {
    pathNodes,
    learningStyle,
    currentNodeId,
    loading,
    error,
<<<<<<< Updated upstream
    setError,
    needsQuiz,
    studentId,
    selectedSubject,
    changeSubject,
=======
    needsOnboarding,
    studentId,
    studySession,
    streak,
>>>>>>> Stashed changes
    loadPath,
    reload,
    setCurrentNode,
    updateProgress,
    markNodeComplete,
    submitOnboardingResult,
    skipOnboarding,
    startSession,
    endSession,
  };
};

export default useLearningPath;
