/**
 * Sınav Arayüzü - ÖSYM Uyumlu Tam Sınav Deneyimi
 *
 * REQ-1.6: Sınav arayüzü özellikleri
 * - İşaretleme sistemi (69.1)
 * - Boş bırakma takibi (69.2)
 * - Şüpheli işaretleme (69.3)
 * - Soru navigasyonu (69.4)
 */
import {
  NavigateBefore,
  NavigateNext,
  Flag,
  FlagOutlined,
  CheckCircle,
  RadioButtonUnchecked,
  Warning,
  GridView,
  Info,
} from '@mui/icons-material';
import {
  Box,
  Paper,
  Typography,
  Button,
  IconButton,
  Tooltip,
  Chip,
  Grid,
  Divider,
  useTheme,
  alpha,
  Badge,
} from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';
import * as React from 'react';
import {  useState, useEffect, useCallback  } from 'react';

import BubbleSheetInterface from './BubbleSheetInterface';

export interface ExamQuestion {
  id: string
  number: number
  content: string
  options: string[]
  subject?: string
  topic?: string
}

export interface ExamAnswer {
  questionId: string
  answer: string
  flaggedForReview: boolean
  timestamp: Date
}

interface ExamInterfaceProps {
  questions: ExamQuestion[]
  answers: Record<string, ExamAnswer>
  currentQuestionIndex: number
  onAnswerChange: (questionId: string, answer: string) => void
  onFlagToggle: (questionId: string) => void
  onQuestionNavigate: (index: number) => void
  disabled?: boolean
  showNavigationPanel?: boolean
}

/**
 * Ana sınav arayüzü bileşeni
 */
export const ExamInterface: React.FC<ExamInterfaceProps> = ({
  questions,
  answers,
  currentQuestionIndex,
  onAnswerChange,
  onFlagToggle,
  onQuestionNavigate,
  disabled = false,
  showNavigationPanel = true,
}) => {
  const theme = useTheme();
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [lastAnsweredQuestion, setLastAnsweredQuestion] = useState<number | null>(null);

  const currentQuestion = questions[currentQuestionIndex];
  const currentAnswer = currentQuestion ? answers[currentQuestion.id] : null;

  /**
   * Cevap değiştiğinde onay göster
   */
  useEffect(() => {
    if (currentAnswer?.answer) {
      setShowConfirmation(true);
      setLastAnsweredQuestion(currentQuestionIndex);
      const timer = setTimeout(() => setShowConfirmation(false), 2000);
      return () => clearTimeout(timer);
    }
  }, [currentAnswer?.answer, currentQuestionIndex]);

  /**
   * Cevap seçme işleyicisi
   */
  const handleAnswerSelect = useCallback((answer: string) => {
    if (disabled || !currentQuestion) {return;}
    onAnswerChange(currentQuestion.id, answer);
  }, [disabled, currentQuestion, onAnswerChange]);

  /**
   * Şüpheli işaretleme işleyicisi
   */
  const handleFlagToggle = useCallback(() => {
    if (disabled || !currentQuestion) {return;}
    onFlagToggle(currentQuestion.id);
  }, [disabled, currentQuestion, onFlagToggle]);

  /**
   * Önceki soru
   */
  const handlePrevious = useCallback(() => {
    if (currentQuestionIndex > 0) {
      onQuestionNavigate(currentQuestionIndex - 1);
    }
  }, [currentQuestionIndex, onQuestionNavigate]);

  /**
   * Sonraki soru
   */
  const handleNext = useCallback(() => {
    if (currentQuestionIndex < questions.length - 1) {
      onQuestionNavigate(currentQuestionIndex + 1);
    }
  }, [currentQuestionIndex, questions.length, onQuestionNavigate]);

  /**
   * Klavye kısayolları
   */
  useEffect(() => {
    const handleKeyPress = (event: KeyboardEvent) => {
      if (disabled) {return;}

      // Sol ok: Önceki soru
      if (event.key === 'ArrowLeft') {
        event.preventDefault();
        handlePrevious();
      }
      // Sağ ok: Sonraki soru
      else if (event.key === 'ArrowRight') {
        event.preventDefault();
        handleNext();
      }
      // F tuşu: Şüpheli işaretle
      else if (event.key === 'f' || event.key === 'F') {
        event.preventDefault();
        handleFlagToggle();
      }
      // A-E tuşları: Cevap seç
      else if (['a', 'b', 'c', 'd', 'e'].includes(event.key.toLowerCase())) {
        event.preventDefault();
        handleAnswerSelect(event.key.toUpperCase());
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [disabled, handlePrevious, handleNext, handleFlagToggle, handleAnswerSelect]);

  if (!currentQuestion) {
    return (
      <Box sx={{ p: 4, textAlign: 'center' }}>
        <Typography variant="h6" color="textSecondary">
          Soru bulunamadı
        </Typography>
      </Box>
    );
  }

  const isFlagged = currentAnswer?.flaggedForReview || false;
  const hasAnswer = !!currentAnswer?.answer;

  return (
    <Box sx={{ display: 'flex', gap: 2, height: '100%' }}>
      {/* Ana soru alanı */}
      <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 2 }}>
        {/* Soru başlığı ve kontroller */}
        <Paper elevation={2} sx={{ p: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Typography variant="h6">
                Soru {currentQuestion.number}
              </Typography>
              {currentQuestion.subject && (
                <Chip label={currentQuestion.subject} size="small" color="primary" variant="outlined" />
              )}
              {currentQuestion.topic && (
                <Chip label={currentQuestion.topic} size="small" variant="outlined" />
              )}
            </Box>

            <Box sx={{ display: 'flex', gap: 1 }}>
              {/* Şüpheli işaretleme */}
              <Tooltip title={isFlagged ? 'İnceleme işaretini kaldır (F)' : 'İnceleme için işaretle (F)'}>
                <IconButton
                  onClick={handleFlagToggle}
                  disabled={disabled}
                  color={isFlagged ? 'warning' : 'default'}
                  sx={{
                    transition: 'all 0.2s',
                    '&:hover': {
                      transform: 'scale(1.1)',
                    },
                  }}
                >
                  {isFlagged ? <Flag /> : <FlagOutlined />}
                </IconButton>
              </Tooltip>

              {/* Durum göstergesi */}
              <Tooltip title={hasAnswer ? 'Cevaplandı' : 'Boş'}>
                <Box>
                  {hasAnswer ? (
                    <CheckCircle color="success" sx={{ fontSize: 32 }} />
                  ) : (
                    <RadioButtonUnchecked color="disabled" sx={{ fontSize: 32 }} />
                  )}
                </Box>
              </Tooltip>
            </Box>
          </Box>
        </Paper>

        {/* Soru içeriği */}
        <Paper elevation={2} sx={{ p: 3, flex: 1 }}>
          <Typography variant="body1" sx={{ mb: 3, lineHeight: 1.8 }}>
            {currentQuestion.content}
          </Typography>

          {/* Cevap seçenekleri */}
          <Box sx={{ mt: 4 }}>
            <BubbleSheetInterface
              questionNumber={currentQuestion.number}
              options={currentQuestion.options}
              selectedAnswer={currentAnswer?.answer || null}
              onAnswerSelect={handleAnswerSelect}
              disabled={disabled}
              size="large"
            />
          </Box>

          {/* Görsel onay */}
          <AnimatePresence>
            {showConfirmation && lastAnsweredQuestion === currentQuestionIndex && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3 }}
              >
                <Box
                  sx={{
                    mt: 3,
                    p: 2,
                    borderRadius: 2,
                    bgcolor: alpha(theme.palette.success.main, 0.1),
                    border: 1,
                    borderColor: theme.palette.success.main,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 1,
                  }}
                >
                  <CheckCircle color="success" />
                  <Typography variant="body2" color="success.main">
                    Cevabınız kaydedildi: <strong>{currentAnswer?.answer}</strong>
                  </Typography>
                </Box>
              </motion.div>
            )}
          </AnimatePresence>
        </Paper>

        {/* Navigasyon kontrolleri */}
        <Paper elevation={2} sx={{ p: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Button
              startIcon={<NavigateBefore />}
              onClick={handlePrevious}
              disabled={disabled || currentQuestionIndex === 0}
              variant="outlined"
            >
              Önceki Soru
            </Button>

            <Typography variant="body2" color="textSecondary">
              {currentQuestionIndex + 1} / {questions.length}
            </Typography>

            <Button
              endIcon={<NavigateNext />}
              onClick={handleNext}
              disabled={disabled || currentQuestionIndex === questions.length - 1}
              variant="outlined"
            >
              Sonraki Soru
            </Button>
          </Box>

          {/* Klavye kısayolları bilgisi */}
          <Box sx={{ mt: 2, p: 1, bgcolor: alpha(theme.palette.info.main, 0.05), borderRadius: 1 }}>
            <Typography variant="caption" color="textSecondary" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <Info fontSize="small" />
              Kısayollar: ← → (Gezinme) | A-E (Cevap) | F (İşaretle)
            </Typography>
          </Box>
        </Paper>
      </Box>

      {/* Soru navigasyon paneli */}
      {showNavigationPanel && (
        <QuestionNavigationPanel
          questions={questions}
          answers={answers}
          currentQuestionIndex={currentQuestionIndex}
          onQuestionNavigate={onQuestionNavigate}
          disabled={disabled}
        />
      )}
    </Box>
  );
};

/**
 * Soru navigasyon paneli bileşeni
 */
interface QuestionNavigationPanelProps {
  questions: ExamQuestion[]
  answers: Record<string, ExamAnswer>
  currentQuestionIndex: number
  onQuestionNavigate: (index: number) => void
  disabled?: boolean
}

const QuestionNavigationPanel: React.FC<QuestionNavigationPanelProps> = ({
  questions,
  answers,
  currentQuestionIndex,
  onQuestionNavigate,
  disabled,
}) => {
  const theme = useTheme();

  // İstatistikleri hesapla
  const stats = {
    total: questions.length,
    answered: Object.values(answers).filter(a => a.answer).length,
    flagged: Object.values(answers).filter(a => a.flaggedForReview).length,
    unanswered: questions.length - Object.values(answers).filter(a => a.answer).length,
  };

  /**
   * Soru durumuna göre renk belirle
   */
  const getQuestionColor = (question: ExamQuestion) => {
    const answer = answers[question.id];
    const isCurrent = currentQuestionIndex === question.number - 1;

    if (isCurrent) {
      return theme.palette.primary.main;
    } else if (answer?.flaggedForReview) {
      return theme.palette.warning.main;
    } else if (answer?.answer) {
      return theme.palette.success.main;
    } else {
      return theme.palette.grey[400];
    }
  };

  return (
    <Paper
      elevation={2}
      sx={{
        width: 320,
        p: 2,
        display: 'flex',
        flexDirection: 'column',
        gap: 2,
        maxHeight: '100%',
        overflow: 'auto',
      }}
    >
      {/* Başlık */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <GridView color="primary" />
        <Typography variant="h6">Soru Haritası</Typography>
      </Box>

      <Divider />

      {/* İstatistikler */}
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
        <Chip
          icon={<CheckCircle />}
          label={`${stats.answered} Cevaplandı`}
          color="success"
          variant="outlined"
          size="small"
        />
        <Chip
          icon={<Warning />}
          label={`${stats.unanswered} Boş`}
          color={stats.unanswered > 0 ? 'error' : 'default'}
          variant="outlined"
          size="small"
        />
        <Chip
          icon={<Flag />}
          label={`${stats.flagged} İşaretli`}
          color="warning"
          variant="outlined"
          size="small"
        />
      </Box>

      <Divider />

      {/* Soru grid */}
      <Box>
        <Typography variant="subtitle2" sx={{ mb: 1 }}>
          Sorular
        </Typography>
        <Grid container spacing={1}>
          {questions.map((question) => {
            const isCurrent = currentQuestionIndex === question.number - 1;
            const answer = answers[question.id];
            const color = getQuestionColor(question);

            return (
              <Grid item xs={3} key={question.id}>
                <Tooltip
                  title={
                    <Box>
                      <Typography variant="caption">Soru {question.number}</Typography>
                      {answer?.answer && (
                        <Typography variant="caption" display="block">
                          Cevap: {answer.answer}
                        </Typography>
                      )}
                      {answer?.flaggedForReview && (
                        <Typography variant="caption" display="block" color="warning.main">
                          İnceleme için işaretli
                        </Typography>
                      )}
                      {!answer?.answer && (
                        <Typography variant="caption" display="block" color="error.main">
                          Boş
                        </Typography>
                      )}
                    </Box>
                  }
                  arrow
                >
                  <motion.div
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    <Badge
                      badgeContent={answer?.flaggedForReview ? <Flag sx={{ fontSize: 12 }} /> : null}
                      color="warning"
                    >
                      <Box
                        onClick={() => !disabled && onQuestionNavigate(question.number - 1)}
                        sx={{
                          width: 48,
                          height: 48,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          borderRadius: 1,
                          border: 2,
                          borderColor: color,
                          bgcolor: isCurrent ? alpha(color, 0.2) : 'transparent',
                          cursor: disabled ? 'default' : 'pointer',
                          fontWeight: isCurrent ? 'bold' : 'normal',
                          transition: 'all 0.2s',
                          '&:hover': disabled ? {} : {
                            bgcolor: alpha(color, 0.1),
                            transform: 'translateY(-2px)',
                            boxShadow: theme.shadows[4],
                          },
                        }}
                      >
                        <Typography
                          variant="body2"
                          sx={{
                            color: isCurrent ? color : 'text.primary',
                            fontWeight: 'inherit',
                          }}
                        >
                          {question.number}
                        </Typography>
                      </Box>
                    </Badge>
                  </motion.div>
                </Tooltip>
              </Grid>
            );
          })}
        </Grid>
      </Box>

      {/* Açıklama */}
      <Box sx={{ mt: 'auto', p: 1, bgcolor: alpha(theme.palette.info.main, 0.05), borderRadius: 1 }}>
        <Typography variant="caption" color="textSecondary">
          <strong>Mavi:</strong> Aktif soru<br />
          <strong>Yeşil:</strong> Cevaplandı<br />
          <strong>Turuncu:</strong> İnceleme için işaretli<br />
          <strong>Gri:</strong> Boş
        </Typography>
      </Box>
    </Paper>
  );
};

export default ExamInterface;
