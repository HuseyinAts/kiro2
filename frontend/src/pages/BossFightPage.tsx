/**
 * BossFightPage -- /boss-fight/:realmSlug
 * Konu bazli boss savasi: HP bar, timer, zorlastirilan sorular.
 * Boss 100 HP baslar. Dogru cevap -20 HP, yanlis cevap bossa +10 HP.
 * Oyuncunun 3 cani var. Timer 30s/soru.
 */
import { useEffect, useState, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box, Button, Card, CardContent, Chip, CircularProgress,
  LinearProgress, Stack, Typography, Alert,
} from '@mui/material';
import { Favorite, FavoriteBorder, Timer, EmojiEvents } from '@mui/icons-material';
import { apiRequest } from '../utils/apiHelpers';

interface BossQuestion {
  question_id: string;
  stem: string;
  options: Record<string, string>;
  correct_answer?: string;
}

const BOSS_PROFILES: Record<string, { name: string; emoji: string; color: string }> = {
  matematik: { name: 'Kaos Sayici', emoji: '🧮', color: '#6366f1' },
  fizik: { name: 'Karanlik Kuvvet', emoji: '⚡', color: '#06b6d4' },
  kimya: { name: 'Zehirli Bilesen', emoji: '☠️', color: '#f59e0b' },
  biyoloji: { name: 'Mutant Hucre', emoji: '🧬', color: '#10b981' },
  turkce: { name: 'Kelime Canavari', emoji: '📜', color: '#ec4899' },
  tarih: { name: 'Zaman Bukucu', emoji: '⏳', color: '#f97316' },
};
const DEFAULT_BOSS = { name: 'Bilinmeyen Boss', emoji: '👹', color: '#ef4444' };

export default function BossFightPage() {
  const { realmSlug = 'matematik' } = useParams<{ realmSlug: string }>();
  const navigate = useNavigate();
  const boss = BOSS_PROFILES[realmSlug] ?? DEFAULT_BOSS;

  const [questions, setQuestions] = useState<BossQuestion[]>([]);
  const [idx, setIdx] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Game state
  const [bossHP, setBossHP] = useState(100);
  const [playerLives, setPlayerLives] = useState(3);
  const [timer, setTimer] = useState(30);
  const [selected, setSelected] = useState<string | null>(null);
  const [revealed, setRevealed] = useState(false);
  const [gameOver, setGameOver] = useState(false);
  const [victory, setVictory] = useState(false);
  const [correctCount, setCorrectCount] = useState(0);
  const [totalAnswered, setTotalAnswered] = useState(0);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const questAdvancedRef = useRef(false);

  // Fetch questions
  useEffect(() => {
    const subject = realmSlug.toUpperCase();
    apiRequest<{ questions?: BossQuestion[]; data?: BossQuestion[] }>(
      `/api/v1/soru-bankasi/random?subject_area=${subject}&limit=10&difficulty=hard`
    )
      .then(res => {
        const qs = res.questions ?? res.data ?? [];
        if (Array.isArray(qs) && qs.length > 0) setQuestions(qs);
        else setError('Bu konu icin boss sorulari bulunamadi.');
      })
      .catch(e => setError(String(e)))
      .finally(() => setLoading(false));
  }, [realmSlug]);

  // Timer
  useEffect(() => {
    if (loading || gameOver || victory || revealed) return;
    timerRef.current = setInterval(() => {
      setTimer(prev => {
        if (prev <= 1) {
          // Zaman doldu — yanlis sayilir
          handleTimeout();
          return 30;
        }
        return prev - 1;
      });
    }, 1000);
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loading, gameOver, victory, revealed, idx]);

  const handleTimeout = useCallback(() => {
    setRevealed(true);
    setPlayerLives(prev => {
      const next = prev - 1;
      if (next <= 0) setGameOver(true);
      return next;
    });
    setBossHP(prev => Math.min(prev + 10, 100));
    setTotalAnswered(t => t + 1);
  }, []);

  const handleSelect = (key: string) => {
    if (revealed || gameOver || victory) return;
    setSelected(key);
    setRevealed(true);
    if (timerRef.current) clearInterval(timerRef.current);

    // Check correctness (simplified — correct_answer may not be provided, use first option as placeholder)
    const q = questions[idx];
    const isCorrect = q.correct_answer ? key === q.correct_answer : false;

    setTotalAnswered(t => t + 1);

    if (isCorrect) {
      setCorrectCount(c => c + 1);
      setBossHP(prev => {
        const next = Math.max(prev - 20, 0);
        if (next <= 0) {
          setVictory(true);
          // Report quest advancement (once only)
          if (!questAdvancedRef.current) {
            questAdvancedRef.current = true;
            apiRequest(`/api/v1/realms/${realmSlug}/quest-chain/advance`, { method: 'POST' }).catch(() => {});
          }
        }
        return next;
      });
    } else {
      setPlayerLives(prev => {
        const next = prev - 1;
        if (next <= 0) setGameOver(true);
        return next;
      });
      setBossHP(prev => Math.min(prev + 10, 100));
    }
  };

  const nextQuestion = () => {
    if (idx + 1 >= questions.length) {
      // Sorular bitti — dogru orana gore karar ver
      if (bossHP <= 0) setVictory(true);
      else setGameOver(true);
      return;
    }
    setIdx(i => i + 1);
    setSelected(null);
    setRevealed(false);
    setTimer(30);
  };

  if (loading) return (
    <Box textAlign="center" py={8}>
      <CircularProgress size={52} />
      <Typography mt={2} color="text.secondary">Boss hazirlaniyor...</Typography>
    </Box>
  );

  if (error) return (
    <Box maxWidth={520} mx="auto" mt={4}>
      <Alert severity="error">{error}</Alert>
      <Button sx={{ mt: 2 }} onClick={() => navigate('/realms')}>Alemlere Don</Button>
    </Box>
  );

  // Victory screen
  if (victory) return (
    <Box maxWidth={520} mx="auto" mt={4} textAlign="center">
      <Typography fontSize={64}>{boss.emoji}</Typography>
      <Typography variant="h4" fontWeight={800} color="success.main" mt={1}>
        Boss Yenildi!
      </Typography>
      <Typography variant="h6" mt={1}>{boss.name} alt edildi!</Typography>
      <Stack direction="row" spacing={2} justifyContent="center" mt={3}>
        <Chip icon={<EmojiEvents />} label={`${correctCount}/${totalAnswered} Dogru`} color="success" />
        <Chip label={`${playerLives} Can Kaldi`} color="primary" />
      </Stack>
      <Button variant="contained" sx={{ mt: 3 }} onClick={() => navigate(`/realms`)}>
        Alemlere Don
      </Button>
    </Box>
  );

  // Game over screen
  if (gameOver) return (
    <Box maxWidth={520} mx="auto" mt={4} textAlign="center">
      <Typography fontSize={64}>💀</Typography>
      <Typography variant="h4" fontWeight={800} color="error.main" mt={1}>
        Yenildin!
      </Typography>
      <Typography variant="body1" mt={1}>{boss.name} kazandi. Tekrar dene!</Typography>
      <Stack direction="row" spacing={2} justifyContent="center" mt={3}>
        <Chip label={`${correctCount}/${totalAnswered} Dogru`} variant="outlined" />
        <Chip label={`Boss HP: ${bossHP}`} color="error" variant="outlined" />
      </Stack>
      <Stack direction="row" spacing={2} justifyContent="center" mt={2}>
        <Button variant="outlined" onClick={() => navigate('/realms')}>Alemlere Don</Button>
        <Button variant="contained" onClick={() => window.location.reload()}>Tekrar Dene</Button>
      </Stack>
    </Box>
  );

  const q = questions[idx];

  return (
    <Box maxWidth={680} mx="auto" py={3}>
      {/* Boss Header */}
      <Card sx={{ mb: 2, borderRadius: 3, background: `linear-gradient(135deg, ${boss.color}22, ${boss.color}11)`, border: `1px solid ${boss.color}44` }}>
        <CardContent sx={{ py: 2 }}>
          <Stack direction="row" alignItems="center" spacing={2}>
            <Typography fontSize={40}>{boss.emoji}</Typography>
            <Box flex={1}>
              <Typography variant="subtitle2" fontWeight={800} color={boss.color}>
                {boss.name}
              </Typography>
              {/* Boss HP bar */}
              <LinearProgress
                variant="determinate" value={bossHP}
                color="error"
                sx={{ height: 12, borderRadius: 6, mt: 0.5, bgcolor: '#1e293b' }}
              />
              <Typography variant="caption" color="text.secondary">
                HP: {bossHP}/100
              </Typography>
            </Box>
            {/* Player lives */}
            <Stack direction="row" spacing={0.5}>
              {Array.from({ length: 3 }).map((_, i) => (
                i < playerLives
                  ? <Favorite key={i} color="error" />
                  : <FavoriteBorder key={i} sx={{ color: 'text.disabled' }} />
              ))}
            </Stack>
          </Stack>
        </CardContent>
      </Card>

      {/* Timer + Progress */}
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={1}>
        <Chip
          icon={<Timer />}
          label={`${timer}s`}
          color={timer <= 10 ? 'error' : 'default'}
          variant="outlined"
        />
        <Typography variant="caption" color="text.secondary">
          Soru {idx + 1}/{questions.length}
        </Typography>
      </Stack>

      {/* Question Card */}
      <Card elevation={2} sx={{ borderRadius: 3, mb: 2 }}>
        <CardContent sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight={600} mb={3} sx={{ lineHeight: 1.6 }}>
            {q.stem ?? 'Soru metni yukleniyor...'}
          </Typography>

          {q.options && (
            <Stack spacing={1.5}>
              {Object.entries(q.options).filter(([, v]) => v).map(([key, val]) => {
                const isSelected = selected === key;
                const isCorrect = revealed && q.correct_answer === key;
                let btnColor: 'primary' | 'success' | 'error' | 'inherit' = 'inherit';
                if (revealed && isCorrect) btnColor = 'success';
                else if (revealed && isSelected && !isCorrect) btnColor = 'error';
                else if (isSelected) btnColor = 'primary';

                return (
                  <Button
                    key={key}
                    variant={isSelected || (revealed && isCorrect) ? 'contained' : 'outlined'}
                    color={btnColor}
                    sx={{
                      justifyContent: 'flex-start', textAlign: 'left',
                      textTransform: 'none', py: 1.5, px: 2,
                      borderRadius: 2,
                    }}
                    onClick={() => handleSelect(key)}
                    disabled={revealed}
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

      {/* Next button after reveal */}
      {revealed && !gameOver && !victory && (
        <Box textAlign="center">
          <Button variant="contained" size="large" onClick={nextQuestion} sx={{ borderRadius: 2 }}>
            Sonraki Soru
          </Button>
        </Box>
      )}
    </Box>
  );
}
