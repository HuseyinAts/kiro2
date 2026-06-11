/**
 * Modern Learning Path Page - Glassmorphism Design
 * Kişiselleştirilmiş öğrenme yolu ve kaynaklar.
 *
 * @TODO S179 fix (B-P1-21): this file is 1,165 LOC and has 6 direct
 * `fetch()` calls bypassing `services/learningPathService.ts`. Sprint
 * plan: split into `LearningPathOverview` + `QuizPanel` +
 * `InterleavedSession` + `DuelLaunchPanel` sub-components, route via
 * `lazy()`. DO NOT add new responsibilities to this file.
 */

<<<<<<< Updated upstream
import { Timeline, VideoLibrary, Assessment, Refresh, AutoAwesome, Shuffle, Science, SportsEsports } from '@mui/icons-material';
import { Container, Box, Tabs, Tab, Typography, Alert, Chip, ToggleButton, ToggleButtonGroup, Dialog, DialogContent, IconButton } from '@mui/material';
=======
import { Timeline, VideoLibrary, Assessment, Refresh, AutoAwesome, Shuffle, Science, CalendarToday, PlayArrow, Stop, LocalFireDepartment, Timer, AccountTree } from '@mui/icons-material';
import { Container, Box, Tabs, Tab, Typography, Alert, Chip } from '@mui/material';
>>>>>>> Stashed changes
import { motion, AnimatePresence } from 'framer-motion';
import { useState, useEffect, useCallback, useMemo, useRef } from 'react';

// Custom hooks
import { VideoResponse } from '../api';
<<<<<<< Updated upstream
import { LearningStyleQuiz } from '../components/LearningPath/LearningStyleQuiz';
import { TopicList } from '../components/LearningPath/TopicList';
// DungeonMap (parşömen + fog-of-war) sade TopicList ile değiştirildi (fallback olarak korunuyor)
// import { ModernLearningPathVisualizer } from '../components/LearningPath/ModernLearningPathVisualizer';
=======
import { OnboardingWizard } from '../components/LearningPath/OnboardingWizard';
import { ModernLearningPathVisualizer } from '../components/LearningPath/ModernLearningPathVisualizer';
>>>>>>> Stashed changes
import { NodeDetailsPanel } from '../components/LearningPath/Page/NodeDetailsPanel';
import type { LayoutNode } from '../hooks/useDungeonMap';
import { PathNodeData } from '../components/LearningPath/PathNode';
import { GlassCard } from '../components/ui/GlassCard';
import { ModernButton } from '../components/ui/ModernButton';
import { ModernLoader } from '../components/ui/ModernLoader';
import { QuizInterface } from '../components/Quiz/QuizInterface';
import type { Question } from '../components/Quiz/QuizInterface';
import type { ErrorType } from '../components/Quiz/ErrorTypeSelector';
import { mapApiToQuizQuestion } from '../utils/questionMappers';
import { ReviewQueuePanel } from '../components/LearningPath/ReviewQueuePanel';
<<<<<<< Updated upstream
import { ErrorClusterCard } from '../components/Quiz/ErrorClusterCard';
import { ProductiveFailureFlow } from '../components/LearningPath/ProductiveFailureFlow';
import { LeaguePanel } from '../components/LearningPath/LeaguePanel';
import { StudyPlannerWidget } from '../components/LearningPath/StudyPlannerWidget';
import { DuelMode } from '../components/LearningPath/DuelMode';
=======
import { AdaptiveFeedbackPanel } from '../components/LearningPath/AdaptiveFeedbackPanel';
import { ProgressDashboard } from '../components/LearningPath/Page/ProgressDashboard';
import { StudyPlannerWidget } from '../components/LearningPath/StudyPlannerWidget';
import { AccessibilitySettings } from '../components/LearningPath/AccessibilitySettings';
import { SkillGraphView } from '../components/LearningPath/SkillGraphView';
import { ProductiveFailureFlow } from '../components/LearningPath/ProductiveFailureFlow';
import { LeaguePanel } from '../components/LearningPath/LeaguePanel';
import { ProactiveCoachWidget } from '../components/LearningPath/ProactiveCoachWidget';
import { SuccessAnimation } from '../components/ADHD/InstantFeedback/SuccessAnimation';
import { StreakTracker } from '../components/ADHD/InstantFeedback/StreakTracker';
>>>>>>> Stashed changes
import { useLearningPath } from '../hooks/useLearningPath';
import { useLearningPathVideos } from '../hooks/useLearningPathVideos';

import modernColors from '../theme/modern-colors';

// Types
// import { generateConnections } from '../utils/learningPathHelpers';
import { turkishLowerCase } from '../utils/turkishUtils';

// Lazy-loaded tab content components

interface TabPanelProps {
  children?: React.ReactNode
  index: number
  value: number
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`modern-learning-path-tabpanel-${index}`}
      aria-labelledby={`modern-learning-path-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

/**
 * Modern Learning Path Page
 */
export function ModernLearningPathPage() {
  // ========================================
  // Custom hooks for business logic
  // ========================================
  const {
    pathNodes,
    learningStyle,
    currentNodeId: _currentNodeId,
    loading,
    error,
    needsOnboarding,
    reload,
    setCurrentNode,
    submitOnboardingResult,
    skipOnboarding,
    markNodeComplete,
    updateProgress,
    studentId,
<<<<<<< Updated upstream
    selectedSubject,
    changeSubject,
    setError,
=======
    studySession,
    streak,
    startSession,
    endSession,
>>>>>>> Stashed changes
  } = useLearningPath();

  const {
    videos,
    videosLoading,
    loadVideosForPath,
    loadVideosForNode,
  } = useLearningPathVideos();

  // ========================================
  // Local UI state
  // ========================================
  const [tabValue, setTabValue] = useState(0);
<<<<<<< Updated upstream
  const dungeonSubject = selectedSubject?.toUpperCase() || 'MATEMATIK';
=======
  const [pathViewMode, setPathViewMode] = useState<'linear' | 'graph'>('linear');
>>>>>>> Stashed changes
  const [showNodeDetails, setShowNodeDetails] = useState(false);
  const [selectedNode, setSelectedNode] = useState<PathNodeData | null>(null);
  const [interleavedQuestions, setInterleavedQuestions] = useState<Question[] | null>(null);
  const [nodeQuizQuestions, setNodeQuizQuestions] = useState<Question[] | null>(null);
  const [activeQuizNode, setActiveQuizNode] = useState<PathNodeData | null>(null);
  const [productiveFailureActive, setProductiveFailureActive] = useState(false);

  // A1: Milestone celebration
  const [celebration, setCelebration] = useState<{ visible: boolean; type: 'correct' | 'streak' | 'achievement' | 'levelup'; message: string }>({
    visible: false, type: 'correct', message: '',
  });

  // Faz 4: Adaptive feedback after quiz
  const [feedbackData, setFeedbackData] = useState<{
    visible: boolean;
    score: number;
    total: number;
    correct: number;
    passed: boolean;
  }>({ visible: false, score: 0, total: 0, correct: 0, passed: false });

  // A4: Quiz streak tracker
  const [quizStreak, setQuizStreak] = useState(0);
  const [bestStreak, setBestStreak] = useState(0);
  useEffect(() => {
    if (!studentId) return;
    try {
      const stored = parseInt(localStorage.getItem(`lp_best_streak_${studentId}`) || '0', 10);
      setBestStreak(stored);
    } catch { /* ignore */ }
  }, [studentId]);

  // B1: Elapsed timer for active session
  const [elapsedMinutes, setElapsedMinutes] = useState(0);
  useEffect(() => {
    if (!studySession.isActive || !studySession.startedAt) {
      setElapsedMinutes(0);
      return;
    }
    const tick = () => {
      const diff = Math.floor((Date.now() - studySession.startedAt!.getTime()) / 60000);
      setElapsedMinutes(diff);
    };
    tick();
    const interval = setInterval(tick, 60000);
    return () => clearInterval(interval);
  }, [studySession.isActive, studySession.startedAt]);

  // Quiz loading/error states
  const [quizLoading, setQuizLoading] = useState(false);
  const [quizError, setQuizError] = useState<string | null>(null);
  const [interleavedLoading, setInterleavedLoading] = useState(false);

  // F8: Collect error type selections during quiz (ref to avoid re-renders)
  const errorTypesRef = useRef<Record<string, ErrorType>>({});

  // F9: Productive failure pretest state
  const [pretestNode, setPretestNode] = useState<PathNodeData | null>(null);

  // F15: Last completed quiz subject for error cluster card
  const [lastQuizSubject, setLastQuizSubject] = useState<string | null>(null);

  // F16: Duel mode dialog
  const [showDuel, setShowDuel] = useState(false);

  // Subject status from /status endpoint (theta, zpd_zone, prereq info)
  interface SubjectStatusInfo {
    subject: string; theta: number; mastery_pct: number; level_label: string;
    theta_se?: number; zpd_zone?: string; prereq_blocked?: boolean; prereq_topic_name?: string;
  }
  const [subjectStatuses, setSubjectStatuses] = useState<SubjectStatusInfo[]>([]);

  // ========================================
  // Effects
  // ========================================

  /**
   * Fetch subject statuses (theta, zpd_zone, prereq) from Daily API
   */
  useEffect(() => {
    // F-06: AbortController ile unmount cleanup
    const controller = new AbortController();
    fetch('/api/v1/learning-path/status', { credentials: 'include', signal: controller.signal })
      .then(r => r.ok ? r.json() : [])
      .then(data => { if (Array.isArray(data)) setSubjectStatuses(data); })
      .catch(() => { /* silent — LP page works without status data */ });
    return () => controller.abort();
  }, []);

  /**
   * Load videos when path is ready
   */
  useEffect(() => {
    if (pathNodes.length > 0 && learningStyle) {
      const path = { modules: [{ title: selectedSubject }] };
      loadVideosForPath(path, learningStyle, selectedSubject);
    }
  }, [pathNodes, learningStyle, selectedSubject, loadVideosForPath]);

  // ========================================
  // Event handlers
  // ========================================

  /**
   * Handle node click in path visualizer
   */
  const handleNodeClick = useCallback(
    async (node: PathNodeData) => {
      setCurrentNode(node.id);
      setSelectedNode(node);
      setShowNodeDetails(true);
      await loadVideosForNode(
        node.id,
        node.title,
        node.description,
        node.difficulty,
        learningStyle,
      );
    },
    [setCurrentNode, loadVideosForNode, learningStyle],
  );

  const handleDungeonNodeClick = useCallback((node: LayoutNode) => {
    // Bridge dungeon node to existing node click handler
    handleNodeClick({
      id: node.topic_id,
      title: node.name_tr,
      description: node.name_tr || node.code,
      status: node.progress.completed ? 'completed' : node.progress.attempt_count > 0 ? 'in_progress' : 'locked',
      difficulty: 'medium',
    } as unknown as PathNodeData);
  }, [handleNodeClick]);

  /**
   * Handle video play
   */
  const handleVideoPlay = useCallback((video: VideoResponse) => {
    window.open(video.url, '_blank');
  }, []);

  /**
   * Handle close node details
   */
  const handleCloseDetails = useCallback(() => {
    setShowNodeDetails(false);
  }, []);

  /**
   * Handle start quiz from NodeDetailsPanel
   * F9: If node is new (available), show Productive Failure pretest first.
   * Otherwise, fetch quiz questions directly.
   */

  // Subject extraction: match known YKS subjects from node title
  const SUBJECT_KEYWORDS: Record<string, string> = {
    'matematik': 'matematik', 'fizik': 'fizik', 'kimya': 'kimya',
    'biyoloji': 'biyoloji', 'türkçe': 'turkce', 'tarih': 'tarih',
    'geometri': 'geometri', 'coğrafya': 'cografya', 'edebiyat': 'edebiyat',
    'felsefe': 'felsefe',
  };

  const extractSubject = useCallback((title: string): string => {
    const words = turkishLowerCase(title.normalize('NFC')).split(/\s+/);
    for (const word of words) {
      if (SUBJECT_KEYWORDS[word]) return SUBJECT_KEYWORDS[word];
    }
    // Fallback: first word (original behavior)
    return words[0] || 'matematik';
  }, []);

  const handleStartQuiz = useCallback(async (node: PathNodeData) => {
    // F9: Productive Failure — show pretest before new topic
    if (node.status === 'available' && !pretestNode) {
      setPretestNode(node);
      setShowNodeDetails(false);
      return;
    }

    // Her zaman selectedSubject kullan (ders bazlı doğru filtreleme)
    const subject = selectedSubject;

    // node.title doğrudan konu adı (örn: "Türev") - split gerekmez
    const topic = node.title || null;

    setQuizLoading(true);
    setQuizError(null);
    try {
      // Konu parametresini API'ye gönder
      const topicParam = topic ? `&topic=${encodeURIComponent(topic)}` : '';
      const url = `/api/v1/learning-path/exit-quiz/${encodeURIComponent(subject)}?count=${node.quiz?.question_count || 5}${topicParam}`;
      const res = await fetch(url, { credentials: 'include' });
      const data = await res.json();

      if (data.success && data.questions?.length > 0) {
        setNodeQuizQuestions(data.questions.map(mapApiToQuizQuestion));
        setActiveQuizNode(node);
        setShowNodeDetails(false);
        setLastQuizSubject(subject);
      } else {
        setQuizError('Bu konu için soru bulunamadı.');
      }
    } catch (err) {
      console.error('Quiz soruları yüklenemedi:', err);
      setQuizError('Quiz soruları yüklenemedi. Lütfen tekrar deneyin.');
    } finally {
      setQuizLoading(false);
    }
  }, [pretestNode, selectedSubject]);

  /** Start productive failure flow — same fetch, different UI mode */
  const handleStartProductiveFailure = useCallback(async (node: PathNodeData) => {
    const subject = node.title.split(' ')[0];
    try {
      const res = await fetch(
        `/api/learning-path/exit-quiz/${encodeURIComponent(subject)}?count=${node.quiz?.question_count || 5}`,
        { credentials: 'include' },
      );
      const data = await res.json();
      if (data.success && data.questions?.length > 0) {
        setNodeQuizQuestions(data.questions.map(mapApiToQuizQuestion));
        setActiveQuizNode(node);
        setProductiveFailureActive(true);
        setShowNodeDetails(false);
      }
    } catch (err) {
      console.error('Productive failure soruları yüklenemedi:', err);
    }
  }, []);

  /**
   * Handle quiz completion — register wrong answers to FSRS + update node progress
   */
  const handleQuizComplete = useCallback(async (results: { score: number; totalScore: number; percentage: number; answers: Record<string, any>; correctCount: number; incorrectCount: number; isTimeout?: boolean }) => {
    // Guard: Ensure studentId is available
    if (!studentId) {
      console.error('Quiz complete failed: studentId is null');
      setError('Profil bulunamadi. Lutfen sayfayi yenileyin.');
      return;
    }

    // Helper: Retry fetch with exponential backoff
    const fetchWithRetry = async (url: string, options: RequestInit, retries = 3): Promise<Response> => {
      for (let i = 0; i < retries; i++) {
        try {
          const res = await fetch(url, options);
          if (res.ok) return res;
          // Server error - retry
          if (res.status >= 500) {
            await new Promise(r => setTimeout(r, 1000 * (i + 1))); // 1s, 2s, 3s
            continue;
          }
          return res; // Client error - don't retry
        } catch (err) {
          if (i < retries - 1) {
            await new Promise(r => setTimeout(r, 1000 * (i + 1)));
            continue;
          }
          throw err;
        }
      }
      throw new Error('Max retries exceeded');
    };

    // 1. Find wrong answer question IDs
    const questions = nodeQuizQuestions || [];
    const wrongIds = questions
      .filter(q => {
        const userAnswer = results.answers[q.id];
        return userAnswer !== q.correctAnswer;
      })
      .map(q => q.id);

    // 2. Register wrong answers to FSRS (with F8 error types if available) - with retry
    if (wrongIds.length > 0) {
      try {
        const errorTypes = Object.keys(errorTypesRef.current).length > 0
          ? errorTypesRef.current
          : undefined;
        const response = await fetchWithRetry('/api/v1/learning-path/register-wrong-answers', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({ question_ids: wrongIds, error_types: errorTypes, is_timeout: results.isTimeout }),
        });
        await response.json().catch(() => ({}));
      } catch (err: any) {
        console.error('FSRS kaydi basarisiz (retry dahil):', err);
        // Don't block quiz completion for FSRS errors - continue
      }
    }

    // 3. Update node progress + A1 celebration
    const passed = results.percentage >= (activeQuizNode?.quiz?.passing_score || 60);
    if (activeQuizNode) {
<<<<<<< Updated upstream
      const passed = results.percentage >= (activeQuizNode.quiz?.passing_score || 60);
      try {
        const result = passed
          ? await markNodeComplete(activeQuizNode.id)
          : await updateProgress({ nodeId: activeQuizNode.id, progress: results.percentage });

        if (result?.allCompleted) {
          window.alert('Tebrikler! Bu konudaki tum adimlari tamamladiniz!');
        }
      } catch (err: any) {
        console.error('Node progress guncelleme hatasi:', err);
        setError(err.message || 'Node progress guncellenemedi');
      }
    }

    // 4. Gamification points: backend on_quiz_completed() handles XP award automatically
    // (removed duplicate frontend XP call — was causing double XP)

    // 5. Show timeout warning if applicable
    if (results.isTimeout) {
      console.warn('Quiz süre dolduğu için sonlandırıldı');
    }

    // 6. Reset error types (quiz UI closes when user clicks exit in results screen)
    errorTypesRef.current = {};
=======
      if (passed) {
        await markNodeComplete(activeQuizNode.id);
        // A1: Milestone kutlama
        setCelebration({
          visible: true,
          type: 'achievement',
          message: `${activeQuizNode.title} tamamlandı!`,
        });
      } else {
        await updateProgress({ nodeId: activeQuizNode.id, progress: results.percentage });
      }
    }

    // A4: Quiz streak hesapla (ardışık doğru cevap sayısı)
    const answers = results.answers || {};
    const orderedQuestions = nodeQuizQuestions || [];
    let currentRun = 0;
    let maxRun = 0;
    for (const q of orderedQuestions) {
      if (answers[q.id] === q.correctAnswer) {
        currentRun++;
        maxRun = Math.max(maxRun, currentRun);
      } else {
        currentRun = 0;
      }
    }
    setQuizStreak(maxRun);
    if (maxRun > bestStreak) {
      setBestStreak(maxRun);
      try { localStorage.setItem(`lp_best_streak_${studentId}`, String(maxRun)); } catch {}
    }

    // 4. Award gamification points
    if (studentId) {
      const points = results.correctCount * 10 + (passed ? 50 : 0);
      if (points > 0) {
        fetch(`/api/v1/gamification/points/award?points=${points}&reason=quiz_complete`, {
          method: 'POST',
          credentials: 'include',
        }).catch(err => console.error('Gamification puan hatası:', err));
      }
    }

    // 5. Show adaptive feedback
    setFeedbackData({
      visible: true,
      score: results.percentage,
      total: questions.length,
      correct: results.correctCount,
      passed,
    });

    // 6. Close quiz
    setNodeQuizQuestions(null);
    setActiveQuizNode(null);
>>>>>>> Stashed changes
  }, [nodeQuizQuestions, activeQuizNode, markNodeComplete, updateProgress, studentId]);

  /**
   * F8: Handle error type selection during immediate feedback.
   * Stores selections in ref; sent with register-wrong-answers on quiz completion.
   */
  const handleErrorTypeSelect = useCallback((questionId: string, errorType: ErrorType) => {
    errorTypesRef.current[questionId] = errorType;
  }, []);

  /**
   * Quiz exit with confirmation
   */
  const handleQuizExit = useCallback((submitted?: boolean) => {
    if (submitted || window.confirm('Quiz\'den çıkmak istediğinize emin misiniz? İlerlemeniz kaydedilmeyecek.')) {
      errorTypesRef.current = {};
      setNodeQuizQuestions(null);
      setActiveQuizNode(null);
    }
  }, []);

  const handleInterleavedExit = useCallback((submitted?: boolean) => {
    if (submitted || window.confirm('Quiz\'den çıkmak istediğinize emin misiniz? İlerlemeniz kaydedilmeyecek.')) {
      errorTypesRef.current = {};
      setInterleavedQuestions(null);
    }
  }, []);

  /**
   * Start interleaved practice with loading state
   */
  const handleStartInterleaved = useCallback(async () => {
    // Use selectedSubject as primary; extractSubject from node titles as additional variety
    const topicSubjects = [...new Set(pathNodes.map(n => extractSubject(n.title)))];
    const subjects = [selectedSubject, ...topicSubjects.filter(s => s !== selectedSubject)].slice(0, 5);
    setInterleavedLoading(true);
    setQuizError(null);
    try {
      // Cache-bust: ?_t=Date.now() + Cache-Control: no-cache
      // Backend middleware'i cache-control: private, max-age=300 set ediyor
      // → reject edilen sorular cached response'da kalıyor. Bypass et.
      const res = await fetch(
        `/api/v1/learning-path/interleaved-practice?subjects=${subjects.join(',')}&count=10&_t=${Date.now()}`,
        { credentials: 'include', headers: { 'Cache-Control': 'no-cache' } },
      );
      const data = await res.json();
      if (data.success && data.questions?.length > 0) {
        setInterleavedQuestions(data.questions.map(mapApiToQuizQuestion));
      } else {
        setQuizError('Karışık pratik soruları bulunamadı.');
      }
    } catch (err) {
      console.error('Karışık pratik yüklenemedi:', err);
      setQuizError('Karışık pratik yüklenemedi. Lütfen tekrar deneyin.');
    } finally {
      setInterleavedLoading(false);
    }
  }, [pathNodes, extractSubject, selectedSubject]);

  /**
   * Tab change with quiz guard
   */
  const handleTabChange = useCallback((_: unknown, newValue: number) => {
    if (nodeQuizQuestions || interleavedQuestions) return;
    setTabValue(newValue);
  }, [nodeQuizQuestions, interleavedQuestions]);

  // ========================================
  // Memoized values
  // ========================================

  /**
   * Check if path exists
   */
  const hasPath = useMemo(
    () => pathNodes.length > 0,
    [pathNodes.length],
  );

  // Replaced by DungeonMap — DAG edges come from backend now
  // const pathConnections = useMemo(
  //   () => generateConnections(pathNodes),
  //   [pathNodes],
  // );

  /**
   * A2: Daily plan — current + next 2 available nodes
   */
  const dailyPlan = useMemo(() => {
    const currentNode = pathNodes.find(n => n.status === 'current');
    const availableNodes = pathNodes.filter(n => n.status === 'available');
    const suggested = [currentNode, ...availableNodes.slice(0, 2)].filter(Boolean) as PathNodeData[];

    // Parse estimated time (e.g. "30 dk" → 30)
    const totalMinutes = suggested.reduce((sum, n) => {
      const match = n.estimatedTime?.match(/(\d+)/);
      return sum + (match ? parseInt(match[1], 10) : 20);
    }, 0);

    return { nodes: suggested, totalMinutes };
  }, [pathNodes]);

  // progressStats moved to ProgressDashboard (A5)

  // ========================================
  // Render states
  // ========================================

  // Loading state
  if (loading) {
    return (
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: modernColors.gradients.mesh,
        }}
      >
        <ModernLoader message="Öğrenme yolunuz yükleniyor..." size="large" />
      </Box>
    );
  }

  // Onboarding state — show AI-guided wizard before creating path
  if (needsOnboarding) {
    return (
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: modernColors.gradients.mesh,
          p: 2,
        }}
      >
        <Container maxWidth="sm">
          <OnboardingWizard
            studentId={studentId || ''}
            onComplete={submitOnboardingResult}
            onSkip={skipOnboarding}
          />
        </Container>
      </Box>
    );
  }

  // Error state — show subject selector so user can switch to a different subject
  if (error) {
    return (
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: modernColors.gradients.mesh,
          p: 2,
        }}
      >
        <Container maxWidth="sm">
          <Box sx={{ mb: 2, overflowX: 'auto', pb: 1, display: 'flex', justifyContent: 'center' }}>
            <ToggleButtonGroup
              value={selectedSubject}
              exclusive
              onChange={(_e, val) => { if (val) changeSubject(val); }}
              size="small"
              sx={{
                '& .MuiToggleButton-root': {
                  textTransform: 'none', fontWeight: 600,
                  borderRadius: '20px !important', px: 1.5, py: 0.5,
                  border: '1px solid rgba(59,130,246,0.3)',
                  '&.Mui-selected': {
                    background: modernColors.gradients.primary,
                    color: '#fff', borderColor: 'transparent',
                  },
                },
              }}
            >
              {[
                { value: 'matematik', label: 'Mat' },
                { value: 'fizik', label: 'Fiz' },
                { value: 'kimya', label: 'Kim' },
                { value: 'biyoloji', label: 'Bio' },
                { value: 'turkce', label: 'Tur' },
                { value: 'tarih', label: 'Tar' },
                { value: 'geometri', label: 'Geo' },
                { value: 'cografya', label: 'Cog' },
                { value: 'edebiyat', label: 'Ede' },
              ].map(s => (
                <ToggleButton key={s.value} value={s.value}>{s.label}</ToggleButton>
              ))}
            </ToggleButtonGroup>
          </Box>
          <GlassCard glassIntensity="medium" elevated>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="h5" sx={{ fontWeight: 700, mb: 2, color: 'error.main' }}>
                Hata Oluştu
              </Typography>
              <Typography variant="body1" sx={{ mb: 3 }}>
                {error}
              </Typography>
              <ModernButton
                variant="gradient"
                gradient={modernColors.gradients.primary}
                icon={<Refresh />}
                onClick={reload}
              >
                Tekrar Dene
              </ModernButton>
            </Box>
          </GlassCard>
        </Container>
      </Box>
    );
  }

  // Main render
  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: `linear-gradient(180deg, ${modernColors.primary[50]} 0%, ${modernColors.background.default} 40%, #fff 100%)`,
        py: 4,
      }}
    >
      {/* A1: Milestone Kutlama */}
      <SuccessAnimation
        isVisible={celebration.visible}
        type={celebration.type}
        message={celebration.message}
        onComplete={() => setCelebration(prev => ({ ...prev, visible: false }))}
        showConfetti
      />

      <Container maxWidth="xl">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <Box sx={{ mb: 4 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Box
                  sx={{
                    width: 56,
                    height: 56,
                    borderRadius: 3,
                    background: modernColors.gradients.primary,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <Timeline sx={{ fontSize: 32, color: 'white' }} />
                </Box>
                <Box>
                  <Typography
                    variant="h3"
                    sx={{
                      fontWeight: 900,
                      color: modernColors.text.dark,
                    }}
                  >
                    Öğrenme Yolunuz
                  </Typography>
                  <Typography variant="body1" sx={{ color: modernColors.text.secondary }}>
                    Kişiselleştirilmiş öğrenme yolunuz ve size özel kaynaklar
                  </Typography>
                </Box>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                {/* League badge */}
                <LeaguePanel compact />

                {/* B2: Streak badge */}
                {streak.dailyStreak > 0 && (
                  <Chip
                    icon={<LocalFireDepartment sx={{ color: '#f97316' }} />}
                    label={`${streak.dailyStreak} gün`}
                    variant="outlined"
                    sx={{ fontWeight: 700, borderColor: '#f97316', color: '#f97316' }}
                  />
                )}

                {/* B1: Session timer button */}
                {studySession.isActive ? (
                  <ModernButton
                    variant="gradient"
                    gradient="linear-gradient(135deg, #ef4444, #dc2626)"
                    icon={<Stop />}
                    onClick={() => endSession()}
                  >
                    <Timer sx={{ fontSize: 16, mr: 0.5 }} />
                    {elapsedMinutes} dk — Bitir
                  </ModernButton>
                ) : (
                  <ModernButton
                    variant="gradient"
                    gradient={modernColors.gradients.success}
                    icon={<PlayArrow />}
                    onClick={startSession}
                  >
                    Oturum Başlat
                  </ModernButton>
                )}

                <AccessibilitySettings />

                <ModernButton
                  variant="glass"
                  icon={<Refresh />}
                  onClick={reload}
                >
                  Yenile
                </ModernButton>
              </Box>
            </Box>

            {/* Learning Style Badge */}
            {learningStyle && (
              <GlassCard
                glassIntensity="light"
                hoverable
                gradient={modernColors.gradients.sunset}
                sx={{ display: 'inline-block' }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <AutoAwesome sx={{ fontSize: 20 }} />
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    İçerik Tercihiniz: {
                      {
                        visual: 'Görsel Öğrenen',
                        auditory: 'İşitsel Öğrenen',
                        reading: 'Okuma-Yazma Öğrenen',
                        kinesthetic: 'Uygulamalı Öğrenen',
                        mixed: 'Karma Öğrenen',
                      }[learningStyle] || learningStyle
                    }
                  </Typography>
                </Box>
              </GlassCard>
            )}

            {/* Subject Selector — disabled during active quiz to prevent state corruption */}
            <Box sx={{ mt: 2, overflowX: 'auto', pb: 1 }}>
              <ToggleButtonGroup
                value={selectedSubject}
                exclusive
                onChange={(_e, val) => { if (val) changeSubject(val); }}
                size="small"
                disabled={!!(nodeQuizQuestions || interleavedQuestions || pretestNode)}
                sx={{
                  flexWrap: 'nowrap',
                  '& .MuiToggleButton-root': {
                    textTransform: 'none',
                    fontWeight: 600,
                    borderRadius: '20px !important',
                    px: 2,
                    py: 0.5,
                    border: '1px solid rgba(59,130,246,0.3)',
                    '&.Mui-selected': {
                      background: modernColors.gradients.primary,
                      color: '#fff',
                      borderColor: 'transparent',
                      '&:hover': { background: modernColors.gradients.primary, opacity: 0.9 },
                    },
                  },
                }}
              >
                {[
                  { value: 'matematik', label: 'Matematik' },
                  { value: 'fizik', label: 'Fizik' },
                  { value: 'kimya', label: 'Kimya' },
                  { value: 'biyoloji', label: 'Biyoloji' },
                  { value: 'turkce', label: 'Turkce' },
                  { value: 'tarih', label: 'Tarih' },
                  { value: 'geometri', label: 'Geometri' },
                  { value: 'cografya', label: 'Cografya' },
                  { value: 'edebiyat', label: 'Edebiyat' },
                ].map(s => {
                  const st = subjectStatuses.find(ss => ss.subject.toLowerCase() === s.value);
                  return (
                    <ToggleButton key={s.value} value={s.value} sx={{ flexDirection: 'column', lineHeight: 1.2 }}>
                      <span>{s.label}</span>
                      {st && (
                        <span style={{ fontSize: 9, opacity: 0.8, fontWeight: 400 }}>
                          θ{st.theta.toFixed(1)} · {st.mastery_pct.toFixed(0)}%
                        </span>
                      )}
                    </ToggleButton>
                  );
                })}
              </ToggleButtonGroup>
            </Box>

            {/* Prereq warning for selected subject */}
            {(() => {
              const st = subjectStatuses.find(ss => ss.subject.toLowerCase() === selectedSubject);
              if (st?.prereq_blocked && st.prereq_topic_name) {
                return (
                  <Alert severity="warning" sx={{ mt: 1 }}>
                    Bu konuyu başlatmak için önce <strong>{st.prereq_topic_name}</strong> tamamlanmalı.
                  </Alert>
                );
              }
              return null;
            })()}
          </Box>
        </motion.div>

        {/* Tabs */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          <GlassCard glassIntensity="medium" elevated>
            <Tabs
              value={tabValue}
              onChange={handleTabChange}
              variant="fullWidth"
              sx={{
                borderBottom: 1,
                borderColor: 'divider',
                '& .MuiTab-root': {
                  fontWeight: 600,
                  fontSize: 16,
                  textTransform: 'none',
                  minHeight: 64,
                },
                '& .Mui-selected': {
                  color: '#3b82f6',
                },
                '& .MuiTabs-indicator': {
                  background: modernColors.gradients.primary,
                  height: 3,
                  borderRadius: '3px 3px 0 0',
                },
              }}
            >
              <Tab icon={<Timeline />} label="Yol Haritası" iconPosition="start" />
              <Tab icon={<VideoLibrary />} label="Size Özel Kaynaklar" iconPosition="start" />
              <Tab icon={<Assessment />} label="İlerleme Takibi" iconPosition="start" />
            </Tabs>

            {/* Tab 1: Path Visualization */}
            <TabPanel value={tabValue} index={0}>
              <AnimatePresence mode="wait">
                <motion.div
                  key="visualization"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  transition={{ duration: 0.3 }}
                >
                  {/* Proaktif AI Koçluk — davranışsal sinyal bazlı öneriler */}
                  {!nodeQuizQuestions && !interleavedQuestions && (
                    <ProactiveCoachWidget />
                  )}

                  {/* A2: Günlük Çalışma Planı */}
                  {!nodeQuizQuestions && !interleavedQuestions && dailyPlan.nodes.length > 0 && (
                    <GlassCard glassIntensity="light" sx={{ mb: 3 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2 }}>
                        <CalendarToday sx={{ color: '#3b82f6' }} />
                        <Typography variant="h6" sx={{ fontWeight: 700 }}>
                          Bugünün Planı
                        </Typography>
                        <Chip
                          label={`~${dailyPlan.totalMinutes} dk`}
                          size="small"
                          sx={{ ml: 'auto', fontWeight: 600, backgroundColor: 'rgba(59, 130, 246, 0.1)', color: '#3b82f6' }}
                        />
                      </Box>
                      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                        {dailyPlan.nodes.map((node, i) => (
                          <Box
                            key={node.id}
                            onClick={() => handleNodeClick(node)}
                            sx={{
                              display: 'flex', alignItems: 'center', gap: 1.5, p: 1.5, borderRadius: 2,
                              cursor: 'pointer', transition: 'background 0.2s',
                              backgroundColor: i === 0 ? 'rgba(59, 130, 246, 0.08)' : 'transparent',
                              '&:hover': { backgroundColor: 'rgba(59, 130, 246, 0.12)' },
                            }}
                          >
                            <Box sx={{
                              width: 28, height: 28, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center',
                              backgroundColor: i === 0 ? '#3b82f6' : 'rgba(0,0,0,0.08)', color: i === 0 ? 'white' : 'text.secondary',
                              fontWeight: 700, fontSize: 14,
                            }}>
                              {i + 1}
                            </Box>
                            <Box sx={{ flex: 1, minWidth: 0 }}>
                              <Typography variant="body2" sx={{ fontWeight: 600 }} noWrap>{node.title}</Typography>
                              <Typography variant="caption" color="text.secondary">{node.estimatedTime} · {node.difficulty}</Typography>
                            </Box>
                            {node.status === 'current' && (
                              <Chip label="Devam" size="small" color="primary" variant="outlined" />
                            )}
                          </Box>
                        ))}
                      </Box>
                    </GlassCard>
                  )}

                  {/* Faz 4: Adaptive Feedback — quiz sonrası göster */}
                  {feedbackData.visible && (
                    <Box sx={{ mb: 3 }}>
                      <AdaptiveFeedbackPanel
                        quizScore={feedbackData.score}
                        totalQuestions={feedbackData.total}
                        correctCount={feedbackData.correct}
                        passed={feedbackData.passed}
                        onClose={() => setFeedbackData(prev => ({ ...prev, visible: false }))}
                        onAdaptPath={reload}
                      />
                    </Box>
                  )}

                  {/* FSRS Tekrar Paneli — due kartlar varsa göster */}
                  {!nodeQuizQuestions && !interleavedQuestions && !pretestNode && (
                    <ReviewQueuePanel />
                  )}

                  {/* Quiz/Interleaved error message */}
                  {quizError && (
                    <Alert severity="error" onClose={() => setQuizError(null)} sx={{ mb: 2 }}>
                      {quizError}
                    </Alert>
                  )}

                  {/* Quiz loading indicator */}
                  {quizLoading && (
                    <Box sx={{ display: 'flex', justifyContent: 'center', py: 3 }}>
                      <ModernLoader message="Quiz soruları yükleniyor..." />
                    </Box>
                  )}

                  {/* F9: Productive Failure Pretest */}
                  {pretestNode && (
                    <Box sx={{ mb: 3 }}>
                      <ProductiveFailureFlow
                        topic={pretestNode.title}
                        onComplete={() => {
                          // After pretest, start the actual quiz directly (skip pretest check)
                          const node = { ...pretestNode, status: 'current' as const };
                          setPretestNode(null);
                          handleStartQuiz(node);
                        }}
                        onSkip={() => {
                          const node = { ...pretestNode, status: 'current' as const };
                          setPretestNode(null);
                          handleStartQuiz(node);
                        }}
                      />
                    </Box>
                  )}

                  {/* F15: Error Cluster Recommendations — after quiz completion */}
                  {lastQuizSubject && !nodeQuizQuestions && !interleavedQuestions && !pretestNode && (
                    <ErrorClusterCard
                      subject={lastQuizSubject}
                      onNavigateToTopic={(topic) => {
                        // Find the node with this topic and navigate to it
                        const targetNode = pathNodes.find(n => extractSubject(n.title) === extractSubject(topic));
                        if (targetNode) handleNodeClick(targetNode);
                      }}
                    />
                  )}

                  {/* Node Quiz — node'dan başlatılan quiz */}
                  {nodeQuizQuestions && activeQuizNode && (
                    <Box sx={{ mb: 3 }}>
<<<<<<< Updated upstream
                      <QuizInterface
                        config={{
                          title: `${activeQuizNode.title} Quiz`,
                          description: `${activeQuizNode.title} konusunu test et`,
                          questions: nodeQuizQuestions,
                          passingScore: activeQuizNode.quiz?.passing_score || 60,
                          immediateFeedback: true,
                          showCorrectAnswers: true,
                        }}
                        onSubmit={handleQuizComplete}
                        onExit={handleQuizExit}
                        onErrorTypeSelect={handleErrorTypeSelect}
                      />
=======
                      {productiveFailureActive ? (
                        /* "Çöz-Sonra-Gör" productive failure mode */
                        <ProductiveFailureFlow
                          config={{
                            title: `${activeQuizNode.title} Quiz`,
                            description: `${activeQuizNode.title} konusunu test et`,
                            questions: nodeQuizQuestions,
                            passingScore: activeQuizNode.quiz?.passing_score || 60,
                          }}
                          nodeTitle={activeQuizNode.title}
                          onComplete={() => {}}
                          onExit={() => {
                            setNodeQuizQuestions(null);
                            setActiveQuizNode(null);
                            setProductiveFailureActive(false);
                          }}
                        />
                      ) : (
                        <>
                          {/* A4: Quiz streak tracker */}
                          {quizStreak > 0 && (
                            <Box sx={{ mb: 2 }}>
                              <StreakTracker currentStreak={quizStreak} bestStreak={bestStreak} position="top-right" />
                            </Box>
                          )}
                          <QuizInterface
                            config={{
                              title: `${activeQuizNode.title} Quiz`,
                              description: `${activeQuizNode.title} konusunu test et`,
                              questions: nodeQuizQuestions,
                              passingScore: activeQuizNode.quiz?.passing_score || 60,
                              immediateFeedback: true,
                              showCorrectAnswers: true,
                            }}
                            onSubmit={handleQuizComplete}
                            onExit={() => { setNodeQuizQuestions(null); setActiveQuizNode(null); }}
                          />
                        </>
                      )}
>>>>>>> Stashed changes
                    </Box>
                  )}

                  {/* Karışık Pratik QuizInterface — sorular yüklendiğinde göster */}
                  {interleavedQuestions && (
                    <Box sx={{ mb: 3 }}>
                      <QuizInterface
                        config={{
                          title: 'Karışık Pratik',
                          description: 'Farklı konulardan karışık sorularla çalış',
                          questions: interleavedQuestions,
                          passingScore: 60,
                          immediateFeedback: true,
                          showCorrectAnswers: true,
                        }}
                        onSubmit={async (results) => {
                          const wrongIds = interleavedQuestions
                            .filter(q => results.answers[q.id] !== q.correctAnswer)
                            .map(q => q.id);
                          if (wrongIds.length > 0) {
                            try {
                              const errorTypes = Object.keys(errorTypesRef.current).length > 0
                                ? errorTypesRef.current
                                : undefined;
                              await fetch('/api/v1/learning-path/register-wrong-answers', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                credentials: 'include',
                                body: JSON.stringify({ question_ids: wrongIds, error_types: errorTypes }),
                              });
                            } catch (err) {
                              console.error('FSRS kaydi basarisiz:', err);
                            }
                          }
                          // Interleaved: tek kaynak FE award (LP quiz submit = backend on_quiz_completed)
                          if (studentId) {
                            const raw =
                              results.correctCount * 10 + (results.percentage >= 60 ? 50 : 0);
                            const points = Math.min(100, Math.max(0, raw));
                            if (points > 0) {
                              try {
                                await fetch('/api/v1/gamification/points/award', {
                                  method: 'POST',
                                  credentials: 'include',
                                  headers: { 'Content-Type': 'application/json' },
                                  body: JSON.stringify({
                                    points,
                                    reason: 'interleaved_practice',
                                  }),
                                });
                              } catch (err) {
                                console.error('Gamification puan hatasi:', err);
                              }
                            }
                          }
                          errorTypesRef.current = {};
                        }}
                        onExit={handleInterleavedExit}
                        onErrorTypeSelect={handleErrorTypeSelect}
                      />
                    </Box>
                  )}

                  {/* Karışık Pratik Kartı — Interleaving d=1.21 */}
                  {hasPath && !interleavedQuestions && (
                    <Alert
                      severity="info"
                      icon={<Shuffle />}
                      sx={{ mb: 3, borderRadius: 2 }}
                      action={
                        <ModernButton
                          variant="glass"
                          icon={<Science />}
                          onClick={handleStartInterleaved}
                          disabled={interleavedLoading}
                        >
                          {interleavedLoading ? 'Yükleniyor...' : 'Karışık Pratik'}
                        </ModernButton>
                      }
                    >
                      <Box>
                        <Typography variant="subtitle2" fontWeight={700}>
                          Karışık Pratik Modu
                        </Typography>
                        <Typography variant="body2">
                          Farklı konulardan karışık sorularla çalış. Araştırmalar bu yöntemin %74 daha iyi sonuç verdiğini gösteriyor.
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 0.5, mt: 1, flexWrap: 'wrap' }}>
                          {[...new Set(pathNodes.map(n => n.title.split(' ')[0]))].slice(0, 5).map(topic => (
                            <Chip key={topic} label={topic} size="small" variant="outlined" />
                          ))}
                        </Box>
                      </Box>
                    </Alert>
                  )}

                  {/* Node Details Panel (conditional) */}
                  {showNodeDetails && selectedNode && (
                    <Box sx={{ mb: 3 }}>
<<<<<<< Updated upstream
                      <NodeDetailsPanel node={selectedNode} onClose={handleCloseDetails} onStartQuiz={handleStartQuiz} quizLoading={quizLoading} />
=======
                      <NodeDetailsPanel
                        node={selectedNode}
                        onClose={handleCloseDetails}
                        onStartQuiz={handleStartQuiz}
                        onStartProductiveFailure={handleStartProductiveFailure}
                        resources={videos}
                        resourcesLoading={videosLoading}
                      />
>>>>>>> Stashed changes
                    </Box>
                  )}

                  {/* View mode toggle */}
                  {pathNodes.length > 0 && (
                    <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                      <Chip
                        icon={<Timeline sx={{ fontSize: 16 }} />}
                        label="Yol Haritası"
                        size="small"
                        onClick={() => setPathViewMode('linear')}
                        sx={{
                          fontWeight: 600,
                          cursor: 'pointer',
                          ...(pathViewMode === 'linear' ? {
                            bgcolor: '#3b82f620',
                            color: '#3b82f6',
                            borderColor: '#3b82f6',
                            borderWidth: 1.5,
                            borderStyle: 'solid',
                          } : {}),
                        }}
                      />
                      <Chip
                        icon={<AccountTree sx={{ fontSize: 16 }} />}
                        label="Skill Haritası"
                        size="small"
                        onClick={() => setPathViewMode('graph')}
                        sx={{
                          fontWeight: 600,
                          cursor: 'pointer',
                          ...(pathViewMode === 'graph' ? {
                            bgcolor: '#8b5cf620',
                            color: '#8b5cf6',
                            borderColor: '#8b5cf6',
                            borderWidth: 1.5,
                            borderStyle: 'solid',
                          } : {}),
                        }}
                      />
                    </Box>
                  )}

                  {/* Learning Path Visualizer / Skill Graph */}
                  {pathNodes.length > 0 ? (
<<<<<<< Updated upstream
                    <TopicList
                      subject={dungeonSubject}
                      onNodeClick={handleDungeonNodeClick}
                    />
=======
                    pathViewMode === 'graph' ? (
                      <SkillGraphView pathNodes={pathNodes} />
                    ) : (
                      <ModernLearningPathVisualizer
                        nodes={pathNodes}
                        connections={generateConnections(pathNodes)}
                        currentNodeId={currentNodeId}
                        onNodeClick={handleNodeClick}
                        viewMode="tree"
                      />
                    )
>>>>>>> Stashed changes
                  ) : (
                    <GlassCard glassIntensity="light">
                      <Box sx={{ textAlign: 'center', py: 8 }}>
                        <Timeline sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                        <Typography variant="h6" color="text.secondary">
                          Henüz öğrenme yolu oluşturulmamış
                        </Typography>
                        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                          Sınav sonuçlarınıza göre kişiselleştirilmiş yolunuz oluşturulacak
                        </Typography>
                      </Box>
                    </GlassCard>
                  )}
                </motion.div>
              </AnimatePresence>
            </TabPanel>

            {/* Tab 2: Video Resources */}
            <TabPanel value={tabValue} index={1}>
              <AnimatePresence mode="wait">
                <motion.div
                  key="videos"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  transition={{ duration: 0.3 }}
                >
                  <GlassCard glassIntensity="light">
                    {videosLoading ? (
                      <Box sx={{ textAlign: 'center', py: 8 }}>
                        <ModernLoader message="Videolar yükleniyor..." />
                      </Box>
                    ) : videos.length > 0 ? (
                      <Box>
                        <Typography variant="h6" sx={{ fontWeight: 700, mb: 3 }}>
                          Size Özel Video Kaynakları
                        </Typography>
                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                          {videos.map((video, index) => (
                            <motion.div
                              key={video.video_id || index}
                              initial={{ opacity: 0, y: 20 }}
                              animate={{ opacity: 1, y: 0 }}
                              transition={{ duration: 0.3, delay: index * 0.05 }}
                            >
                              <GlassCard
                                glassIntensity="light"
                                hoverable
                                role="button"
                                aria-label={`${video.title} videosunu oynat`}
                                tabIndex={0}
                                onClick={() => handleVideoPlay(video)}
                                onKeyDown={(e: React.KeyboardEvent) => {
                                  if (e.key === 'Enter' || e.key === ' ') {
                                    e.preventDefault();
                                    handleVideoPlay(video);
                                  }
                                }}
                                sx={{
                                  cursor: 'pointer',
                                  '&:focus': {
                                    outline: '2px solid rgba(59, 130, 246, 0.5)',
                                    outlineOffset: '2px',
                                  },
                                }}
                              >
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                                  <VideoLibrary color="primary" />
                                  <Box sx={{ flex: 1 }}>
                                    <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                                      {video.title}
                                    </Typography>
                                    <Typography variant="body2" color="text.secondary">
                                      {video.description || 'Video açıklaması'}
                                    </Typography>
                                  </Box>
                                </Box>
                              </GlassCard>
                            </motion.div>
                          ))}
                        </Box>
                      </Box>
                    ) : (
                      <Box sx={{ textAlign: 'center', py: 8 }}>
                        <VideoLibrary sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                        <Typography variant="h6" color="text.secondary">
                          Henüz video kaynağı eklenmemiş
                        </Typography>
                        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                          Öğrenme yolunuzdaki konulara uygun videolar burada görünecek
                        </Typography>
                      </Box>
                    )}
                  </GlassCard>
                </motion.div>
              </AnimatePresence>
            </TabPanel>

            {/* Tab 3: Progress Tracking (A5: ProgressDashboard) */}
            <TabPanel value={tabValue} index={2}>
              <AnimatePresence mode="wait">
                <motion.div
                  key="progress"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  transition={{ duration: 0.3 }}
                >
                  {hasPath ? (
                    <>
                      <StudyPlannerWidget pathNodes={pathNodes} />
                      <LeaguePanel />
                      <Box sx={{ mt: 2 }}>
                        <ProgressDashboard pathNodes={pathNodes} />
                      </Box>
                    </>
                  ) : (
                    <GlassCard glassIntensity="light">
                      <Box sx={{ textAlign: 'center', py: 8 }}>
                        <Assessment sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                        <Typography variant="h6" color="text.secondary">
                          İlerleme takibi için önce bir öğrenme yolu oluşturun
                        </Typography>
                      </Box>
<<<<<<< Updated upstream
                    )}
                  </GlassCard>

                  {/* League + Study Planner + Duel */}
                  <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 3, mt: 3 }}>
                    <LeaguePanel compact={false} />
                    <StudyPlannerWidget pathNodes={pathNodes} />
                  </Box>

                  <Box sx={{ mt: 3, textAlign: 'center' }}>
                    <ModernButton
                      variant="solid"
                      icon={<SportsEsports />}
                      onClick={() => setShowDuel(true)}
                      sx={{ background: modernColors.gradients.sunset, px: 4 }}
                    >
                      Düello Başlat
                    </ModernButton>
                  </Box>
=======
                    </GlassCard>
                  )}
>>>>>>> Stashed changes
                </motion.div>
              </AnimatePresence>
            </TabPanel>
          </GlassCard>
        </motion.div>
      </Container>

      {/* Duel Mode Dialog */}
      <Dialog
        open={showDuel}
        onClose={() => setShowDuel(false)}
        maxWidth="md"
        fullWidth
        PaperProps={{ sx: { borderRadius: 3, minHeight: '60vh' } }}
      >
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', p: 1 }}>
          <IconButton onClick={() => setShowDuel(false)} size="small">✕</IconButton>
        </Box>
        <DialogContent>
          <DuelMode subject={turkishLowerCase(selectedSubject) === 'matematik' ? 'MATEMATIK' : selectedSubject.toUpperCase()} />
        </DialogContent>
      </Dialog>
    </Box>
  );
}

export default ModernLearningPathPage;
