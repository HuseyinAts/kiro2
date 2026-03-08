/**
 * Modern ÖSYM Sınav Arayüzü
 * Glassmorphism tasarım ile gerçek zamanlı sınav deneyimi
 */

import {
  CheckCircle,
  BookmarkBorder,
  Bookmark,
  ExitToApp,
  NavigateNext,
  NavigateBefore,
  Flag,
  CloudDone,
  CloudOff,
  GridView,
  Close,
  Assessment,
} from '@mui/icons-material';
import {
  Box,
  Container,
  Typography,
  Button,
  RadioGroup,
  FormControlLabel,
  Radio,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  Tooltip,
  Grid,
  Snackbar,
  Alert,
  LinearProgress,
  useTheme,
  useMediaQuery,
  Badge,
  Avatar,
} from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';
import * as React from 'react';
import {  useState, useEffect, useRef  } from 'react';
import { useNavigate } from 'react-router-dom';

import useAutoSave from '../../hooks/useAutoSave';
import {
  examService,
  ExamStatus,
  ExamSessionResponse,
  QuestionResponse,
  PerformanceResponse,
} from '../../services/examService';
import { GlassCard } from '@/components/ui/GlassCard';
import { ModernButton } from '@/components/ui/ModernButton';
import { ModernLoader } from '@/components/ui/ModernLoader';
import modernColors from '@/theme/modern-colors';

interface ModernOSYMExamInterfaceProps {
  sessionId: string
  onExit?: () => void
}

interface ExamState {
  session: ExamSessionResponse | null
  currentQuestion: QuestionResponse | null
  performance: PerformanceResponse | null
  remainingTime: number
  answers: Record<string, string>
  flaggedQuestions: Set<string>
  answeredIndices: Set<number>
  flaggedIndices: Set<number>
}

export const ModernOSYMExamInterface: React.FC<ModernOSYMExamInterfaceProps> = ({
  sessionId,
  onExit: _onExit,
}) => {
  const navigate = useNavigate();
  useTheme();
  useMediaQuery('(max-width:960px)');

  // State
  const [examState, setExamState] = useState<ExamState>({
    session: null,
    currentQuestion: null,
    performance: null,
    remainingTime: 0,
    answers: {},
    flaggedQuestions: new Set(),
    answeredIndices: new Set(),
    flaggedIndices: new Set(),
  });

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showExitDialog, setShowExitDialog] = useState(false);
  const [showQuestionGrid, setShowQuestionGrid] = useState(false);
  const [showTimeWarning, setShowTimeWarning] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [saveStatus, setSaveStatus] = useState<'saved' | 'saving' | 'error' | null>(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);

  // WebSocket ref
  const wsRef = useRef<(() => void) | null>(null);

  // Auto-save
  const autoSave = useAutoSave({
    sessionId,
    enabled: examState.session?.status === ExamStatus.IN_PROGRESS,
    interval: 30000,
    onSave: (success) => {
      setSaveStatus(success ? 'saved' : 'error');
      setTimeout(() => setSaveStatus(null), 3000);
    },
    onError: () => {
      setSaveStatus('error');
      setTimeout(() => setSaveStatus(null), 5000);
    },
  });

  /**
   * Load exam data
   */
  useEffect(() => {
    loadExamData();
    return () => {
      if (wsRef.current) {wsRef.current();}
      examService.disconnectWebSocket();
      if (autoSave.getSaveStatus().pendingCount > 0) {
        autoSave.saveNow();
      }
    };
  }, [sessionId]);

  /**
   * WebSocket connection
   */
  useEffect(() => {
    if (examState.session && examState.session.status === ExamStatus.IN_PROGRESS) {
      examService.connectWebSocket(sessionId);
      wsRef.current = examService.onWebSocketMessage(handleWebSocketMessage);
    }
  }, [examState.session, sessionId]);

  /**
   * Update remaining time
   */
  useEffect(() => {
    let countdownInterval: NodeJS.Timeout | null = null;
    let syncInterval: NodeJS.Timeout | null = null;

    if (examState.session?.status === ExamStatus.IN_PROGRESS) {
      // Local countdown: her saniye 1 azalt (API çağrısı YOK)
      countdownInterval = setInterval(() => {
        setExamState((prev) => {
          const newTime = Math.max(0, prev.remainingTime - 1);
          if (newTime <= 300 && !showTimeWarning) {
            setShowTimeWarning(true);
          }
          return { ...prev, remainingTime: newTime };
        });
      }, 1000);

      // Server sync: her 30 saniyede bir doğrula
      syncInterval = setInterval(async () => {
        try {
          const timeData = await examService.getRemainingTime(sessionId);
          setExamState((prev) => ({
            ...prev,
            remainingTime: timeData.remaining_seconds,
          }));
        } catch (error) {
          console.error('Time sync error:', error);
        }
      }, 30000);
    }

    return () => {
      if (countdownInterval) {clearInterval(countdownInterval);}
      if (syncInterval) {clearInterval(syncInterval);}
    };
  }, [examState.session?.status, sessionId, showTimeWarning]);

  const loadExamData = async () => {
    try {
      setLoading(true);
      setError(null);

      const sessionData = await examService.getExamSession(sessionId);

      if (sessionData.status === ExamStatus.COMPLETED) {
        const performanceData = await examService.getPerformanceAnalysis(sessionId);
        setExamState((prev) => ({
          ...prev,
          session: sessionData,
          performance: performanceData,
        }));
      } else if (sessionData.status === ExamStatus.IN_PROGRESS) {
        const [questionData, timeData] = await Promise.all([
          examService.getCurrentQuestion(sessionId),
          examService.getRemainingTime(sessionId),
        ]);

        setExamState((prev) => ({
          ...prev,
          session: sessionData,
          currentQuestion: questionData,
          remainingTime: timeData.remaining_seconds,
        }));
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load exam data');
    } finally {
      setLoading(false);
    }
  };

  const handleWebSocketMessage = (data: any) => {
    switch (data.type) {
      case 'time_update':
        setExamState((prev) => ({ ...prev, remainingTime: data.remaining_time }));
        break;
      case 'time_warning':
        setShowTimeWarning(true);
        break;
      case 'auto_submit':
        handleSubmitExam();
        break;
    }
  };

  const handleAnswerChange = async (answer: string) => {
    if (!examState.currentQuestion) {return;}

    const questionId = examState.currentQuestion.question_id || examState.currentQuestion.id;

    try {
      await examService.submitAnswer(sessionId, questionId, answer);

      setExamState((prev) => {
        const newAnswered = new Set(prev.answeredIndices);
        newAnswered.add(currentQuestionIndex);
        return {
          ...prev,
          answers: {
            ...prev.answers,
            [questionId]: answer,
          },
          answeredIndices: newAnswered,
        };
      });

      setSaveStatus('saved');
      setTimeout(() => setSaveStatus(null), 2000);
    } catch (error) {
      console.error('Answer submit error:', error);
      setSaveStatus('error');
    }
  };

  const handleFlagToggle = () => {
    if (!examState.currentQuestion) {return;}

    const questionId = examState.currentQuestion.question_id || examState.currentQuestion.id;
    const newFlagged = new Set(examState.flaggedQuestions);
    const newFlaggedIndices = new Set(examState.flaggedIndices);

    if (newFlagged.has(questionId)) {
      newFlagged.delete(questionId);
      newFlaggedIndices.delete(currentQuestionIndex);
    } else {
      newFlagged.add(questionId);
      newFlaggedIndices.add(currentQuestionIndex);
    }

    setExamState((prev) => ({ ...prev, flaggedQuestions: newFlagged, flaggedIndices: newFlaggedIndices }));
  };

  const handleNavigateQuestion = async (index: number) => {
    try {
      const questionData = await examService.getQuestion(sessionId, index);
      setExamState((prev) => ({ ...prev, currentQuestion: questionData }));
      setCurrentQuestionIndex(index);
    } catch (error) {
      console.error('Navigation error:', error);
    }
  };

  const handlePrevious = () => {
    if (currentQuestionIndex > 0) {
      handleNavigateQuestion(currentQuestionIndex - 1);
    }
  };

  const handleNext = () => {
    if (examState.session && currentQuestionIndex < examState.session.total_questions - 1) {
      handleNavigateQuestion(currentQuestionIndex + 1);
    }
  };

  const handleSubmitExam = async () => {
    try {
      setIsSubmitting(true);
      await examService.submitExam(sessionId);
      navigate(`/exam/${sessionId}/results`);
    } catch (error) {
      console.error('Submit error:', error);
      setError('Failed to submit exam');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleMidExamExit = () => {
    // Cevaplar auto-save ile zaten kaydedilmiş, dashboard'a dön
    onExit();
  };

  const formatTime = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  if (loading) {
    return (
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: modernColors.gradients.primary,
        }}
      >
        <ModernLoader message="Sınav yükleniyor..." size="large" />
      </Box>
    );
  }

  if (error) {
    return (
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: modernColors.gradients.primary,
          p: 2,
        }}
      >
        <GlassCard glassIntensity="medium" elevated>
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
          <ModernButton variant="gradient" gradient={modernColors.gradients.primary} onClick={loadExamData}>
            Tekrar Dene
          </ModernButton>
        </GlassCard>
      </Box>
    );
  }

  const currentQuestion = examState.currentQuestion;
  const currentQuestionId = currentQuestion ? (currentQuestion.question_id || currentQuestion.id) : null;
  const currentAnswer = currentQuestionId ? examState.answers[currentQuestionId] : null;
  const isFlagged = currentQuestionId ? examState.flaggedQuestions.has(currentQuestionId) : false;

  // Transform options from individual fields to array format for rendering
  const questionOptions = currentQuestion ? [
    { option_letter: 'A', text: currentQuestion.option_a },
    { option_letter: 'B', text: currentQuestion.option_b },
    { option_letter: 'C', text: currentQuestion.option_c },
    { option_letter: 'D', text: currentQuestion.option_d },
    ...(currentQuestion.option_e ? [{ option_letter: 'E', text: currentQuestion.option_e }] : []),
  ] : [];

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: modernColors.gradients.lightBlue,
        pb: 2,
      }}
    >
      {/* Header */}
      <Box
        sx={{
          background: modernColors.glass.white.light,
          backdropFilter: 'blur(16px)',
          borderBottom: `1px solid ${modernColors.glass.border}`,
          boxShadow: modernColors.shadow.sm,
          position: 'sticky',
          top: 0,
          zIndex: 1000,
          py: 2,
        }}
      >
        <Container maxWidth="xl">
          <Grid container alignItems="center" spacing={2}>
            {/* Exam Info */}
            <Grid item xs={12} sm={4}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Avatar
                  sx={{
                    background: modernColors.gradients.primary,
                    width: 48,
                    height: 48,
                  }}
                >
                  <Assessment />
                </Avatar>
                <Box>
                  <Typography variant="h6" fontWeight={700}>
                    {examState.session?.exam_type}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Soru {currentQuestionIndex + 1}/{examState.session?.total_questions}
                  </Typography>
                </Box>
              </Box>
            </Grid>

            {/* Timer */}
            <Grid item xs={12} sm={4}>
              <Box
                sx={{
                  textAlign: 'center',
                  p: 2,
                  background: examState.remainingTime < 300 ? modernColors.gradients.error : modernColors.gradients.success,
                  borderRadius: '12px',
                  boxShadow: modernColors.shadow.md,
                }}
              >
                <Typography variant="h4" fontWeight={800} sx={{ color: 'white' }}>
                  {formatTime(examState.remainingTime)}
                </Typography>
                <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.9)' }}>
                  Kalan Süre
                </Typography>
              </Box>
            </Grid>

            {/* Actions */}
            <Grid item xs={12} sm={4}>
              <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
                <Tooltip title="Soru Haritası">
                  <IconButton
                    onClick={() => setShowQuestionGrid(true)}
                    sx={{
                      background: modernColors.glass.white.medium,
                      '&:hover': { background: modernColors.glass.white.light },
                    }}
                  >
                    <Badge badgeContent={examState.flaggedQuestions.size} color="error">
                      <GridView />
                    </Badge>
                  </IconButton>
                </Tooltip>

                <Tooltip title={saveStatus === 'saved' ? 'Kaydedildi' : 'Kaydediliyor'}>
                  <IconButton
                    sx={{
                      background: modernColors.glass.white.medium,
                      color: saveStatus === 'saved' ? 'success.main' : 'text.primary',
                    }}
                  >
                    {saveStatus === 'saved' ? <CloudDone /> : <CloudOff />}
                  </IconButton>
                </Tooltip>

                <ModernButton
                  variant="glass"
                  icon={<ExitToApp />}
                  onClick={() => setShowExitDialog(true)}
                >
                  Çık
                </ModernButton>
              </Box>
            </Grid>
          </Grid>

          {/* Progress Bar */}
          <LinearProgress
            variant="determinate"
            value={((currentQuestionIndex + 1) / (examState.session?.total_questions || 1)) * 100}
            sx={{
              mt: 2,
              height: 6,
              borderRadius: 3,
              backgroundColor: modernColors.glass.black.light,
              '& .MuiLinearProgress-bar': {
                borderRadius: 3,
                background: modernColors.gradients.primary,
              },
            }}
          />
        </Container>
      </Box>

      {/* Question Content */}
      <Container maxWidth="xl" sx={{ mt: 3 }}>
        <AnimatePresence mode="wait">
          {currentQuestion && (
            <motion.div
              key={currentQuestionId}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.3 }}
            >
              <GlassCard glassIntensity="medium" elevated>
                {/* Question Header */}
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                  <Chip
                    label={`Soru ${currentQuestionIndex + 1}`}
                    sx={{
                      background: modernColors.gradients.primary,
                      color: 'white',
                      fontWeight: 700,
                    }}
                  />

                  <Tooltip title={isFlagged ? 'İşareti Kaldır' : 'İşaretle'}>
                    <IconButton onClick={handleFlagToggle}>
                      {isFlagged ? <Bookmark sx={{ color: 'error.main' }} /> : <BookmarkBorder />}
                    </IconButton>
                  </Tooltip>
                </Box>

                {/* Question Text */}
                <Typography variant="h6" sx={{ mb: 3, lineHeight: 1.8 }}>
                  {currentQuestion.content || currentQuestion.question_text}
                </Typography>

                {/* Options */}
                <RadioGroup value={currentAnswer || ''} onChange={(e) => handleAnswerChange(e.target.value)}>
                  {questionOptions.map((option, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.1 }}
                    >
                      <FormControlLabel
                        value={option.option_letter}
                        control={<Radio />}
                        label={`${option.option_letter}) ${option.text}`}
                        sx={{
                          p: 2,
                          mb: 1,
                          borderRadius: '12px',
                          background:
                            currentAnswer === option.option_letter
                              ? modernColors.glass.primary.light
                              : modernColors.glass.white.light,
                          border: `2px solid ${
                            currentAnswer === option.option_letter
                              ? modernColors.primary[500]
                              : 'transparent'
                          }`,
                          transition: 'all 0.2s',
                          '&:hover': {
                            background: modernColors.glass.white.medium,
                            transform: 'translateX(4px)',
                          },
                        }}
                      />
                    </motion.div>
                  ))}
                </RadioGroup>
              </GlassCard>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Navigation */}
        <Box sx={{ display: 'flex', gap: 2, mt: 3, justifyContent: 'space-between' }}>
          <ModernButton
            variant="glass"
            icon={<NavigateBefore />}
            onClick={handlePrevious}
            disabled={currentQuestionIndex === 0}
          >
            Önceki
          </ModernButton>

          {currentQuestionIndex === (examState.session?.total_questions || 1) - 1 ? (
            <ModernButton
              variant="gradient"
              gradient={modernColors.gradients.success}
              glow
              icon={<CheckCircle />}
              onClick={() => setShowExitDialog(true)}
              loading={isSubmitting}
            >
              Sınavı Bitir
            </ModernButton>
          ) : (
            <ModernButton
              variant="gradient"
              gradient={modernColors.gradients.primary}
              icon={<NavigateNext />}
              onClick={handleNext}
            >
              Sonraki
            </ModernButton>
          )}
        </Box>
      </Container>

      {/* Question Grid Dialog */}
      <Dialog
        open={showQuestionGrid}
        onClose={() => setShowQuestionGrid(false)}
        maxWidth="md"
        fullWidth
        PaperProps={{
          sx: {
            background: modernColors.glass.white.light,
            backdropFilter: 'blur(16px)',
          },
        }}
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Typography variant="h6" fontWeight={700}>
              Soru Haritası
            </Typography>
            <IconButton onClick={() => setShowQuestionGrid(false)}>
              <Close />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={1}>
            {Array.from({ length: examState.session?.total_questions || 0 }).map((_, index) => {
              const answered = examState.answeredIndices.has(index);
              const flagged = examState.flaggedIndices.has(index);

              return (
                <Grid item xs={2} key={index}>
                  <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                    <Box
                      onClick={() => {
                        handleNavigateQuestion(index);
                        setShowQuestionGrid(false);
                      }}
                      sx={{
                        p: 2,
                        borderRadius: '8px',
                        textAlign: 'center',
                        cursor: 'pointer',
                        background: answered
                          ? modernColors.gradients.success
                          : modernColors.glass.white.medium,
                        color: answered ? 'white' : 'text.primary',
                        border: currentQuestionIndex === index ? `2px solid ${modernColors.primary[500]}` : 'none',
                        position: 'relative',
                      }}
                    >
                      {flagged && (
                        <Flag
                          sx={{
                            position: 'absolute',
                            top: 2,
                            right: 2,
                            fontSize: 14,
                            color: 'error.main',
                          }}
                        />
                      )}
                      <Typography fontWeight={700}>{index + 1}</Typography>
                    </Box>
                  </motion.div>
                </Grid>
              );
            })}
          </Grid>
        </DialogContent>
      </Dialog>

      {/* Exit Dialog */}
      <Dialog
        open={showExitDialog}
        onClose={() => setShowExitDialog(false)}
        PaperProps={{
          sx: {
            background: modernColors.glass.white.light,
            backdropFilter: 'blur(16px)',
          },
        }}
      >
        <DialogTitle>
          <Typography variant="h6" fontWeight={700}>
            Sınavdan Çıkmak İstediğinize Emin Misiniz?
          </Typography>
        </DialogTitle>
        <DialogContent>
          <Alert severity="warning">
            {currentQuestionIndex === (examState.session?.total_questions || 1) - 1
              ? 'Sınavınız kaydedilecek ve sonuçlarınız gösterilecek.'
              : 'Cevaplarınız kaydedilecek ancak sınav yarıda kalacak.'}
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowExitDialog(false)}>İptal</Button>
          <ModernButton
            variant="gradient"
            gradient={modernColors.gradients.error}
            onClick={
              currentQuestionIndex === (examState.session?.total_questions || 1) - 1
                ? handleSubmitExam
                : handleMidExamExit
            }
            loading={isSubmitting}
          >
            {currentQuestionIndex === (examState.session?.total_questions || 1) - 1
              ? 'Sınavı Tamamla'
              : 'Çık ve Kaydet'}
          </ModernButton>
        </DialogActions>
      </Dialog>

      {/* Time Warning Snackbar */}
      <Snackbar
        open={showTimeWarning}
        autoHideDuration={6000}
        onClose={() => setShowTimeWarning(false)}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
      >
        <Alert severity="warning" onClose={() => setShowTimeWarning(false)}>
          Dikkat! Süreniz dolmak üzere!
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default ModernOSYMExamInterface;
