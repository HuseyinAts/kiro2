/**
 * Modern Learning Path Page - Glassmorphism Design
 * Kişiselleştirilmiş öğrenme yolu ve kaynaklar
 */

import { Timeline, VideoLibrary, Assessment, Refresh, AutoAwesome, Shuffle, Science, CalendarToday, PlayArrow, Stop, LocalFireDepartment, Timer, AccountTree } from '@mui/icons-material';
import { Container, Box, Tabs, Tab, Typography, Alert, Chip } from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';
import { useState, useEffect, useCallback, useMemo } from 'react';

// Custom hooks
import { VideoResponse } from '../api';
import { OnboardingWizard } from '../components/LearningPath/OnboardingWizard';
import { ModernLearningPathVisualizer } from '../components/LearningPath/ModernLearningPathVisualizer';
import { NodeDetailsPanel } from '../components/LearningPath/Page/NodeDetailsPanel';
import { PathNodeData } from '../components/LearningPath/PathNode';
import { GlassCard } from '../components/ui/GlassCard';
import { ModernButton } from '../components/ui/ModernButton';
import { ModernLoader } from '../components/ui/ModernLoader';
import { QuizInterface } from '../components/Quiz/QuizInterface';
import type { Question } from '../components/Quiz/QuizInterface';
import { mapApiToQuizQuestion } from '../utils/questionMappers';
import { ReviewQueuePanel } from '../components/LearningPath/ReviewQueuePanel';
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
import { useLearningPath } from '../hooks/useLearningPath';
import { useLearningPathVideos } from '../hooks/useLearningPathVideos';

import modernColors from '../theme/modern-colors';

// Types
import { generateConnections } from '../utils/learningPathHelpers';

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
    currentNodeId,
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
    studySession,
    streak,
    startSession,
    endSession,
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
  const [pathViewMode, setPathViewMode] = useState<'linear' | 'graph'>('linear');
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

  // ========================================
  // Effects
  // ========================================

  /**
   * Load videos when path is ready
   */
  useEffect(() => {
    if (pathNodes.length > 0 && learningStyle) {
      // Build a minimal path object from nodes for video loading
      const path = { modules: [{ title: pathNodes[0]?.title || 'matematik' }] };
      loadVideosForPath(path, learningStyle);
    }
  }, [pathNodes, learningStyle, loadVideosForPath]);

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
   * Fetches questions via exit-quiz endpoint and renders QuizInterface
   */
  const handleStartQuiz = useCallback(async (node: PathNodeData) => {
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
        setShowNodeDetails(false);
      }
    } catch (err) {
      console.error('Quiz soruları yüklenemedi:', err);
    }
  }, []);

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
  const handleQuizComplete = useCallback(async (results: { score: number; totalScore: number; percentage: number; answers: Record<string, any>; correctCount: number; incorrectCount: number }) => {
    // 1. Find wrong answer question IDs
    const questions = nodeQuizQuestions || [];
    const wrongIds = questions
      .filter(q => {
        const userAnswer = results.answers[q.id];
        return userAnswer !== q.correctAnswer;
      })
      .map(q => q.id);

    // 2. Register wrong answers to FSRS
    if (wrongIds.length > 0) {
      try {
        await fetch('/api/learning-path/register-wrong-answers', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({ question_ids: wrongIds }),
        });
      } catch (err) {
        console.error('FSRS kaydi basarisiz:', err);
      }
    }

    // 3. Update node progress + A1 celebration
    const passed = results.percentage >= (activeQuizNode?.quiz?.passing_score || 60);
    if (activeQuizNode) {
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
  }, [nodeQuizQuestions, activeQuizNode, markNodeComplete, updateProgress, studentId]);

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

  // Error state
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
        background: modernColors.gradients.mesh,
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
                      background: modernColors.gradients.primary,
                      backgroundClip: 'text',
                      WebkitBackgroundClip: 'text',
                      WebkitTextFillColor: 'transparent',
                    }}
                  >
                    Öğrenme Yolunuz
                  </Typography>
                  <Typography variant="body1" color="text.secondary">
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
              onChange={(_, newValue) => setTabValue(newValue)}
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
                  {!nodeQuizQuestions && !interleavedQuestions && (
                    <ReviewQueuePanel />
                  )}

                  {/* Node Quiz — node'dan başlatılan quiz */}
                  {nodeQuizQuestions && activeQuizNode && (
                    <Box sx={{ mb: 3 }}>
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
                              await fetch('/api/learning-path/register-wrong-answers', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                credentials: 'include',
                                body: JSON.stringify({ question_ids: wrongIds }),
                              });
                            } catch (err) {
                              console.error('FSRS kaydi basarisiz:', err);
                            }
                          }
                        }}
                        onExit={() => setInterleavedQuestions(null)}
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
                          onClick={async () => {
                            const subjects = [...new Set(pathNodes.map(n => n.title.split(' ')[0]))].slice(0, 5);
                            try {
                              const res = await fetch(`/api/learning-path/interleaved-practice?subjects=${subjects.join(',')}&count=10`, { credentials: 'include' });
                              const data = await res.json();
                              if (data.success && data.questions?.length > 0) {
                                setInterleavedQuestions(data.questions.map(mapApiToQuizQuestion));
                              }
                            } catch (err) {
                              console.error('Karışık pratik yüklenemedi:', err);
                            }
                          }}
                        >
                          Karışık Pratik
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
                      <NodeDetailsPanel
                        node={selectedNode}
                        onClose={handleCloseDetails}
                        onStartQuiz={handleStartQuiz}
                        onStartProductiveFailure={handleStartProductiveFailure}
                        resources={videos}
                        resourcesLoading={videosLoading}
                      />
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
                              key={(video as any).id || video.video_id || index}
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
                    </GlassCard>
                  )}
                </motion.div>
              </AnimatePresence>
            </TabPanel>
          </GlassCard>
        </motion.div>
      </Container>
    </Box>
  );
}

export default ModernLearningPathPage;
