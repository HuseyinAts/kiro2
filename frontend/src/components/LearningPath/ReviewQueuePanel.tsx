/**
 * ReviewQueuePanel — FSRS due kart listesi
 *
 * GET /api/learning-path/review-queue ile tekrar zamanı gelen soruları gösterir.
 * Tıklanınca QuizInterface ile soru çözme akışı başlatır.
 */

import { Alert, Box, Button, Chip, CircularProgress, Paper, Typography } from '@mui/material';
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

export function ReviewQueuePanel({ onClose }: ReviewQueuePanelProps) {
  const [cards, setCards] = useState<ReviewCard[]>([]);
  const [loading, setLoading] = useState(true);
  const [reviewQuestions, setReviewQuestions] = useState<Question[] | null>(null);
  const [activeCardIds, setActiveCardIds] = useState<string[]>([]);

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
    const withQuestions = cards.filter(c => c.question);
    if (withQuestions.length === 0) return;

    setActiveCardIds(withQuestions.map(c => c.card_id));
    setReviewQuestions(
      withQuestions.map(c => mapApiToQuizQuestion(c.question!)),
    );
  }, [cards]);

  const handleReviewComplete = useCallback(async (results: { answers: Record<string, any> }) => {
    // Submit each card's grade to FSRS
    const mappedQuestions = reviewQuestions || [];
    for (let i = 0; i < activeCardIds.length; i++) {
      const cardId = activeCardIds[i];
      const mappedQ = mappedQuestions[i];
      if (!mappedQ) continue;

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
    }

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
    );
  }

  if (cards.length === 0) {
    return null; // No due cards — don't show panel
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
