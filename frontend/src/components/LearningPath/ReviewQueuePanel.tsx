/**
 * ReviewQueuePanel — FSRS due kart listesi
 *
 * GET /api/learning-path/review-queue ile tekrar zamanı gelen soruları gösterir.
 * Tıklanınca QuizInterface ile soru çözme akışı başlatır.
 */

import { Alert, Box, Button, Chip, CircularProgress, LinearProgress, Paper, Typography } from '@mui/material';
import { Replay, Quiz } from '@mui/icons-material';
import { useState, useEffect, useCallback } from 'react';

import { QuizInterface } from '../Quiz/QuizInterface';
import type { Question } from '../Quiz/QuizInterface';
import { mapApiToQuizQuestion } from '../../utils/questionMappers';

interface ReviewCard {
  card_id: string;
  question_id: string;
  subject_area: string;
  due_date: string;
  reps: number;
  question?: {
    id: string;
    question_text: string;
    options: Record<string, string | null>;
    correct_answer: string;
    explanation?: string;
    difficulty_level?: string;
    subject_area?: string;
  };
}

interface ReviewQueuePanelProps {
  onClose?: () => void;
}

const hasQuestion = (c: ReviewCard): c is ReviewCard & { question: NonNullable<ReviewCard['question']> } =>
  c.question != null;

export function ReviewQueuePanel({ onClose }: ReviewQueuePanelProps) {
  const [cards, setCards] = useState<ReviewCard[]>([]);
  const [loading, setLoading] = useState(true);
  const [reviewQuestions, setReviewQuestions] = useState<Question[] | null>(null);
  const [activeCardIds, setActiveCardIds] = useState<string[]>([]);
  const [submitProgress, setSubmitProgress] = useState(0);

  const loadQueue = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/learning-path/review-queue?limit=20', {
        credentials: 'include',
      });
      const data = await res.json();
      if (data.success && data.due_questions) {
        setCards(data.due_questions);
      }
    } catch (err) {
      console.error('Review queue yüklenemedi:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadQueue();
  }, [loadQueue]);

  const handleStartReview = useCallback(() => {
    const withQuestions = cards.filter(hasQuestion);
    if (withQuestions.length === 0) return;

    setActiveCardIds(withQuestions.map(c => c.card_id));
    setReviewQuestions(
      withQuestions.map(c => mapApiToQuizQuestion(c.question)),
    );
  }, [cards]);

  const handleReviewComplete = useCallback(async (results: { answers: Record<string, any> }) => {
    const mappedQuestions = reviewQuestions || [];
    let completed = 0;
    setSubmitProgress(1); // Show progress bar

    const promises = activeCardIds.map(async (cardId, i) => {
      const mappedQ = mappedQuestions[i];
      if (!mappedQ) return;

      const userAnswer = results.answers[mappedQ.id];
      const isCorrect = userAnswer === mappedQ.correctAnswer;

      try {
        await fetch('/api/learning-path/submit-review', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({
            card_id: cardId,
            grade: isCorrect ? 4 : 1, // FSRS: 4=easy, 1=again
          }),
        });
      } catch (err) {
        console.error(`Review submit basarisiz (${cardId}):`, err);
      }
      completed++;
      setSubmitProgress(Math.round((completed / activeCardIds.length) * 100));
    });

    await Promise.allSettled(promises);
    setSubmitProgress(0);

    // Reload queue
    setReviewQuestions(null);
    setActiveCardIds([]);
    await loadQueue();
  }, [activeCardIds, reviewQuestions, loadQueue]);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
        <CircularProgress size={32} />
      </Box>
    );
  }

  // Review quiz active
  if (reviewQuestions) {
    return (
      <Box>
        {submitProgress > 0 && (
          <LinearProgress variant="determinate" value={submitProgress} sx={{ mb: 1 }} />
        )}
        <QuizInterface
          config={{
            title: 'Tekrar Zamanı',
            description: `${reviewQuestions.length} soru tekrar bekliyor`,
            questions: reviewQuestions,
            passingScore: 0,
            immediateFeedback: true,
            showCorrectAnswers: true,
          }}
          onSubmit={handleReviewComplete}
          onExit={() => { setReviewQuestions(null); setActiveCardIds([]); }}
        />
      </Box>
    );
  }

  if (cards.length === 0) {
    return (
      <Alert severity="success" variant="outlined" sx={{ mb: 3 }}>
        <Typography variant="body2">
          Tüm tekrarlar tamamlandı! Şu an tekrar bekleyen soru yok.
        </Typography>
      </Alert>
    );
  }

  return (
    <Paper elevation={2} sx={{ p: 2, mb: 3, borderLeft: '4px solid #f59e0b' }}>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Replay color="warning" />
          <Typography variant="subtitle1" fontWeight={700}>
            Tekrar Zamanı
          </Typography>
          <Chip label={`${cards.length} soru`} size="small" color="warning" />
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="contained"
            color="warning"
            size="small"
            startIcon={<Quiz />}
            onClick={handleStartReview}
          >
            Tekrar Başlat
          </Button>
          {onClose && (
            <Button size="small" onClick={onClose}>
              Kapat
            </Button>
          )}
        </Box>
      </Box>
      <Alert severity="warning" variant="outlined" sx={{ mt: 1 }}>
        <Typography variant="body2">
          Aralıklı tekrar (FSRS) algoritmasına göre bu soruları tekrar etme zamanınız geldi.
          Düzenli tekrar, uzun süreli hafıza için kritik.
        </Typography>
      </Alert>
    </Paper>
  );
}

export default ReviewQueuePanel;
