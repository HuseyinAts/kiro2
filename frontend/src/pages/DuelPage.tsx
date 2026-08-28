/**
 * DuelPage — /duel
 * 1v1 Düello. POST /api/v1/duel/matchmake → session → SSE events → answer
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import {
  Alert, Box, Button, Card, CardContent, Chip,
  CircularProgress, Divider, LinearProgress,
  Stack, Typography,
} from '@mui/material';
import {
  Person, SportsEsports,
  Timer,
} from '@mui/icons-material';
import { apiRequest } from '../utils/apiHelpers';

// ── Types ────────────────────────────────────────────────────────────────────
type Phase = 'lobby' | 'queued' | 'playing' | 'result';

interface Question {
  id: string;
  text: string;
  options: Record<string, string>;
  order: number;
}

interface DuelState {
  session_id: string;
  my_score: number;
  opp_score: number;
  question: Question | null;
  q_index: number;
  total_q: number;
  time_left: number;
}

interface DuelResult {
  won: boolean; draw: boolean;
  my_score: number; opp_score: number;
  elo_change: number;
}

const SUBJECTS = [
  { id: 'MATEMATIK', name: 'Matematik', emoji: '📐' },
  { id: 'TURKCE',    name: 'Türkçe',    emoji: '📖' },
  { id: 'FEN',       name: 'Fen',       emoji: '🔬' },
  { id: 'FIZIK',     name: 'Fizik',     emoji: '⚛️' },
  { id: 'KIMYA',     name: 'Kimya',     emoji: '🧪' },
  { id: 'BIYOLOJI',  name: 'Biyoloji',  emoji: '🧬' },
];

// ── Main Component ───────────────────────────────────────────────────────────
export default function DuelPage() {
  const [phase,   setPhase]   = useState<Phase>('lobby');
  const [subject, setSubject] = useState('MATEMATIK');
  const [duel,    setDuel]    = useState<DuelState | null>(null);
  const [result,  setResult]  = useState<DuelResult | null>(null);
  const [selected,setSelected]= useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState<string | null>(null);
  const [rating,  setRating]  = useState<number>(1200);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const pollRef  = useRef<NodeJS.Timeout | null>(null);

  // Elo rating al
  useEffect(() => {
    apiRequest<{elo_rating:number}>('/api/v1/duel/rating')
      .then(r => setRating(Math.round(r.elo_rating)))
      .catch(() => {});
    return () => {
      clearInterval(pollRef.current!);
      clearInterval(timerRef.current!);
    };
  }, []);

  // Matchmaking başlat
  const startMatchmaking = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const r = await apiRequest<{status:string;session_id:string|null;message:string}>(
        '/api/v1/duel/matchmake',
        { method:'POST', body: JSON.stringify({ subject }) },
      );
      if (r.status === 'matched' && r.session_id) {
        await loadDuelSession(r.session_id);
      } else {
        setPhase('queued');
        // Poll every 3s for match
        pollRef.current = setInterval(async () => {
          try {
            const pr = await apiRequest<{status:string;session_id:string|null;message:string}>(
              '/api/v1/duel/matchmake',
              { method:'POST', body: JSON.stringify({ subject }) },
            );
            if (pr.status === 'matched' && pr.session_id) {
              clearInterval(pollRef.current!);
              await loadDuelSession(pr.session_id);
            }
          } catch {}
        }, 3000);
      }
    } catch (e:any) { setError(String(e?.message ?? e)); }
    finally { setLoading(false); }
  }, [subject]);

  const loadDuelSession = async (session_id: string) => {
    // Fetch first question via SSE events endpoint (simplified: HTTP fallback)
    try {
      const q = await apiRequest<{question:Question;total:number}>(
        `/api/v1/duel/${session_id}/current-question`,
      );
      setDuel({ session_id, my_score:0, opp_score:0, question:q.question,
                q_index:0, total_q:q.total, time_left:30 });
      setPhase('playing');
      startTimer(session_id, 0);
    } catch {
      // Fallback: SSE ile dinle
      setDuel({ session_id, my_score:0, opp_score:0, question:null,
                q_index:0, total_q:5, time_left:30 });
      setPhase('playing');
    }
  };

  const startTimer = (session_id: string, qIdx: number) => {
    setDuel(prev => prev ? { ...prev, time_left:30 } : prev);
    timerRef.current = setInterval(() => {
      setDuel(prev => {
        if (!prev) {return prev;}
        if (prev.time_left <= 1) {
          clearInterval(timerRef.current!);
          submitAnswer(session_id, qIdx, 'X', 30000); // timeout
          return { ...prev, time_left:0 };
        }
        return { ...prev, time_left: prev.time_left - 1 };
      });
    }, 1000);
  };

  const submitAnswer = async (session_id: string, qIdx: number, ans: string, ms: number) => {
    clearInterval(timerRef.current!);
    setSelected(ans);
    try {
      const r = await apiRequest<{round_complete:boolean;player1_score:number;player2_score:number;is_correct:boolean}>(
        `/api/v1/duel/${session_id}/answer`,
        { method:'POST', body: JSON.stringify({ question_order:qIdx, answer:ans, time_ms:ms }) },
      );
      setDuel(prev => prev ? { ...prev, my_score:r.player1_score, opp_score:r.player2_score } : prev);
      if (r.round_complete) {
        // Tüm sorular bitti — sonuç al
        setTimeout(() => fetchResult(session_id), 1000);
      } else {
        // Sonraki soru
        setTimeout(async () => {
          try {
            const q = await apiRequest<{question:Question;total:number}>(
              `/api/v1/duel/${session_id}/current-question`,
            );
            setDuel(prev => prev ? { ...prev, question:q.question, q_index:qIdx+1, time_left:30 } : prev);
            setSelected(null);
            startTimer(session_id, qIdx+1);
          } catch {}
        }, 1200);
      }
    } catch {}
  };

  const fetchResult = async (session_id: string) => {
    try {
      const r = await apiRequest<DuelResult>(`/api/v1/duel/${session_id}/result`);
      setResult(r); setPhase('result');
    } catch {
      setResult({ won:false, draw:true, my_score:0, opp_score:0, elo_change:0 });
      setPhase('result');
    }
  };

  const reset = () => {
    clearInterval(timerRef.current!); clearInterval(pollRef.current!);
    setPhase('lobby'); setDuel(null); setResult(null); setSelected(null); setError(null);
  };

  // ── LOBBY ─────────────────────────────────────────────────────────────────
  if (phase === 'lobby') {return (
    <Box maxWidth={520} mx="auto" py={4}>
      <Card elevation={2} sx={{ borderRadius: 3, p: 1 }}>
        <CardContent>
          <Stack spacing={2} alignItems="center" mb={3}>
            <SportsEsports sx={{ fontSize: 52, color: 'primary.main' }} />
            <Typography variant="h5" fontWeight={700}>1v1 Düello</Typography>
            <Stack direction="row" spacing={1} alignItems="center">
              <Person fontSize="small" />
              <Typography variant="body2">ELO: {rating}</Typography>
            </Stack>
          </Stack>

          <Typography variant="subtitle2" fontWeight={600} mb={1}>Ders seç</Typography>
          <Box display="flex" flexWrap="wrap" gap={1} mb={3}>
            {SUBJECTS.map(s => (
              <Chip key={s.id} label={`${s.emoji} ${s.name}`}
                onClick={() => setSubject(s.id)}
                color={subject === s.id ? 'primary' : 'default'}
                variant={subject === s.id ? 'filled' : 'outlined'} />
            ))}
          </Box>

          {error && <Alert severity="error" sx={{ mb:2 }}>{error}</Alert>}

          <Button fullWidth variant="contained" size="large"
            startIcon={loading ? <CircularProgress size={20} /> : <SportsEsports />}
            disabled={loading} onClick={startMatchmaking}
            sx={{ borderRadius: 2, py: 1.5 }}>
            Düello Başlat
          </Button>
          <Typography variant="caption" color="text.secondary" display="block" textAlign="center" mt={1}>
            5 soruluk hızlı düello · Doğru cevap = +1 puan
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );}

  // ── QUEUED ────────────────────────────────────────────────────────────────
  if (phase === 'queued') {return (
    <Box maxWidth={400} mx="auto" py={6} textAlign="center">
      <CircularProgress size={64} />
      <Typography variant="h6" mt={3} fontWeight={600}>Rakip Aranıyor...</Typography>
      <Typography variant="body2" color="text.secondary" mt={1}>
        Sana uygun seviyede rakip bulunuyor
      </Typography>
      <Button variant="outlined" sx={{ mt: 3 }} onClick={reset}>İptal</Button>
    </Box>
  );}

  // ── PLAYING ───────────────────────────────────────────────────────────────
  if (phase === 'playing' && duel) {
    const pct = duel.time_left / 30 * 100;
    return (
      <Box maxWidth={680} mx="auto" py={2}>
        {/* Skor */}
        <Card sx={{ mb: 2, borderRadius: 2 }}>
          <CardContent sx={{ py: 1.5, '&:last-child':{ pb:1.5 } }}>
            <Stack direction="row" justifyContent="space-between" alignItems="center">
              <Stack direction="row" spacing={1} alignItems="center">
                <Person color="primary" />
                <Typography fontWeight={700} fontSize={20}>{duel.my_score}</Typography>
                <Typography color="text.secondary">Sen</Typography>
              </Stack>
              <Stack direction="row" spacing={1} alignItems="center">
                <Timer color={pct < 30 ? 'error' : 'action'} />
                <Typography fontWeight={700} color={pct < 30 ? 'error.main' : 'text.primary'}>
                  {duel.time_left}s
                </Typography>
              </Stack>
              <Stack direction="row" spacing={1} alignItems="center">
                <Typography color="text.secondary">Rakip</Typography>
                <Typography fontWeight={700} fontSize={20}>{duel.opp_score}</Typography>
                <Person />
              </Stack>
            </Stack>
            <LinearProgress variant="determinate" value={pct}
              color={pct < 30 ? 'error' : 'primary'}
              sx={{ mt: 1, height: 4, borderRadius: 2 }} />
          </CardContent>
        </Card>

        {/* Soru */}
        {duel.question ? (
          <Card elevation={2} sx={{ borderRadius: 3, mb: 2 }}>
            <CardContent sx={{ p: 3 }}>
              <Stack direction="row" justifyContent="space-between" mb={2}>
                <Chip size="small" label={`Soru ${duel.q_index+1}/${duel.total_q}`} />
                <Chip size="small" label={subject} variant="outlined" />
              </Stack>
              <Typography variant="h6" fontWeight={600} mb={3} lineHeight={1.6}>
                {duel.question.text}
              </Typography>
              <Stack spacing={1.5}>
                {Object.entries(duel.question.options).filter(([,v])=>v).map(([key,val])=>(
                  <Button key={key}
                    variant={selected===key ? 'contained' : 'outlined'}
                    color={selected===key ? 'primary' : 'inherit'}
                    sx={{ justifyContent:'flex-start', textAlign:'left',
                          textTransform:'none', py:1.5, px:2, borderRadius:2 }}
                    disabled={!!selected}
                    onClick={() => submitAnswer(duel.session_id, duel.q_index, key, (30-duel.time_left)*1000)}>
                    <strong>{key})</strong>&nbsp;{val}
                  </Button>
                ))}
              </Stack>
            </CardContent>
          </Card>
        ) : (
          <Box textAlign="center" py={4}>
            <CircularProgress />
            <Typography mt={2} color="text.secondary">Soru yükleniyor...</Typography>
          </Box>
        )}
      </Box>
    );
  }

  // ── RESULT ────────────────────────────────────────────────────────────────
  if (phase === 'result' && result) {return (
    <Box maxWidth={440} mx="auto" py={4}>
      <Card elevation={2} sx={{ borderRadius: 3, p:1, textAlign:'center' }}>
        <CardContent>
          <Typography fontSize={64}>
            {result.won ? '🏆' : result.draw ? '🤝' : '😔'}
          </Typography>
          <Typography variant="h4" fontWeight={800} mt={1}>
            {result.won ? 'Kazandın!' : result.draw ? 'Berabere!' : 'Kaybettin'}
          </Typography>
          <Stack direction="row" spacing={3} justifyContent="center" mt={3}>
            <Box textAlign="center">
              <Typography variant="h4" fontWeight={700} color="primary.main">{result.my_score}</Typography>
              <Typography variant="caption" color="text.secondary">Senin puanın</Typography>
            </Box>
            <Divider orientation="vertical" flexItem />
            <Box textAlign="center">
              <Typography variant="h4" fontWeight={700}>{result.opp_score}</Typography>
              <Typography variant="caption" color="text.secondary">Rakip puanı</Typography>
            </Box>
          </Stack>
          <Chip sx={{ mt:2 }}
            label={`ELO: ${result.elo_change >= 0 ? '+' : ''}${result.elo_change}`}
            color={result.elo_change > 0 ? 'success' : 'error'} />
          <Box mt={3}>
            <Button fullWidth variant="contained" onClick={reset} sx={{ borderRadius:2 }}>
              Tekrar Oyna
            </Button>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );}

  return null;
}
