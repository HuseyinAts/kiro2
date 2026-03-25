/**
 * PlacementWidget — Placement Test tam akışı
 * Kullanım: <PlacementWidget subjectId="mat" token={jwt} onComplete={fn} />
 */
import React from 'react';
import {
  Box, Button, Typography, CircularProgress,
  Alert, Paper, Stack, Chip, LinearProgress,
  List, ListItem, ListItemIcon, ListItemText,
} from '@mui/material';
import { PlayArrow, Refresh, School, CheckCircle } from '@mui/icons-material';
import { usePlacementSession } from '../../hooks/usePlacementSession';
import { QuestionCard } from './QuestionCard';

interface PlacementWidgetProps {
  subjectId: string;
  subjectName?: string;
  schoolType?: string;
  token?: string | null;
  onComplete?: (result: { theta: number; level: string; level_label: string }) => void;
}

const LEVEL_LABELS: Record<string, { label: string; color: 'error' | 'warning' | 'info' | 'success' | 'primary' }> = {
  beginner:      { label: 'Başlangıç',    color: 'error' },
  elementary:    { label: 'Temel',         color: 'warning' },
  intermediate:  { label: 'Orta',          color: 'info' },
  upper_intermediate: { label: 'Orta-Üst', color: 'primary' },
  advanced:      { label: 'İleri',         color: 'success' },
};

export function PlacementWidget({
  subjectId, subjectName = 'Ders', schoolType = 'default', token, onComplete,
}: PlacementWidgetProps) {
  const { phase, session, finalResult, error, startSession, submitAnswer, reset } = usePlacementSession(token);

  React.useEffect(() => {
    if (phase === 'complete' && finalResult && onComplete) {
      onComplete({ theta: finalResult.theta_final, level: finalResult.level, level_label: finalResult.level_label });
    }
  }, [phase]);

  // ── IDLE ──────────────────────────────────────────────────────────────────
  if (phase === 'idle') {
    return (
      <Paper elevation={2} sx={{ p: 4, borderRadius: 3, textAlign: 'center', maxWidth: 480, mx: 'auto' }}>
        <School sx={{ fontSize: 48, color: 'secondary.main', mb: 2 }} />
        <Typography variant="h6" fontWeight={700} mb={1}>
          {subjectName} — Seviye Tespiti
        </Typography>
        <Typography variant="body2" color="text.secondary" mb={3}>
          En fazla 12 soru ile mevcut seviyeni belirliyoruz.
        </Typography>
        <Button variant="contained" color="secondary" size="large"
          startIcon={<PlayArrow />}
          onClick={() => startSession(subjectId, schoolType)}>
          Seviye Testini Başlat
        </Button>
      </Paper>
    );
  }

  // ── LOADING ───────────────────────────────────────────────────────────────
  if (phase === 'loading') {
    return (
      <Box textAlign="center" py={6}>
        <CircularProgress size={48} color="secondary" />
        <Typography mt={2} color="text.secondary">Sorular hazırlanıyor...</Typography>
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
  if (phase === 'complete' && finalResult) {
    const lvl = LEVEL_LABELS[finalResult.level] ?? { label: finalResult.level_label, color: 'primary' };
    return (
      <Paper elevation={2} sx={{ p: 4, borderRadius: 3, maxWidth: 520, mx: 'auto' }}>
        <Typography variant="h5" fontWeight={700} mb={1} textAlign="center">
          🎓 Seviye Tespiti Tamamlandı
        </Typography>
        <Stack spacing={2} mt={3}>
          <Box p={2.5} bgcolor="secondary.50" borderRadius={2} textAlign="center">
            <Typography variant="caption" color="text.secondary">Seviyeniz</Typography>
            <Typography variant="h3" fontWeight={800} color="secondary.main">
              {finalResult.level_label}
            </Typography>
            <Chip label={lvl.label} color={lvl.color} sx={{ mt: 1 }} />
          </Box>
          <Stack direction="row" spacing={1} justifyContent="center">
            <Chip label={`θ = ${finalResult.theta_final.toFixed(2)}`} variant="outlined" />
            <Chip label={`Güven: SE ${finalResult.se_final.toFixed(2)}`} variant="outlined" />
          </Stack>
          {finalResult.recommended_subjects?.length > 0 && (
            <Box>
              <Typography variant="subtitle2" fontWeight={600} mb={1}>
                📚 Önerilen Başlangıç Konuları
              </Typography>
              <List dense disablePadding>
                {finalResult.recommended_subjects.slice(0, 5).map((s) => (
                  <ListItem key={s} disablePadding>
                    <ListItemIcon sx={{ minWidth: 28 }}><CheckCircle fontSize="small" color="success" /></ListItemIcon>
                    <ListItemText primary={s} />
                  </ListItem>
                ))}
              </List>
            </Box>
          )}
        </Stack>
        <Box mt={3} textAlign="center">
          <Button variant="outlined" startIcon={<Refresh />} onClick={reset}>Tekrarla</Button>
        </Box>
      </Paper>
    );
  }

  // ── ACTIVE / ANSWERING ────────────────────────────────────────────────────
  if ((phase === 'active' || phase === 'answering') && session) {
    return (
      <Box>
        <Box mb={2} maxWidth={720} mx="auto">
          <Stack direction="row" justifyContent="space-between" alignItems="center">
            <Typography variant="caption" color="text.secondary">
              Soru {session.progress.current + 1} / {session.progress.max}
            </Typography>
            <Chip size="small" label={session.level_hint} variant="outlined" />
          </Stack>
          <LinearProgress
            variant="determinate"
            value={(session.progress.current / session.progress.max) * 100}
            color="secondary"
            sx={{ mt: 0.5, borderRadius: 1, height: 6 }}
          />
        </Box>
        <QuestionCard
          stem={session.question.stem}
          options={session.question.options}
          onAnswer={(key) => submitAnswer(key)}
          disabled={phase === 'answering'}
        />
        {phase === 'answering' && (
          <Box textAlign="center" mt={2}><CircularProgress size={24} color="secondary" /></Box>
        )}
      </Box>
    );
  }

  return null;
}
