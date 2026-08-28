import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Box,
  Container,
  Typography,
  RadioGroup,
  FormControlLabel,
  Radio,
  Button,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Grid,
  Alert
} from '@mui/material';
import { CheckCircle, NavigateNext, NavigateBefore, EmojiObjects } from '@mui/icons-material';

import { MathText } from '@/components/ui/MathText';
import { GlassCard } from '@/components/ui/GlassCard';
import { ModernButton } from '@/components/ui/ModernButton';
import { ModernLoader } from '@/components/ui/ModernLoader';
import modernColors from '@/theme/modern-colors';
import { examService, QuestionResponse } from '../../services/examService';

interface DiagnosticTestInterfaceProps {
  onComplete?: () => void;
}

interface OptionItemProps {
  letter: string;
  text: string;
  isSelected: boolean;
  onSelect: (letter: string) => void;
}

const OptionItem = React.memo<OptionItemProps>(({ letter, text, isSelected, onSelect }) => (
  <Grid item xs={12}>
    <Box
      onClick={() => onSelect(letter)}
      sx={{
        border: `2px solid ${isSelected ? modernColors.primary[500] : 'rgba(255,255,255,0.1)'}`,
        borderRadius: '12px',
        p: 2,
        cursor: 'pointer',
        transition: 'all 0.2s ease-in-out',
        backgroundColor: isSelected ? 'rgba(79, 70, 229, 0.1)' : 'transparent',
        '&:hover': {
          borderColor: isSelected ? modernColors.primary[500] : 'rgba(255,255,255,0.3)',
          backgroundColor: 'rgba(255,255,255,0.05)'
        }
      }}
    >
      <FormControlLabel
        value={letter}
        control={<Radio sx={{ color: 'rgba(255,255,255,0.5)', '&.Mui-checked': { color: modernColors.primary[500] } }} />}
        label={
          <Box display="flex" alignItems="center">
            <Typography variant="h6" sx={{ color: modernColors.primary[300], mr: 2, fontWeight: 'bold' }}>
              {letter}
            </Typography>
            <Typography variant="body1" color="white" component="div">
              <MathText>{text}</MathText>
            </Typography>
          </Box>
        }
        sx={{ m: 0, width: '100%' }}
      />
    </Box>
  </Grid>
));

// A more adaptive and simpler UI for the Diagnostic test
export const DiagnosticTestInterface: React.FC<DiagnosticTestInterfaceProps> = ({ onComplete }) => {
  const navigate = useNavigate();

  const [isLoading, setIsLoading] = useState(true);
  const [questions, setQuestions] = useState<QuestionResponse[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [showConfirm, setShowConfirm] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Start diagnostic test
    const initDiagnostic = async () => {
      try {
        setIsLoading(true);
        // FIXME: createBetaPractice doesn't return questions in ExamSessionResponse,
        // we might need a specific endpoint to fetch all questions for a session
        const session = await examService.createBetaPractice(20);
        setSessionId(session.session_id);

        // Wait for session to be started and fetch questions
        await examService.startExam(session.session_id);

        // Let's assume we have an endpoint to fetch all questions for the session
        // For now, since beta-practice is used, we need to fetch the current question
        // and build the list. To keep it simple, we use getQuestion(sessionId, index) if available.
        // As a fallback, if questions are not directly available, we fetch the first one.
        const currentQ = await examService.getQuestion(session.session_id, 0);
        setQuestions([currentQ]);
        setIsLoading(false);
      } catch (err) {
        console.error("Failed to init diagnostic:", err);
        setError("Seviye tespit sınavı başlatılamadı. Lütfen daha sonra tekrar deneyin.");
        setIsLoading(false);
      }
    };
    initDiagnostic();
  }, []);

  const handleAnswerSelect = async (questionId: string, answer: string) => {
    setAnswers(prev => ({ ...prev, [questionId]: answer }));

    if (sessionId) {
      try {
        await examService.saveAnswer(sessionId, {
          question_id: questionId,
          selected_answer: answer
        });
      } catch (err) {
        console.error("Cevap kaydedilemedi:", err);
      }
    }
  };

  const handleNext = async () => {
    if (!sessionId) return;

    // Fetch next question if not already in state
    if (currentIndex === questions.length - 1) {
      try {
        setIsLoading(true);
        await examService.navigateToQuestion(sessionId, { question_index: currentIndex + 1 });
        const nextQ = await examService.getQuestion(sessionId, currentIndex + 1);
        setQuestions(prev => [...prev, nextQ]);
        setCurrentIndex(prev => prev + 1);
        setIsLoading(false);
      } catch (err) {
        console.error("No more questions or failed to fetch:", err);
        // Likely end of test
        setShowConfirm(true);
        setIsLoading(false);
      }
    } else {
      setCurrentIndex(prev => prev + 1);
    }
  };

  const handlePrev = () => {
    if (currentIndex > 0) {
      setCurrentIndex(prev => prev - 1);
      if (sessionId) {
        examService.navigateToQuestion(sessionId, { question_index: currentIndex - 1 }).catch(console.error);
      }
    }
  };

  const handleFinish = async () => {
    if (!sessionId) return;
    try {
      setIsLoading(true);
      await examService.completeExam(sessionId);
      if (onComplete) {
        onComplete();
      } else {
        navigate('/dashboard');
      }
    } catch (err) {
      console.error("Sınav bitirilemedi:", err);
      setIsLoading(false);
    }
  };

  if (isLoading && questions.length === 0) {
    return (
      <Box sx={{ display: 'flex', height: '100vh', alignItems: 'center', justifyContent: 'center' }}>
        <ModernLoader message="Seviye Tespit Sınavı Hazırlanıyor..." />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ display: 'flex', height: '100vh', alignItems: 'center', justifyContent: 'center', p: 3 }}>
        <Alert severity="error" sx={{ width: '100%', maxWidth: 500 }}>{error}</Alert>
      </Box>
    );
  }

  const currentQuestion = questions[currentIndex];
  const questionOptions = currentQuestion ? [
    { letter: 'A', text: currentQuestion.option_a },
    { letter: 'B', text: currentQuestion.option_b },
    { letter: 'C', text: currentQuestion.option_c },
    { letter: 'D', text: currentQuestion.option_d },
    ...(currentQuestion.option_e ? [{ letter: 'E', text: currentQuestion.option_e }] : []),
  ] : [];

  return (
    <Box sx={{ minHeight: '100vh', background: `linear-gradient(135deg, ${modernColors.background.default} 0%, #1a1a2e 100%)`, py: 4 }}>
      <Container maxWidth="md">

        {/* Header Progress */}
        <GlassCard sx={{ mb: 4, textAlign: 'center', p: 3 }}>
          <Box display="flex" alignItems="center" justifyContent="center" gap={2} mb={2}>
            <EmojiObjects sx={{ color: modernColors.primary[500], fontSize: 32 }} />
            <Typography variant="h5" color="white" fontWeight={700}>
              Kişiselleştirilmiş Öğrenme Rotası (Seviye Tespiti)
            </Typography>
          </Box>
          <LinearProgress
            variant="determinate"
            value={questions.length > 0 ? ((currentIndex + 1) / 20) * 100 : 0}
            sx={{
              height: 12,
              borderRadius: 6,
              backgroundColor: 'rgba(255,255,255,0.1)',
              '& .MuiLinearProgress-bar': {
                backgroundImage: modernColors.gradients.primary
              }
            }}
          />
          <Typography variant="body2" color="grey.400" mt={1}>
            Soru {currentIndex + 1}
          </Typography>
        </GlassCard>

        {/* Question Area */}
        <AnimatePresence mode="wait">
          {currentQuestion && (
            <motion.div
              key={currentQuestion.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
            >
              <GlassCard sx={{ p: { xs: 2, md: 5 } }}>
                <Box mb={4}>
                  <Typography variant="h6" color="white" lineHeight={1.6} component="div">
                    <MathText>{currentQuestion.question_text || currentQuestion.content || ''}</MathText>
                  </Typography>
                </Box>

                <RadioGroup
                  value={answers[currentQuestion.id || currentQuestion.question_id!] || ''}
                  onChange={(e) => handleAnswerSelect(currentQuestion.id || currentQuestion.question_id!, e.target.value)}
                >
                  <Grid container spacing={2}>
                    {questionOptions.map((opt) => (
                      <OptionItem
                        key={opt.letter}
                        letter={opt.letter}
                        text={opt.text}
                        isSelected={answers[currentQuestion.id || currentQuestion.question_id!] === opt.letter}
                        onSelect={(letter) => handleAnswerSelect(currentQuestion.id || currentQuestion.question_id!, letter)}
                      />
                    ))}
                  </Grid>
                </RadioGroup>
              </GlassCard>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Navigation */}
        <Box display="flex" justifyContent="space-between" mt={4}>
          <ModernButton
            onClick={handlePrev}
            disabled={currentIndex === 0 || isLoading}
            startIcon={<NavigateBefore />}
            variant="outlined"
            sx={{ borderColor: 'rgba(255,255,255,0.2)', color: 'white' }}
          >
            Önceki
          </ModernButton>

          <ModernButton
            onClick={handleNext}
            disabled={isLoading}
            endIcon={currentIndex === 19 ? <CheckCircle /> : <NavigateNext />}
            variant="gradient"
            gradient={modernColors.gradients.primary}
          >
            {currentIndex === 19 ? 'Testi Bitir' : 'Sonraki Soru'}
          </ModernButton>
        </Box>
      </Container>

      {/* Confirmation Dialog */}
      <Dialog
        open={showConfirm}
        onClose={() => setShowConfirm(false)}
        PaperProps={{
          sx: {
            background: modernColors.background.paper,
            color: 'white',
            borderRadius: '16px',
            border: `1px solid rgba(255,255,255,0.1)`
          }
        }}
      >
        <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <CheckCircle color="success" /> Seviye Tespiti Tamamlandı
        </DialogTitle>
        <DialogContent>
          <Typography color="grey.300">
            Cevaplarınız kaydedildi. Yapay zeka motorumuz öğrenme rotanızı çizmek için sonuçlarınızı analiz edecek. Sınavı bitirmek istiyor musunuz?
          </Typography>
        </DialogContent>
        <DialogActions sx={{ p: 3 }}>
          <Button onClick={() => setShowConfirm(false)} sx={{ color: 'grey.400' }}>
            İptal
          </Button>
          <ModernButton onClick={handleFinish} variant="gradient" gradient={modernColors.gradients.success}>
            Analizi Başlat
          </ModernButton>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
