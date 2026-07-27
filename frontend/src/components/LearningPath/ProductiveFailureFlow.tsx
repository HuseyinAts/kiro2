/**
 * ProductiveFailureFlow — F9: Pretest Before Instruction
 *
 * Based on Kapur (2008) Productive Failure research.
 * Shows 2-3 questions from an upcoming topic BEFORE teaching,
 * then compares pretest vs post-test for normalized learning gain.
 *
 * 4 Phases: pretest → learn → post-test → results
 */
import { useState, useCallback, useEffect } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Typography,
  LinearProgress,
  Paper,
  Stack,
  Chip,
  Alert,
  CircularProgress,
} from '@mui/material';
import {
  Psychology as PsychIcon,
  School as LearnIcon,
  CheckCircle as CheckIcon,
  TrendingUp as GrowthIcon,
  SkipNext as SkipIcon,
} from '@mui/icons-material';

import { MathText } from '../ui/MathText';
import { API_ERROR_MESSAGES } from '../../constants/errorMessages';

interface PretestQuestion {
  id: string;
  question_text: string;
  options: Record<string, string>;
  correct_answer: string;
}

interface ProductiveFailureFlowProps {
  /** Topic name for the upcoming lesson */
  topic: string;
  /** Called when the entire flow is complete */
  onComplete: () => void;
  /** Called if user skips the pretest */
  onSkip: () => void;
}

type Phase = 'intro' | 'pretest' | 'learn' | 'posttest' | 'results';

export function ProductiveFailureFlow({ topic, onComplete, onSkip }: ProductiveFailureFlowProps) {
  const [phase, setPhase] = useState<Phase>('intro');
  const [questions, setQuestions] = useState<PretestQuestion[]>([]);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [pretestAnswers, setPretestAnswers] = useState<Record<string, string>>({});
  const [posttestAnswers, setPosttestAnswers] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [pretestScore, setPretestScore] = useState(0);
  const [posttestScore, setPosttestScore] = useState(0);

  // Fetch pretest questions on mount
  useEffect(() => {
    const fetchQuestions = async () => {
      setLoading(true);
      try {
        const res = await fetch('/api/v1/productive-failure/pretest/start', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({ topic, question_count: 3 }),
        });
        if (res.ok) {
          const data = await res.json();
          setQuestions(data.questions || []);
        }
      } catch {
        // If API fails, skip productive failure
        onComplete();
      } finally {
        setLoading(false);
      }
    };
    fetchQuestions();
  }, [topic, onComplete]);

  const currentQuestion = questions[currentIdx];

  const handleAnswer = useCallback((questionId: string, answer: string) => {
    if (phase === 'pretest') {
      setPretestAnswers(prev => ({ ...prev, [questionId]: answer }));
    } else if (phase === 'posttest') {
      setPosttestAnswers(prev => ({ ...prev, [questionId]: answer }));
    }

    // Move to next question or next phase
    if (currentIdx < questions.length - 1) {
      setCurrentIdx(prev => prev + 1);
    } else {
      // Calculate score
      const answers = phase === 'pretest'
        ? { ...pretestAnswers, [questionId]: answer }
        : { ...posttestAnswers, [questionId]: answer };

      const correct = questions.filter(q => answers[q.id] === q.correct_answer).length;

      if (phase === 'pretest') {
        setPretestScore(correct);
        setPhase('learn');
        setCurrentIdx(0);
        // Submit pretest results
        fetch('/api/v1/productive-failure/pretest/submit', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({
            topic,
            answers: Object.entries({ ...pretestAnswers, [questionId]: answer }).map(([qid, ans]) => ({
              question_id: qid,
              answer: ans,
            })),
          }),
        }).catch(() => {});
      } else {
        setPosttestScore(correct);
        setPhase('results');
        // Submit growth data
        fetch('/api/v1/productive-failure/growth', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({
            topic,
            pretest_score: pretestScore,
            pretest_total: questions.length,
            posttest_score: correct,
            posttest_total: questions.length,
          }),
        }).catch(() => {});
      }
    }
  }, [phase, currentIdx, questions, pretestAnswers, posttestAnswers, pretestScore, topic]);

  // Normalized learning gain (Hake, 1998)
  const normalizedGain = questions.length > 0 && pretestScore < questions.length
    ? ((posttestScore - pretestScore) / (questions.length - pretestScore)) * 100
    : 0;

  if (loading) {
    return (
      <Card variant="outlined">
        <CardContent sx={{ textAlign: 'center', py: 4 }}>
          <CircularProgress size={32} />
          <Typography sx={{ mt: 1 }}>Ön test hazırlanıyor...</Typography>
        </CardContent>
      </Card>
    );
  }

  // Boş havuz SESSİZ OLMAMALI (27 Tem 2026). Eskiden `return null` ile hiçbir
  // şey çizilmiyordu: öğrenci neden boş ekrana baktığını bilmiyordu.
  // Kalite kapısı yayılınca bu yol gerçek hâle geldi — 26 konu ile GENEL/FEN
  // derslerinde doğrulanmış soru YOK. Ürün kararı (Hüseyin, 27 Tem): kapı
  // gevşetilmez, komşu konudan doldurulmaz — boş dönülür ve SÖYLENİR.
  if (questions.length === 0) {
    return (
      <Card variant="outlined">
        <CardContent sx={{ textAlign: 'center', py: 4 }}>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {API_ERROR_MESSAGES.NO_VERIFIED_QUESTIONS}
          </Typography>
          <Button variant="text" startIcon={<SkipIcon />} onClick={onSkip}>
            Konuya geç
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card variant="outlined" sx={{ borderColor: 'secondary.light' }}>
      <CardContent>
        {/* Phase: Intro */}
        {phase === 'intro' && (
          <Box sx={{ textAlign: 'center' }}>
            <PsychIcon sx={{ fontSize: 48, color: 'secondary.main', mb: 1 }} />
            <Typography variant="h6" fontWeight={700} gutterBottom>
              Ön Test: {topic}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2, maxWidth: 400, mx: 'auto' }}>
              Yeni konuya başlamadan önce kısa bir ön test yaparak mevcut bilgini ölçeceğiz.
              Araştırmalar bu yöntemin öğrenmeyi %30 artırdığını gösteriyor.
            </Typography>
            <Stack direction="row" spacing={1} justifyContent="center">
              <Button variant="contained" color="secondary" onClick={() => setPhase('pretest')}>
                Ön Teste Başla ({questions.length} soru)
              </Button>
              <Button variant="text" startIcon={<SkipIcon />} onClick={onSkip}>
                Atla
              </Button>
            </Stack>
          </Box>
        )}

        {/* Phase: Pretest / Posttest */}
        {(phase === 'pretest' || phase === 'posttest') && currentQuestion && (
          <Box>
            <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 2 }}>
              <Chip
                label={phase === 'pretest' ? 'Ön Test' : 'Son Test'}
                color="secondary"
                size="small"
              />
              <Typography variant="caption" color="text.secondary">
                {currentIdx + 1} / {questions.length}
              </Typography>
            </Stack>
            <LinearProgress
              variant="determinate"
              value={((currentIdx + 1) / questions.length) * 100}
              sx={{ mb: 2, height: 4, borderRadius: 2 }}
            />
            <Typography variant="body1" sx={{ mb: 2, lineHeight: 1.8 }} component="div">
              <MathText>{currentQuestion.question_text}</MathText>
            </Typography>
            <Stack spacing={1}>
              {Object.entries(currentQuestion.options).map(([key, value]) => (
                <Paper
                  key={key}
                  variant="outlined"
                  sx={{
                    p: 1.5,
                    cursor: 'pointer',
                    '&:hover': { borderColor: 'secondary.main', bgcolor: 'action.hover' },
                  }}
                  onClick={() => handleAnswer(currentQuestion.id, key)}
                >
                  <Stack direction="row" alignItems="center" spacing={1}>
                    <Chip label={key} size="small" sx={{ fontWeight: 700 }} />
                    <Typography variant="body2" component="span">
                      <MathText inline>{value}</MathText>
                    </Typography>
                  </Stack>
                </Paper>
              ))}
            </Stack>
          </Box>
        )}

        {/* Phase: Learn */}
        {phase === 'learn' && (
          <Box sx={{ textAlign: 'center' }}>
            <LearnIcon sx={{ fontSize: 48, color: 'info.main', mb: 1 }} />
            <Typography variant="h6" fontWeight={700} gutterBottom>
              Şimdi Konuyu Öğren
            </Typography>
            <Alert severity="info" sx={{ mb: 2, textAlign: 'left' }}>
              Ön test sonucun: <strong>{pretestScore}/{questions.length}</strong> doğru.
              {pretestScore < questions.length
                ? ' Şimdi konuyu çalış ve ardından tekrar test et.'
                : ' Harika! Konuyu zaten biliyorsun.'}
            </Alert>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Konuyu çalıştıktan sonra devam et. İlerleme takibi için son testi yapacağız.
            </Typography>
            <Stack direction="row" spacing={1} justifyContent="center">
              <Button
                variant="contained"
                onClick={() => { setCurrentIdx(0); setPhase('posttest'); }}
              >
                Son Teste Geç
              </Button>
              <Button variant="outlined" onClick={onComplete}>
                Daha Sonra
              </Button>
            </Stack>
          </Box>
        )}

        {/* Phase: Results */}
        {phase === 'results' && (
          <Box sx={{ textAlign: 'center' }}>
            <GrowthIcon sx={{ fontSize: 48, color: 'success.main', mb: 1 }} />
            <Typography variant="h6" fontWeight={700} gutterBottom>
              Gelişim Sonucu
            </Typography>
            <Stack direction="row" spacing={3} justifyContent="center" sx={{ mb: 2 }}>
              <Box>
                <Typography variant="h4" fontWeight={700} color="text.secondary">
                  {pretestScore}/{questions.length}
                </Typography>
                <Typography variant="caption">Ön Test</Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Typography variant="h5">→</Typography>
              </Box>
              <Box>
                <Typography variant="h4" fontWeight={700} color="success.main">
                  {posttestScore}/{questions.length}
                </Typography>
                <Typography variant="caption">Son Test</Typography>
              </Box>
            </Stack>
            {normalizedGain > 0 && (
              <Chip
                icon={<GrowthIcon />}
                label={`Normalize Öğrenme Kazanımı: %${Math.round(normalizedGain)}`}
                color="success"
                sx={{ mb: 2 }}
              />
            )}
            <Box sx={{ mt: 2 }}>
              <Button variant="contained" startIcon={<CheckIcon />} onClick={onComplete}>
                Devam Et
              </Button>
            </Box>
          </Box>
        )}
      </CardContent>
    </Card>
  );
}
