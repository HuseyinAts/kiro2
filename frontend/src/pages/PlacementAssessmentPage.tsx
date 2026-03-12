/**
 * PlacementAssessmentPage — F5: Neural Network Placement Assessment
 *
 * Adaptive 16-question assessment using Maximum Fisher Information selection
 * and Bayesian posterior ability estimation. Replaces the 10 fixed-question onboarding.
 */
import { useState, useCallback } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  LinearProgress,
  Typography,
  Alert,
  Chip,
  Stack,
  Paper,
  Tooltip,
} from '@mui/material';
import {
  PlayArrow as StartIcon,
  CheckCircle as CorrectIcon,
  Cancel as WrongIcon,
  Assessment as AssessmentIcon,
  ArrowForward as NextIcon,
} from '@mui/icons-material';

interface AssessmentQuestion {
  question_id: string;
  question_number: number;
  total_questions: number;
  question_text: string;
  options: Record<string, string>;
  subject: string;
  topic: string;
  difficulty: number;
  ability_estimate: number;
  confidence_interval: [number, number];
}

interface AssessmentResult {
  knowledge_state: Record<string, {
    mastery: number;
    confidence: string;
    response_count: number;
    topics: Record<string, number>;
  }>;
  overall_ability: number;
  total_questions: number;
  total_correct: number;
}

type PageState = 'intro' | 'assessment' | 'answering' | 'feedback' | 'loading-next' | 'result';

export default function PlacementAssessmentPage() {
  const [state, setState] = useState<PageState>('intro');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState<AssessmentQuestion | null>(null);
  const [selectedAnswer, setSelectedAnswer] = useState<string | null>(null);
  const [lastCorrect, setLastCorrect] = useState<boolean | null>(null);
  const [result, setResult] = useState<AssessmentResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [answers, setAnswers] = useState<Array<{ correct: boolean }>>([]);

  const handleStart = useCallback(async () => {
    setState('assessment');
    setError(null);
    try {
      const res = await fetch('/api/v1/assessment/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ subject: 'general' }),
      });
      if (!res.ok) throw new Error('Değerlendirme başlatılamadı');
      const data = await res.json();
      setSessionId(data.session_id);
      setCurrentQuestion(data.first_question);
      setState('answering');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Hata oluştu');
      setState('intro');
    }
  }, []);

  const handleAnswer = useCallback(async (answer: string) => {
    if (!sessionId || !currentQuestion) return;

    setSelectedAnswer(answer);
    setState('feedback');

    try {
      const res = await fetch('/api/v1/assessment/answer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          session_id: sessionId,
          question_id: currentQuestion.question_id,
          answer,
        }),
      });
      if (!res.ok) throw new Error('Cevap gönderilemedi');
      const data = await res.json();

      const isCorrect = data.is_correct;
      setLastCorrect(isCorrect);
      setAnswers(prev => [...prev, { correct: isCorrect }]);

      // Short delay to show feedback before loading next
      setTimeout(async () => {
        if (data.is_complete) {
          // Fetch final results
          try {
            const resultRes = await fetch(`/api/v1/assessment/result?session_id=${sessionId}`, {
              credentials: 'include',
            });
            if (resultRes.ok) {
              const resultData = await resultRes.json();
              setResult(resultData);
            }
          } catch {
            // Result fetch failed, show basic result
          }
          setState('result');
        } else if (data.next_question) {
          setCurrentQuestion(data.next_question);
          setSelectedAnswer(null);
          setLastCorrect(null);
          setState('answering');
        }
      }, 1200);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Hata oluştu');
    }
  }, [sessionId, currentQuestion]);

  const progress = currentQuestion
    ? (currentQuestion.question_number / currentQuestion.total_questions) * 100
    : 0;

  return (
    <Box sx={{ maxWidth: 700, mx: 'auto', p: 2 }}>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Intro */}
      {state === 'intro' && (
        <Card variant="outlined">
          <CardContent sx={{ textAlign: 'center', py: 4 }}>
            <AssessmentIcon sx={{ fontSize: 64, color: 'primary.main', mb: 2 }} />
            <Typography variant="h5" fontWeight={700} gutterBottom>
              Seviye Belirleme Testi
            </Typography>
            <Typography color="text.secondary" sx={{ mb: 3, maxWidth: 480, mx: 'auto' }}>
              16 soruluk adaptif test ile bilgi seviyeni belirleyelim.
              Her soru senin performansına göre otomatik seçilir.
              Sonunda konu bazlı güçlü ve zayıf yönlerini göreceksin.
            </Typography>
            <Stack spacing={1} sx={{ mb: 3, textAlign: 'left', maxWidth: 320, mx: 'auto' }}>
              <Typography variant="body2">✅ 16 soru — yaklaşık 10-15 dakika</Typography>
              <Typography variant="body2">✅ Her soru seviyene göre ayarlanır</Typography>
              <Typography variant="body2">✅ Sonunda kişiselleştirilmiş çalışma planı</Typography>
            </Stack>
            <Button
              variant="contained"
              size="large"
              startIcon={<StartIcon />}
              onClick={handleStart}
            >
              Teste Başla
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Assessment Loading */}
      {state === 'assessment' && (
        <Card variant="outlined">
          <CardContent sx={{ textAlign: 'center', py: 6 }}>
            <CircularProgress size={48} sx={{ mb: 2 }} />
            <Typography>Sorular hazırlanıyor...</Typography>
          </CardContent>
        </Card>
      )}

      {/* Question */}
      {(state === 'answering' || state === 'feedback') && currentQuestion && (
        <Box>
          {/* Progress bar */}
          <Box sx={{ mb: 2 }}>
            <Stack direction="row" justifyContent="space-between" sx={{ mb: 0.5 }}>
              <Typography variant="caption" color="text.secondary">
                Soru {currentQuestion.question_number} / {currentQuestion.total_questions}
              </Typography>
              <Stack direction="row" spacing={0.5}>
                {answers.map((a, i) => (
                  <Box
                    key={i}
                    sx={{
                      width: 8,
                      height: 8,
                      borderRadius: '50%',
                      bgcolor: a.correct ? 'success.main' : 'error.main',
                    }}
                  />
                ))}
              </Stack>
            </Stack>
            <LinearProgress variant="determinate" value={progress} sx={{ height: 6, borderRadius: 3 }} />
          </Box>

          {/* Subject/topic chips */}
          <Stack direction="row" spacing={0.5} sx={{ mb: 2 }}>
            <Chip label={currentQuestion.subject} size="small" color="primary" />
            <Chip label={currentQuestion.topic} size="small" variant="outlined" />
            <Tooltip title={`Zorluk: ${currentQuestion.difficulty.toFixed(1)}`}>
              <Chip
                label={
                  currentQuestion.difficulty < -1 ? 'Kolay' :
                  currentQuestion.difficulty < 1 ? 'Orta' : 'Zor'
                }
                size="small"
                color={
                  currentQuestion.difficulty < -1 ? 'success' :
                  currentQuestion.difficulty < 1 ? 'warning' : 'error'
                }
                variant="outlined"
              />
            </Tooltip>
          </Stack>

          {/* Question text */}
          <Card variant="outlined" sx={{ mb: 2 }}>
            <CardContent>
              <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.8 }}>
                {currentQuestion.question_text}
              </Typography>
            </CardContent>
          </Card>

          {/* Options */}
          <Stack spacing={1}>
            {Object.entries(currentQuestion.options).map(([key, value]) => {
              const isSelected = selectedAnswer === key;
              const showFeedback = state === 'feedback' && isSelected;

              return (
                <Paper
                  key={key}
                  variant="outlined"
                  sx={{
                    p: 1.5,
                    cursor: state === 'answering' ? 'pointer' : 'default',
                    borderColor: showFeedback
                      ? (lastCorrect ? 'success.main' : 'error.main')
                      : isSelected ? 'primary.main' : 'divider',
                    borderWidth: isSelected ? 2 : 1,
                    bgcolor: showFeedback
                      ? (lastCorrect ? 'success.light' : 'error.light')
                      : isSelected ? 'primary.light' : 'background.paper',
                    opacity: state === 'feedback' && !isSelected ? 0.6 : 1,
                    transition: 'all 0.2s',
                    '&:hover': state === 'answering' ? { borderColor: 'primary.main', bgcolor: 'action.hover' } : {},
                  }}
                  onClick={() => state === 'answering' && handleAnswer(key)}
                >
                  <Stack direction="row" alignItems="center" spacing={1}>
                    <Chip label={key} size="small" sx={{ fontWeight: 700, minWidth: 28 }} />
                    <Typography variant="body2">{value}</Typography>
                    {showFeedback && (
                      lastCorrect
                        ? <CorrectIcon color="success" sx={{ ml: 'auto' }} />
                        : <WrongIcon color="error" sx={{ ml: 'auto' }} />
                    )}
                  </Stack>
                </Paper>
              );
            })}
          </Stack>

          {/* Confidence band */}
          {currentQuestion.confidence_interval && (
            <Box sx={{ mt: 2, textAlign: 'center' }}>
              <Typography variant="caption" color="text.secondary">
                Tahmin güveni: {(
                  (currentQuestion.confidence_interval[1] - currentQuestion.confidence_interval[0]) < 1.5
                    ? 'Yüksek' : 'Gelişiyor'
                )}
              </Typography>
            </Box>
          )}
        </Box>
      )}

      {/* Loading next question */}
      {state === 'loading-next' && (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <CircularProgress size={32} />
          <Typography variant="body2" sx={{ mt: 1 }}>Sonraki soru hazırlanıyor...</Typography>
        </Box>
      )}

      {/* Result */}
      {state === 'result' && (
        <Box>
          <Card variant="outlined" sx={{ mb: 2 }}>
            <CardContent sx={{ textAlign: 'center' }}>
              <AssessmentIcon sx={{ fontSize: 48, color: 'primary.main', mb: 1 }} />
              <Typography variant="h5" fontWeight={700} gutterBottom>
                Değerlendirme Tamamlandı!
              </Typography>
              {result && (
                <Typography color="text.secondary">
                  {result.total_correct}/{result.total_questions} doğru
                </Typography>
              )}
            </CardContent>
          </Card>

          {/* Knowledge state per subject */}
          {result?.knowledge_state && (
            <Stack spacing={1.5}>
              {Object.entries(result.knowledge_state).map(([subject, data]) => (
                <Card key={subject} variant="outlined">
                  <CardContent sx={{ py: 1.5 }}>
                    <Stack direction="row" alignItems="center" justifyContent="space-between">
                      <Typography variant="subtitle2" fontWeight={600}>
                        {subject}
                      </Typography>
                      <Chip
                        label={`%${Math.round(data.mastery * 100)}`}
                        size="small"
                        color={
                          data.mastery >= 0.7 ? 'success' :
                          data.mastery >= 0.4 ? 'warning' : 'error'
                        }
                      />
                    </Stack>
                    <LinearProgress
                      variant="determinate"
                      value={data.mastery * 100}
                      sx={{ mt: 1, height: 6, borderRadius: 3 }}
                      color={
                        data.mastery >= 0.7 ? 'success' :
                        data.mastery >= 0.4 ? 'warning' : 'error'
                      }
                    />
                    {data.topics && Object.keys(data.topics).length > 0 && (
                      <Stack direction="row" spacing={0.5} sx={{ mt: 1, flexWrap: 'wrap', gap: 0.5 }}>
                        {Object.entries(data.topics).map(([topic, score]) => (
                          <Chip
                            key={topic}
                            label={`${topic}: %${Math.round(score * 100)}`}
                            size="small"
                            variant="outlined"
                          />
                        ))}
                      </Stack>
                    )}
                  </CardContent>
                </Card>
              ))}
            </Stack>
          )}

          <Button
            variant="contained"
            fullWidth
            endIcon={<NextIcon />}
            sx={{ mt: 3 }}
            href="/learning-path"
          >
            Çalışma Planına Git
          </Button>
        </Box>
      )}
    </Box>
  );
}
