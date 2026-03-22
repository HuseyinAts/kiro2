/**
 * ÖSYM Uyumlu Sınav Arayüzü - Yeni API ile
 * TYT/AYT/YDT formatında gerçek zamanlı sınav deneyimi
 *
 * OSYM EXAM INTERFACE HIERARCHY (2025-01-25):
 * Bu projede 3 OSYM exam interface var:
 *
 * 1. OSYMExamInterface.tsx (BU DOSYA) - Ana orkestrasyon component
 * 2. OSYMExamInterfaceRefactored.tsx - Hooks + store versiyonu
 * 3. ModernOSYMExamInterface.tsx - Glassmorphism tasarim
 *
 * REFACTORED (2025-01-25):
 * Bu dosya bolundu. Alt componentler Interface/ dizininde:
 *
 * - Interface/ExamHeader.tsx - Baslik, timer, progress (~100 satir)
 * - Interface/QuestionPanel.tsx - Soru gosterimi (~70 satir)
 * - Interface/AnswerPanel.tsx - Cevap secenekleri (~100 satir)
 * - Interface/ExamNavigation.tsx - Soru gezinme (~130 satir)
 * - Interface/ExamDialogs.tsx - Onay diyaloglari (~130 satir)
 *
 * Kullanim: import { ExamHeader, QuestionPanel, ... } from './Interface'
 */
import {
  CheckCircle,
  BookmarkBorder,
  Bookmark,
  ExitToApp,
  Warning,
  Assessment,
  Refresh,
  Home,
  Save,
  CloudDone,
  CloudOff,
  NavigateNext,
  NavigateBefore,
  Flag,
} from '@mui/icons-material';
import {
  Paper,
  Button,
  RadioGroup,
  FormControlLabel,
  Radio,
  Chip,
  Card,
  CardContent,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  Typography,
  Box,
  Grid,
  CircularProgress,
  Snackbar,
  useTheme,
  useMediaQuery,
  LinearProgress,
} from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';
import * as React from 'react';
import {  useState, useEffect, useCallback  } from 'react';
import { useNavigate } from 'react-router-dom';

import useAutoSave from '../../hooks/useAutoSave';
import {
  examService,
  ExamType,
  ExamStatus,
  QuestionDifficulty,
  ExamSessionResponse,
  QuestionResponse,
  PerformanceResponse,
} from '../../services/examService';
import QuestionGeometry from '../QuestionGeometry';
import QuestionGraph from '../QuestionGraph';
import QuestionMapDiagram from '../QuestionMapDiagram';
import QuestionTable from '../QuestionTable';

import { MathText } from '@/components/ui/MathText';
import { QuestionImage } from '@/components/ui/ImageZoomModal';
import ExamTimer from './ExamTimer';
import FlaggedQuestionsPanel from './FlaggedQuestionsPanel';

interface OSYMExamInterfaceProps {
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
}

export const OSYMExamInterface: React.FC<OSYMExamInterfaceProps> = ({
  sessionId,
  onExit,
}) => {
  const navigate = useNavigate();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  // State yönetimi
  const [examState, setExamState] = useState<ExamState>({
    session: null,
    currentQuestion: null,
    performance: null,
    remainingTime: 0,
    answers: {},
    flaggedQuestions: new Set(),
  });

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showExitDialog, setShowExitDialog] = useState(false);
  const [showTimeWarning, setShowTimeWarning] = useState(false);
  const [showFlaggedDialog, setShowFlaggedDialog] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [saveStatus, setSaveStatus] = useState<'saved' | 'saving' | 'error' | null>(null);
  const [saveMessage, setSaveMessage] = useState('');

  // Otomatik kaydetme
  const autoSave = useAutoSave({
    sessionId,
    enabled: examState.session?.status === ExamStatus.IN_PROGRESS,
    interval: 30000, // 30 saniye
    onSave: (success, error) => {
      if (success) {
        setSaveStatus('saved');
        setSaveMessage('Cevaplar otomatik kaydedildi');
      } else {
        setSaveStatus('error');
        setSaveMessage(error || 'Kaydetme hatası');
      }

      setTimeout(() => setSaveStatus(null), 3000);
    },
    onError: (error) => {
      setSaveStatus('error');
      setSaveMessage(error);
      setTimeout(() => setSaveStatus(null), 5000);
    },
  });

  /**
   * Bileşen mount edildiğinde sınav bilgilerini yükle
   */
  useEffect(() => {
    loadExamData();
    return () => {
      // Son kaydetme
      if (autoSave.getSaveStatus().pendingCount > 0) {
        autoSave.saveNow();
      }
    };
  }, [sessionId]);

  /**
   * Kalan süreyi periyodik olarak güncelle
   */
  useEffect(() => {
    let interval: NodeJS.Timeout | null = null;

    if (examState.session?.status === ExamStatus.IN_PROGRESS) {
      interval = setInterval(async () => {
        try {
          const timeData = await examService.getRemainingTime(sessionId);
          setExamState(prev => ({
            ...prev,
            remainingTime: timeData.remaining_seconds,
          }));

          // Uyarı kontrolü
          if (timeData.warning && !showTimeWarning) {
            setShowTimeWarning(true);
          }
        } catch (error) {
          console.error('Kalan süre güncelleme hatası:', error);
        }
      }, 1000);
    }

    return () => {
      if (interval) {clearInterval(interval);}
    };
  }, [examState.session?.status, sessionId, showTimeWarning]);

  /**
   * Sınav verilerini yükle
   */
  const loadExamData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Oturum bilgilerini getir
      const sessionData = await examService.getExamSession(sessionId);

      // Sınav durumuna göre işlem yap
      if (sessionData.status === ExamStatus.COMPLETED) {
        // Performans verilerini getir
        const performanceData = await examService.getPerformanceAnalysis(sessionId);
        setExamState(prev => ({
          ...prev,
          session: sessionData,
          performance: performanceData,
        }));
      } else if (sessionData.status === ExamStatus.IN_PROGRESS) {
        // Mevcut soruyu ve kalan süreyi getir
        const [questionData, timeData] = await Promise.all([
          examService.getCurrentQuestion(sessionId),
          examService.getRemainingTime(sessionId),
        ]);

        setExamState(prev => ({
          ...prev,
          session: sessionData,
          currentQuestion: questionData,
          remainingTime: timeData.remaining_seconds,
        }));
      } else {
        setExamState(prev => ({
          ...prev,
          session: sessionData,
        }));
      }
    } catch (err: any) {
      setError(err.message || 'Sınav verileri yüklenirken hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  /**
   * Timer güncellemelerini işle
   */
  const handleTimeUpdate = useCallback((remainingTime: number) => {
    setExamState(prev => ({
      ...prev,
      remainingTime,
    }));
  }, []);

  /**
   * Timer uyarılarını işle
   */
  const handleTimeWarning = useCallback((warningType: 'halfway' | 'final' | 'critical') => {
    if (warningType === 'final' || warningType === 'critical') {
      setShowTimeWarning(true);
    }
  }, []);

  /**
   * Süre bittiğinde otomatik gönder
   */
  const handleTimeUp = useCallback(() => {
    handleAutoSubmit();
  }, []);

  /**
   * Otomatik sınav gönderimi
   */
  const handleAutoSubmit = async () => {
    try {
      setIsSubmitting(true);

      // Son kaydetme
      await autoSave.saveNow();

      const performanceData = await examService.completeExam(sessionId);

      setExamState(prev => ({
        ...prev,
        performance: performanceData,
        session: prev.session ? { ...prev.session, status: ExamStatus.COMPLETED } : null,
      }));
    } catch (err: any) {
      setError(err.message || 'Sınav gönderilirken hata oluştu');
    } finally {
      setIsSubmitting(false);
    }
  };

  /**
   * Cevap kaydet
   */
  const handleAnswerSave = async (selectedAnswer: string) => {
    if (!examState.currentQuestion || !examState.session) {return;}

    // Optimistic update
    setExamState(prev => ({
      ...prev,
      answers: {
        ...prev.answers,
        [examState.currentQuestion!.id]: selectedAnswer,
      },
    }));

    // Otomatik kaydetme kuyruğuna ekle
    autoSave.queueSave({
      question_id: examState.currentQuestion.id,
      selected_answer: selectedAnswer,
      response_time: undefined,
    });

    // Kaydetme durumunu göster
    setSaveStatus('saving');
    setSaveMessage('Cevap kaydediliyor...');
  };

  /**
   * Sonraki soruya geç
   */
  const handleNextQuestion = async () => {
    if (!examState.session) {return;}

    try {
      const questionData = await examService.nextQuestion(sessionId, examState.session.current_question_index);

      setExamState(prev => ({
        ...prev,
        currentQuestion: questionData,
        session: prev.session ? {
          ...prev.session,
          current_question_index: prev.session.current_question_index + 1,
        } : null,
      }));
    } catch (err: any) {
      setError(err.message || 'Sonraki soru getirilemedi');
    }
  };

  /**
   * Önceki soruya dön
   */
  const handlePreviousQuestion = async () => {
    if (!examState.session) {return;}

    try {
      const questionData = await examService.previousQuestion(sessionId, examState.session.current_question_index);

      setExamState(prev => ({
        ...prev,
        currentQuestion: questionData,
        session: prev.session ? {
          ...prev.session,
          current_question_index: prev.session.current_question_index - 1,
        } : null,
      }));
    } catch (err: any) {
      setError(err.message || 'Önceki soru getirilemedi');
    }
  };

  /**
   * Belirli bir soruya git
   */
  const handleQuestionSelect = async (questionIndex: number) => {
    if (!examState.session || questionIndex === examState.session.current_question_index) {return;}

    try {
      const questionData = await examService.navigateToQuestion(sessionId, { question_index: questionIndex });

      setExamState(prev => ({
        ...prev,
        currentQuestion: questionData,
        session: prev.session ? {
          ...prev.session,
          current_question_index: questionIndex,
        } : null,
      }));
    } catch (err: any) {
      setError(err.message || 'Soru değiştirilemedi');
    }
  };

  /**
   * Soru işaretleme
   */
  const handleFlagQuestion = async (questionId?: string) => {
    if (!examState.currentQuestion) {return;}

    const targetQuestionId = questionId || examState.currentQuestion.id;
    const isCurrentlyFlagged = examState.flaggedQuestions.has(targetQuestionId);

    try {
      await examService.flagQuestion(sessionId, {
        question_id: targetQuestionId,
        flagged: !isCurrentlyFlagged,
      });

      setExamState(prev => {
        const newFlagged = new Set(prev.flaggedQuestions);
        if (isCurrentlyFlagged) {
          newFlagged.delete(targetQuestionId);
        } else {
          newFlagged.add(targetQuestionId);
        }

        return {
          ...prev,
          flaggedQuestions: newFlagged,
        };
      });
    } catch (err: any) {
      setError(err.message || 'Soru işaretlenirken hata oluştu');
    }
  };

  /**
   * Sınavı manuel tamamla
   */
  const handleCompleteExam = async () => {
    try {
      setIsSubmitting(true);

      // Son kaydetme
      await autoSave.saveNow();

      const performanceData = await examService.completeExam(sessionId);

      setExamState(prev => ({
        ...prev,
        performance: performanceData,
        session: prev.session ? { ...prev.session, status: ExamStatus.COMPLETED } : null,
      }));
    } catch (err: any) {
      setError(err.message || 'Sınav tamamlanırken hata oluştu');
    } finally {
      setIsSubmitting(false);
    }
  };

  /**
   * Zorluk seviyesi rengini getir
   */
  const getDifficultyColor = (difficulty: string): 'success' | 'warning' | 'error' | 'default' => {
    switch (difficulty) {
      case QuestionDifficulty.EASY:
        return 'success';
      case QuestionDifficulty.MEDIUM:
        return 'warning';
      case QuestionDifficulty.HARD:
        return 'error';
      default:
        return 'default';
    }
  };

  // Loading durumu
  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress size={60} />
        <Typography variant="h6" sx={{ ml: 2 }}>
          Sınav yükleniyor...
        </Typography>
      </Box>
    );
  }

  // Hata durumu
  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        <Typography variant="h6">Hata</Typography>
        <Typography>{error}</Typography>
        <Button onClick={loadExamData} startIcon={<Refresh />} sx={{ mt: 1 }}>
          Tekrar Dene
        </Button>
      </Alert>
    );
  }

  // Sınav tamamlandı - Sonuçları göster
  if (examState.performance && examState.session?.status === ExamStatus.COMPLETED) {
    return (
      <Paper elevation={3} sx={{ p: 3, m: 2 }}>
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center"
        >
          <Assessment sx={{
            fontSize: 80,
            color: examState.performance.raw_score >= 60 ? 'success.main' : 'error.main',
            mb: 2,
          }} />

          <Typography variant="h4" gutterBottom>
            Sınav Tamamlandı!
          </Typography>

          <Typography variant="h6" color="textSecondary" gutterBottom>
            {examService.getExamTypeDescription(examState.session.exam_type as ExamType)}
          </Typography>

          <Grid container spacing={3} sx={{ my: 3 }}>
            <Grid item xs={12} md={3}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" color="primary">
                    {examState.performance.raw_score.toFixed(1)}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Ham Puan
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={3}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" color="success.main">
                    {examState.performance.correct_answers}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Doğru
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={3}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" color="error.main">
                    {examState.performance.wrong_answers}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Yanlış
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={3}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" color="warning.main">
                    {examState.performance.empty_answers}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Boş
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          <Box sx={{ mb: 3 }}>
            <Typography variant="h5" gutterBottom>
              Net: {examState.performance.net_score.toFixed(2)}
            </Typography>
            <LinearProgress
              variant="determinate"
              value={(examState.performance.raw_score / 100) * 100}
              sx={{ height: 10, borderRadius: 5 }}
              color={examState.performance.raw_score >= 60 ? 'success' : 'error'}
            />
          </Box>

          {examState.performance.raw_score >= 60 ? (
            <Alert severity="success" sx={{ mb: 3 }}>
              Tebrikler! Başarılı bir performans sergiledıniz.
            </Alert>
          ) : (
            <Alert severity="info" sx={{ mb: 3 }}>
              Daha iyi bir performans için çalışmaya devam edin.
            </Alert>
          )}

          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
            <Button
              variant="contained"
              startIcon={<Home />}
              onClick={() => navigate('/dashboard')}
            >
              Ana Sayfa
            </Button>
            <Button
              variant="outlined"
              onClick={onExit}
            >
              Çıkış
            </Button>
          </Box>
        </motion.div>
      </Paper>
    );
  }

  // Sınav devam ediyor - Soru arayüzü
  if (examState.session && examState.currentQuestion && examState.session.status === ExamStatus.IN_PROGRESS) {
    const currentAnswer = examState.answers[examState.currentQuestion.id] || '';
    const isFlagged = examState.flaggedQuestions.has(examState.currentQuestion.id);
    const totalTimeSeconds = examState.session.duration_minutes * 60;
    const isFirstQuestion = examState.session.current_question_index === 0;
    const isLastQuestion = examState.session.current_question_index === examState.session.total_questions - 1;

    return (
      <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
        {/* Header - Responsive */}
        <Paper elevation={2} sx={{
          p: { xs: 1, sm: 2 },
          borderRadius: 0,
          borderBottom: 1,
          borderColor: 'divider',
        }}>
          <Box sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: { xs: 'flex-start', sm: 'center' },
            flexDirection: { xs: 'column', sm: 'row' },
            gap: { xs: 2, sm: 1 },
            mb: { xs: 2, sm: 1 },
          }}>
            <Box sx={{ flex: 1 }}>
              <Typography variant="h6" sx={{ fontSize: { xs: '1rem', sm: '1.25rem' } }}>
                {examService.getExamTypeDescription(examState.session.exam_type as ExamType)}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Soru {examState.session.current_question_index + 1} / {examState.session.total_questions}
              </Typography>
            </Box>

            <Box sx={{
              display: 'flex',
              alignItems: 'center',
              gap: { xs: 1, sm: 2 },
              alignSelf: { xs: 'stretch', sm: 'center' },
              justifyContent: { xs: 'space-between', sm: 'flex-end' },
            }}>
              {/* Kaydetme durumu */}
              {saveStatus && (
                <Chip
                  icon={saveStatus === 'saved' ? <CloudDone /> : saveStatus === 'saving' ? <Save /> : <CloudOff />}
                  label={saveStatus === 'saved' ? 'Kaydedildi' : saveStatus === 'saving' ? 'Kaydediliyor' : 'Hata'}
                  color={saveStatus === 'saved' ? 'success' : saveStatus === 'saving' ? 'info' : 'error'}
                  size="small"
                  variant="outlined"
                />
              )}

              {/* Timer */}
              <ExamTimer
                totalTimeSeconds={totalTimeSeconds}
                remainingTimeSeconds={examState.remainingTime}
                onTimeUpdate={handleTimeUpdate}
                onTimeWarning={handleTimeWarning}
                onTimeUp={handleTimeUp}
                showProgress={!isMobile}
              />

              <IconButton
                onClick={() => setShowExitDialog(true)}
                color="error"
                size="medium"
              >
                <ExitToApp />
              </IconButton>
            </Box>
          </Box>

          {/* Soru bilgileri */}
          <Box sx={{
            display: 'flex',
            gap: 0.5,
            flexWrap: 'wrap',
            justifyContent: { xs: 'center', sm: 'flex-start' },
            mb: 1,
          }}>
            <Chip
              label={`Soru ${examState.session.current_question_index + 1}`}
              variant="outlined"
              size="small"
            />
            <Chip
              label={examState.currentQuestion.difficulty}
              size="small"
              color={getDifficultyColor(examState.currentQuestion.difficulty)}
            />
            <Chip
              label={examState.currentQuestion.topic.length > 15 ?
                examState.currentQuestion.topic.substring(0, 15) + '...' :
                examState.currentQuestion.topic}
              size="small"
              variant="outlined"
            />
          </Box>
        </Paper>

        {/* Main Content Area - Responsive */}
        <Box sx={{
          flex: 1,
          overflow: 'auto',
          display: 'flex',
          flexDirection: { xs: 'column', lg: 'row' },
          gap: 2,
          p: { xs: 2, sm: 3 },
          WebkitOverflowScrolling: 'touch',
        }}>
          {/* Question Content */}
          <Box sx={{ flex: 1, minWidth: 0 }}>
          <AnimatePresence mode="wait">
            <motion.div
              key={examState.currentQuestion.id}
              initial={{ opacity: 0, x: 50 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -50 }}
              transition={{ duration: 0.3 }}
            >
              {/* Question */}
              <Box sx={{ mb: { xs: 3, sm: 4 } }}>
                <Box sx={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'flex-start',
                  mb: 2,
                  flexDirection: { xs: 'column', sm: 'row' },
                  gap: { xs: 1, sm: 0 },
                }}>
                  <Typography
                    variant="h6"
                    sx={{
                      flex: 1,
                      pr: { xs: 0, sm: 2 },
                      fontSize: { xs: '1rem', sm: '1.25rem' },
                      lineHeight: { xs: 1.5, sm: 1.6 },
                      wordBreak: 'break-word',
                    }}
                    component="div"
                  >
                    <MathText>{examState.currentQuestion.question_text}</MathText>
                  </Typography>

                  <IconButton
                    onClick={() => handleFlagQuestion()}
                    size="small"
                    sx={{
                      alignSelf: { xs: 'flex-end', sm: 'flex-start' },
                      mt: { xs: 1, sm: 0 },
                    }}
                  >
                    {isFlagged ? (
                      <Bookmark color="warning" />
                    ) : (
                      <BookmarkBorder />
                    )}
                  </IconButton>
                </Box>

                {/* Visual Content: Tables (Phase 1), Graphs (Phase 2), Geometry (Phase 3), Maps/Diagrams (Phase 4) */}
                {(examState.currentQuestion as any).visual_content && (
                  <Box sx={{ mb: 2 }}>
                    {(examState.currentQuestion as any).visual_content.type === 'table' && (
                      <QuestionTable visualContent={(examState.currentQuestion as any).visual_content} />
                    )}
                    {(examState.currentQuestion as any).visual_content.type === 'graph' && (
                      <QuestionGraph visualContent={(examState.currentQuestion as any).visual_content} />
                    )}
                    {(examState.currentQuestion as any).visual_content.type === 'geometry' && (
                      <QuestionGeometry visualContent={(examState.currentQuestion as any).visual_content} />
                    )}
                    {(examState.currentQuestion as any).visual_content.type === 'map_diagram' && (
                      <QuestionMapDiagram visualContent={(examState.currentQuestion as any).visual_content} />
                    )}
                  </Box>
                )}

                {examState.currentQuestion.question_image_url && (
                  <QuestionImage
                    src={examState.currentQuestion.question_image_url}
                    alt={examState.currentQuestion.image_alt_text || undefined}
                    width={examState.currentQuestion.image_width}
                    height={examState.currentQuestion.image_height}
                  />
                )}
              </Box>

              {/* Answer Options */}
              <Box sx={{ mb: { xs: 3, sm: 4 } }}>
                <RadioGroup
                  value={currentAnswer}
                  onChange={(e) => handleAnswerSave(e.target.value)}
                >
                  {[
                    examState.currentQuestion.option_a,
                    examState.currentQuestion.option_b,
                    examState.currentQuestion.option_c,
                    examState.currentQuestion.option_d,
                    examState.currentQuestion.option_e,
                  ].filter(Boolean).map((option, index) => {
                    const optionLabel = String.fromCharCode(65 + index); // A, B, C, D, E
                    return (
                      <FormControlLabel
                        key={index}
                        value={optionLabel}
                        control={<Radio />}
                        label={<span>{optionLabel}) <MathText inline>{String(option)}</MathText></span>}
                        sx={{
                          mb: { xs: 1.5, sm: 1 },
                          p: { xs: 1.5, sm: 2 },
                          borderRadius: 2,
                          border: 1,
                          borderColor: currentAnswer === optionLabel ? 'primary.main' : 'grey.300',
                          bgcolor: currentAnswer === optionLabel ? 'primary.50' : 'transparent',
                          transition: 'all 0.2s',
                          minHeight: { xs: 48, sm: 'auto' },
                          alignItems: 'flex-start',
                          '&:hover': {
                            bgcolor: 'grey.50',
                          },
                          '& .MuiFormControlLabel-label': {
                            fontSize: { xs: '0.95rem', sm: '1rem' },
                            lineHeight: { xs: 1.4, sm: 1.5 },
                            wordBreak: 'break-word',
                            flex: 1,
                          },
                          '& .MuiRadio-root': {
                            padding: { xs: '6px', sm: '9px' },
                          },
                        }}
                      />
                    );
                  })}
                </RadioGroup>
              </Box>
            </motion.div>
          </AnimatePresence>
          </Box>

          {/* Flagged Questions Panel - Desktop Only */}
          {!isMobile && (
            <Box sx={{ width: 320, flexShrink: 0 }}>
              <FlaggedQuestionsPanel
                flaggedQuestions={examState.flaggedQuestions}
                answers={examState.answers}
                currentQuestionIndex={examState.session.current_question_index}
                totalQuestions={examState.session.total_questions}
                onQuestionSelect={handleQuestionSelect}
                onFlagToggle={handleFlagQuestion}
                disabled={isSubmitting}
              />
            </Box>
          )}
        </Box>

        {/* Footer Navigation */}
        <Paper elevation={2} sx={{ borderRadius: 0, borderTop: 1, borderColor: 'divider' }}>
          <Box sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            p: 2,
          }}>
            <Button
              variant="outlined"
              startIcon={<NavigateBefore />}
              onClick={handlePreviousQuestion}
              disabled={isSubmitting || isFirstQuestion}
            >
              Önceki
            </Button>

            <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
              <Chip
                icon={<Flag />}
                label={`${examState.flaggedQuestions.size} İşaretli`}
                color="warning"
                variant="outlined"
                size="small"
                onClick={() => isMobile && setShowFlaggedDialog(true)}
                sx={{ cursor: isMobile ? 'pointer' : 'default' }}
              />
              <Typography variant="body2" color="textSecondary">
                {examState.session.current_question_index + 1} / {examState.session.total_questions}
              </Typography>
            </Box>

            {isLastQuestion ? (
              <Button
                variant="contained"
                color="success"
                onClick={handleCompleteExam}
                disabled={isSubmitting}
                startIcon={isSubmitting ? <CircularProgress size={20} /> : <CheckCircle />}
              >
                {isSubmitting ? 'Gönderiliyor...' : 'Sınavı Bitir'}
              </Button>
            ) : (
              <Button
                variant="contained"
                endIcon={<NavigateNext />}
                onClick={handleNextQuestion}
                disabled={isSubmitting}
              >
                Sonraki
              </Button>
            )}
          </Box>
        </Paper>

        {/* Exit Dialog */}
        <Dialog open={showExitDialog} onClose={() => setShowExitDialog(false)}>
          <DialogTitle>Sınavdan Çıkış</DialogTitle>
          <DialogContent>
            <Typography>
              Sınavdan çıkmak istediğinizden emin misiniz?
              Bu işlem geri alınamaz ve sınavınız tamamlanmış sayılacaktır.
            </Typography>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setShowExitDialog(false)}>
              İptal
            </Button>
            <Button onClick={handleCompleteExam} color="error" variant="contained">
              Çıkış Yap
            </Button>
          </DialogActions>
        </Dialog>

        {/* Time Warning Dialog */}
        <Dialog open={showTimeWarning} onClose={() => setShowTimeWarning(false)}>
          <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Warning color="warning" />
            Süre Uyarısı
          </DialogTitle>
          <DialogContent>
            <Typography>
              Sınav sürenizin az kaldı! Lütfen cevaplarınızı kontrol edin.
            </Typography>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setShowTimeWarning(false)} variant="contained">
              Tamam
            </Button>
          </DialogActions>
        </Dialog>

        {/* Flagged Questions Dialog (Mobile) */}
        <Dialog
          open={showFlaggedDialog}
          onClose={() => setShowFlaggedDialog(false)}
          fullScreen={isMobile}
          maxWidth="sm"
          fullWidth
        >
          <DialogTitle>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Flag color="warning" />
              Şüpheli Sorular
            </Box>
          </DialogTitle>
          <DialogContent sx={{ p: 0 }}>
            <FlaggedQuestionsPanel
              flaggedQuestions={examState.flaggedQuestions}
              answers={examState.answers}
              currentQuestionIndex={examState.session.current_question_index}
              totalQuestions={examState.session.total_questions}
              onQuestionSelect={(index) => {
                handleQuestionSelect(index);
                setShowFlaggedDialog(false);
              }}
              onFlagToggle={handleFlagQuestion}
              disabled={isSubmitting}
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setShowFlaggedDialog(false)}>
              Kapat
            </Button>
          </DialogActions>
        </Dialog>

        {/* Kaydetme durumu bildirimi */}
        <Snackbar
          open={!!saveStatus}
          autoHideDuration={saveStatus === 'error' ? 5000 : 3000}
          onClose={() => setSaveStatus(null)}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
        >
          <Alert
            onClose={() => setSaveStatus(null)}
            severity={saveStatus === 'saved' ? 'success' : saveStatus === 'saving' ? 'info' : 'error'}
            variant="filled"
            sx={{ width: '100%' }}
          >
            {saveMessage}
          </Alert>
        </Snackbar>
      </Box>
    );
  }

  // Varsayılan durum
  return (
    <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
      <Typography variant="h6">Sınav durumu belirsiz</Typography>
    </Box>
  );
};

export default OSYMExamInterface;