/**
 * CATWidget — CAT Engine tam akışı
 * Kullanım: <CATWidget subjectId="matematik" token={jwt} onComplete={fn} />
 */
import React from 'react';
import {
  Box, Button, Typography, CircularProgress,
  Alert, Paper, Stack, Chip,
} from '@mui/material';
import { PlayArrow, Refresh, TrendingUp } from '@mui/icons-material';
import { useCATSession } from '../../hooks/useCATSession';
import { QuestionCard } from './QuestionCard';

interface CATWidgetProps {
  subjectId: string;
  subjectName?: string;
  token?: string | null;
  onComplete?: (theta: number, se: number, nQuestions: number) => void;
}

export function CATWidget({ subjectId, subjectName = 'Ders', token, onComplete }: CATWidgetProps) {
  const { phase, session, error, startSession, submitAnswer, reset } = useCATSession(token);

  const handleStart = () => startSession(subjectId);

  const handleAnswer = (key: string, ms: number) => {
    submitAnswer(key, ms);
  };

  React.useEffect(() => {
    if (phase === 'complete' && session && onComplete) {
      onComplete(session.theta, session.se, session.n_questions);
    }
  }, [phase, session, onComplete]);

  // ── IDLE ──────────────────────────────────────────────────────────────────
  if (phase === 'idle') {
    return (
      <Paper elevation={2} sx={{ p: 4, borderRadius: 3, textAlign: 'center', maxWidth: 480, mx: 'auto' }}>
        <TrendingUp sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
        <Typography variant="h6" fontWeight={700} mb={1}>
          {subjectName} — Adaptif Test
        </Typography>
        <Typography variant="body2" color="text.secondary" mb={3}>
          Sistem senin seviyene göre soru seçer. En fazla 20 soru.
        </Typography>
        <Button variant="contained" size="large" startIcon={<PlayArrow />} onClick={handleStart}>
          Testi Başlat
        </Button>
      </Paper>
    );
  }

  // ── LOADING ───────────────────────────────────────────────────────────────
  if (phase === 'loading') {
    return (
      <Box textAlign="center" py={6}>
        <CircularProgress size={48} />
        <Typography mt={2} color="text.secondary">Sorular yükleniyor...</Typography>
      </Box>
    );
  }

  // ── ERROR ─────────────────────────────────────────────────────────────────
  if (phase === 'error') {
    return (
      <Box maxWidth={480} mx="auto">
        <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>
        <Button variant="outlined" startIcon={<Refresh />} onClick={reset}>Tekrar Dene</Button>
      </Box>
    );
  }

  // ── COMPLETE ──────────────────────────────────────────────────────────────
  if (phase === 'complete' && session) {
    const pct = Math.round(((session.theta + 3) / 6) * 100);
    return (
      <Paper elevation={2} sx={{ p: 4, borderRadius: 3, maxWidth: 480, mx: 'auto', textAlign: 'center' }}>
        <Typography variant="h5" fontWeight={700} mb={1}>🎯 Test Tamamlandı</Typography>
        <Typography variant="body2" color="text.secondary" mb={3}>
          {session.n_questions} soruda yetenek tahmini yapıldı
        </Typography>
        <Stack spacing={1.5} mb={3}>
          <Box p={2} bgcolor="primary.50" borderRadius={2}>
            <Typography variant="caption" color="text.secondary">Yetenek Skoru (θ)</Typography>
            <Typography variant="h4" fontWeight={700} color="primary.main">
              {session.theta.toFixed(2)}
            </Typography>
          </Box>
          <Stack direction="row" spacing={1} justifyContent="center">
            <Chip label={`Güven: ${(100 - session.se * 50).toFixed(0)}%`} color="success" />
            <Chip label={`${session.n_questions} soru`} variant="outlined" />
            <Chip label={`Yüzdelik: %${pct}`} color="primary" />
          </Stack>
        </Stack>
        <Button variant="outlined" startIcon={<Refresh />} onClick={reset}>Tekrar Test Et</Button>
      </Paper>
    );
  }

  if ((phase === 'active' || phase === 'answering') && session) {
    return (
      <Box>
        <QuestionCard
          stem={session.question.stem}
          options={session.question.options}
          onAnswer={handleAnswer}
          disabled={phase === 'answering'}
          questionNumber={session.n_questions + 1}
          totalQuestions={20}
          theta={session.theta}
          phase={session.phase}
        />
        {phase === 'answering' && (
          <Box textAlign="center" mt={2}>
            <CircularProgress size={24} />
          </Box>
        )}
      </Box>
    );
  }

  return null;
}
