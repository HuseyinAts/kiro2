/**
 * FSRSReviewPage — /fsrs-review
 * Vadesi gelen kartları gösterir. FSRS Anki-benzeri tekrar akışı.
 */
import { useEffect, useState, useCallback } from 'react';
import {
  Box, Button, Card, CardContent, Chip, CircularProgress,
  LinearProgress, Stack, Typography, Alert, Paper,
} from '@mui/material';
import { CheckCircle, Cancel, Replay, EmojiEvents } from '@mui/icons-material';
import { apiRequest } from '../utils/apiHelpers';
import { FlagButton } from '../components/Quality/FlagButton';

interface DueCard {
  question_id: string;
  stem:        string | null;
  options:     Record<string, string> | null;
  subject_id:  string | null;
  stability:   number;
  difficulty:  number;
  reps:        number;
  lapses:      number;
  state:       number;
  urgency_score: number;
}

const SUBJECT_LABELS: Record<string, string> = {
  MATEMATIK: 'Matematik', TURKCE: 'Türkçe', FEN: 'Fen',
  FIZIK: 'Fizik', KIMYA: 'Kimya', BIYOLOJI: 'Biyoloji',
  TARIH: 'Tarih', COGRAFYA: 'Coğrafya', EDEBIYAT: 'Edebiyat',
};

export default function FSRSReviewPage() {
  const [cards,      setCards]      = useState<DueCard[]>([]);
  const [idx,        setIdx]        = useState(0);
  const [loading,    setLoading]    = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [revealed,   setRevealed]   = useState(false);
  const [selected,   setSelected]   = useState<string | null>(null);
  const [done,       setDone]       = useState(false);
  const [correct,    setCorrect]    = useState(0);
  const [wrong,      setWrong]      = useState(0);
  const [error,      setError]      = useState<string | null>(null);

  useEffect(() => {
    apiRequest<DueCard[]>('/api/v1/fsrs/due?limit=20')
      .then(data => { setCards(data); setLoading(false); })
      .catch(e => { setError(String(e?.message ?? e)); setLoading(false); });
  }, []);

  const submitAnswer = useCallback(async (isCorrect: boolean) => {
    const card = cards[idx];
    if (!card || submitting) return;
    setSubmitting(true);
    try {
      await apiRequest('/api/v1/fsrs/review', {
        method: 'POST',
        body: JSON.stringify({ question_id: card.question_id, is_correct: isCorrect }),
      });
      if (isCorrect) setCorrect(c => c + 1); else setWrong(c => c + 1);
      if (idx + 1 >= cards.length) setDone(true);
      else { setIdx(i => i + 1); setRevealed(false); setSelected(null); }
    } catch (e) { setError(String(e)); }
    finally { setSubmitting(false); }
  }, [cards, idx, submitting]);

  if (loading) return (
    <Box textAlign="center" py={8}><CircularProgress size={52} />
      <Typography mt={2} color="text.secondary">Tekrar kartları yükleniyor...</Typography>
    </Box>
  );

  if (error) return (
    <Box maxWidth={520} mx="auto" mt={4}>
      <Alert severity="error">{error}</Alert>
    </Box>
  );

  if (cards.length === 0) return (
    <Box maxWidth={520} mx="auto" mt={4}>
      <Alert severity="success" icon={<EmojiEvents />}>
        <Typography fontWeight={700}>Tebrikler! 🎉</Typography>
        <Typography variant="body2">Bugün için vadesi gelen kart yok. Yarın tekrar kontrol et.</Typography>
      </Alert>
    </Box>
  );

  if (done) return (
    <Box maxWidth={520} mx="auto" mt={4}>
      <Paper elevation={2} sx={{ p: 4, borderRadius: 3, textAlign: 'center' }}>
        <EmojiEvents sx={{ fontSize: 52, color: 'primary.main' }} />
        <Typography variant="h5" fontWeight={700} mt={1}>Oturum Tamamlandı!</Typography>
        <Stack direction="row" spacing={2} justifyContent="center" mt={3}>
          <Chip icon={<CheckCircle />} label={`${correct} Doğru`} color="success" />
          <Chip icon={<Cancel />}      label={`${wrong} Yanlış`}  color="error"   />
          <Chip label={`${cards.length} Kart`} variant="outlined" />
        </Stack>
        <Typography variant="body2" color="text.secondary" mt={2}>
          Başarı oranı: %{Math.round((correct / cards.length) * 100)}
        </Typography>
        <Button variant="outlined" sx={{ mt: 3 }} onClick={() => window.location.reload()}>
          Tekrar Çalış
        </Button>
      </Paper>
    </Box>
  );

  const card = cards[idx];
  const progress = ((idx) / cards.length) * 100;

  return (
    <Box maxWidth={680} mx="auto" py={3}>
      {/* Progress */}
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={1}>
        <Typography variant="caption" color="text.secondary">
          {idx + 1} / {cards.length} kart
        </Typography>
        <Stack direction="row" spacing={1}>
          {card.subject_id && (
            <Chip size="small" label={SUBJECT_LABELS[card.subject_id] ?? card.subject_id} />
          )}
          <Chip size="small" label={`Tekrar: ${card.reps}`} variant="outlined" />
          <Chip size="small" label={`Hata: ${card.lapses}`}
            color={card.lapses > 3 ? 'error' : 'default'} variant="outlined" />
        </Stack>
      </Stack>
      <LinearProgress variant="determinate" value={progress}
        sx={{ mb: 2, height: 6, borderRadius: 3 }} />

      {/* Soru kartı */}
      <Card elevation={2} sx={{ borderRadius: 3, mb: 2 }}>
        <CardContent sx={{ p: 3 }}>
          <Stack direction="row" alignItems="flex-start" justifyContent="space-between" spacing={1} mb={3}>
            <Typography variant="h6" fontWeight={600} sx={{ lineHeight: 1.6, flex: 1 }}>
              {card.stem ?? 'Soru metni yükleniyor...'}
            </Typography>
            <FlagButton questionId={card.question_id} />
          </Stack>

          {/* Seçenekler */}
          {card.options && (
            <Stack spacing={1.5}>
              {Object.entries(card.options).filter(([, v]) => v).map(([key, val]) => {
                const isSelected = selected === key;
                const _isCorrectOpt = revealed && selected && key === Object.entries(card.options!)
                  .find(() => false)?.[ 0]; // correct_answer gizli — seçim sonrası revealed
                void _isCorrectOpt; // TODO: implement correct answer highlighting
                return (
                  <Button
                    key={key}
                    variant={isSelected ? 'contained' : 'outlined'}
                    color={isSelected ? 'primary' : 'inherit'}
                    sx={{
                      justifyContent: 'flex-start', textAlign: 'left',
                      textTransform: 'none', py: 1.5, px: 2,
                      borderRadius: 2, fontWeight: isSelected ? 700 : 400,
                    }}
                    onClick={() => { setSelected(key); setRevealed(true); }}
                    disabled={revealed && !isSelected}
                  >
                    <Typography variant="body1">
                      <strong>{key})</strong>&nbsp;{val}
                    </Typography>
                  </Button>
                );
              })}
            </Stack>
          )}
        </CardContent>
      </Card>

      {/* Yanıt düğmeleri — seçim yapıldıktan sonra göster */}
      {revealed ? (
        <Stack direction="row" spacing={2} justifyContent="center">
          <Button size="large" variant="contained" color="error"
            startIcon={<Replay />} disabled={submitting}
            onClick={() => submitAnswer(false)} sx={{ minWidth: 160, borderRadius: 2 }}>
            Tekrar Et
          </Button>
          <Button size="large" variant="contained" color="success"
            startIcon={<CheckCircle />} disabled={submitting}
            onClick={() => submitAnswer(true)} sx={{ minWidth: 160, borderRadius: 2 }}>
            Bildim
          </Button>
        </Stack>
      ) : (
        <Box textAlign="center">
          <Typography variant="body2" color="text.secondary">
            Bir seçenek seç — sonra Bildim / Tekrar Et düğmesi çıkar
          </Typography>
        </Box>
      )}

      {submitting && <Box textAlign="center" mt={2}><CircularProgress size={28} /></Box>}
    </Box>
  );
}
