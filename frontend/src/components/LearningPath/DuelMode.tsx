/**
 * DuelMode — F1 1v1 Düello
 *
 * @TODO S179 fix (B-P1-21): 1,072 LOC, 17 useState, 0 useMemo. Sprint
 * plan: useReducer for game-state machine + child split (DuelArena,
 * DuelHud, DuelTimer, DuelResults). Do NOT add new useState here.
 *
 * İki mod:
 *   1. "Rakip Bul" — POST /api/v1/duel/matchmake ile gerçek eşleşme, SSE stream.
 *   2. "AI Bot" — API yokken çevrimdışı fallback (mevcut davranış).
 *
 * SSE events işlenir: match_found, question, opponent_answered, duel_complete.
 * ELO puanı GET /api/v1/duel/rating endpoint'inden yüklenir.
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import {
  Box,
  Typography,
  Button,
  Chip,
  LinearProgress,
  CircularProgress,
  Alert,
  Divider,
} from '@mui/material';
import {
  SportsEsports,
  Person,
  SmartToy,
  EmojiEvents,
  CheckCircle,
  Cancel,
  Wifi,
  WifiOff,
} from '@mui/icons-material';
import { GlassCard } from '../ui/GlassCard';
import { apiRequest } from '../../utils/apiHelpers';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface DuelQuestion {
  id: string;
  content: string;
  options: { key: string; text: string }[];
  subject: string;
  difficulty?: number;
}

interface DuelRating {
  elo_rating: number;
  wins: number;
  losses: number;
  draws: number;
  peak_rating: number;
}

/** Backend MatchmakeResponse */
interface MatchmakeResponse {
  status: 'matched' | 'queued';
  session_id: string | null;
  message: string;
}

/** Backend DuelAnswerResponse */
interface DuelAnswerResponse {
  round_complete: boolean;
  question_order: number;
  player1_score: int;
  player2_score: int;
  is_correct: boolean;
}

// Fix: TypeScript doesn't know `int` — use number
type int = number;

type DuelPhase =
  | 'idle'          // Başlangıç ekranı
  | 'matchmaking'   // Rakip aranıyor
  | 'waiting'       // Kuyrukta, SSE dinliyor
  | 'playing'       // Soru aktif
  | 'round_result'  // Tur sonucu gösteriliyor
  | 'finished'      // Düello bitti
  | 'ai_playing';   // AI bot modu

interface RoundResult {
  questionOrder: int;
  myAnswer: string;
  isCorrect: boolean;
  myScore: int;
  opponentScore: int;
  opponentAnswered: boolean;
}

// ---------------------------------------------------------------------------
// AI Bot mock data (fallback when no real opponent)
// ---------------------------------------------------------------------------

const AI_BOT_QUESTIONS: DuelQuestion[] = [
  {
    id: 'ai-q1',
    content: 'Bir otomobil 90 km/s sabit hızla 2 saat yol alıyor. Kaç km yol almıştır?',
    options: [
      { key: 'A', text: '45 km' },
      { key: 'B', text: '92 km' },
      { key: 'C', text: '180 km' },
      { key: 'D', text: '360 km' },
      { key: 'E', text: '450 km' },
    ],
    subject: 'Fizik',
  },
  {
    id: 'ai-q2',
    content: 'x² - 5x + 6 = 0 denkleminin kökleri nelerdir?',
    options: [
      { key: 'A', text: '1 ve 6' },
      { key: 'B', text: '2 ve 3' },
      { key: 'C', text: '-2 ve -3' },
      { key: 'D', text: '3 ve 5' },
      { key: 'E', text: '-1 ve -6' },
    ],
    subject: 'Matematik',
  },
  {
    id: 'ai-q3',
    content: 'Türkiye\'nin en uzun nehri hangisidir?',
    options: [
      { key: 'A', text: 'Sakarya' },
      { key: 'B', text: 'Fırat' },
      { key: 'C', text: 'Kızılırmak' },
      { key: 'D', text: 'Dicle' },
      { key: 'E', text: 'Yeşilırmak' },
    ],
    subject: 'Coğrafya',
  },
  {
    id: 'ai-q4',
    content: '2³ × 2⁴ işleminin sonucu kaçtır?',
    options: [
      { key: 'A', text: '2⁷' },
      { key: 'B', text: '4⁷' },
      { key: 'C', text: '2¹²' },
      { key: 'D', text: '8⁷' },
      { key: 'E', text: '2⁻¹' },
    ],
    subject: 'Matematik',
  },
  {
    id: 'ai-q5',
    content: 'Osmanlı Devleti hangi yılda kurulmuştur?',
    options: [
      { key: 'A', text: '1071' },
      { key: 'B', text: '1243' },
      { key: 'C', text: '1299' },
      { key: 'D', text: '1453' },
      { key: 'E', text: '1520' },
    ],
    subject: 'Tarih',
  },
];

const AI_BOT_CORRECT: Record<string, string> = {
  'ai-q1': 'C',
  'ai-q2': 'B',
  'ai-q3': 'C',
  'ai-q4': 'A',
  'ai-q5': 'C',
};

function aiBotAnswer(questionId: string): string {
  // AI bot doğru cevabı %70 ihtimalle verir
  const correct = AI_BOT_CORRECT[questionId] ?? 'A';
  const roll = Math.random();
  if (roll < 0.70) {return correct;}
  const options = ['A', 'B', 'C', 'D', 'E'].filter(o => o !== correct);
  return options[Math.floor(Math.random() * options.length)];
}

// ---------------------------------------------------------------------------
// Timer hook
// ---------------------------------------------------------------------------

function useCountdown(initialSeconds: int, active: boolean, onExpire: () => void) {
  const [seconds, setSeconds] = useState(initialSeconds);
  const expireRef = useRef(onExpire);
  expireRef.current = onExpire;

  useEffect(() => {
    if (!active) {
      setSeconds(initialSeconds);
      return;
    }
    setSeconds(initialSeconds);
    const interval = setInterval(() => {
      setSeconds(prev => {
        if (prev <= 1) {
          clearInterval(interval);
          expireRef.current();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(interval);
  }, [active, initialSeconds]);

  return seconds;
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

interface DuelModeProps {
  /** Subject for matchmaking (e.g. "MATEMATIK") */
  subject?: string;
}

const QUESTION_TIME_SEC = 30;

export function DuelMode({ subject = 'MATEMATIK' }: DuelModeProps) {
  // ------ Rating ------
  const [rating, setRating] = useState<DuelRating | null>(null);
  const [loadingRating, setLoadingRating] = useState(false);

  // ------ Matchmaking / session ------
  const [phase, setPhase] = useState<DuelPhase>('idle');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [useAiBot, setUseAiBot] = useState(false);
  const [matchmakeError, setMatchmakeError] = useState<string | null>(null);

  // ------ Scores ------
  const [myScore, setMyScore] = useState(0);
  const [opponentScore, setOpponentScore] = useState(0);
  const [opponentAnswered, setOpponentAnswered] = useState(false);

  // ------ Questions ------
  const [questions, setQuestions] = useState<DuelQuestion[]>([]);
  const [currentQIndex, setCurrentQIndex] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState<string | null>(null);
  const [roundResult, setRoundResult] = useState<RoundResult | null>(null);
  const [roundHistory, setRoundHistory] = useState<RoundResult[]>([]);
  const [answerSubmitting, setAnswerSubmitting] = useState(false);
  const questionStartMs = useRef<number>(Date.now());

  // ------ SSE ------
  const sseRef = useRef<EventSource | null>(null);

  // ------ Timer ------
  const timerActive = phase === 'playing' || phase === 'ai_playing';
  const timeLeft = useCountdown(QUESTION_TIME_SEC, timerActive, () => {
    if (timerActive && !selectedAnswer) {
      handleSubmitAnswer(null);
    }
  });

  // ------------------------------------------------------------------
  // Load ELO rating on mount
  // ------------------------------------------------------------------
  useEffect(() => {
    let cancelled = false;

    async function fetchRating() {
      setLoadingRating(true);
      try {
        const data = await apiRequest<DuelRating>('/api/v1/duel/rating');
        if (!cancelled) {setRating(data);}
      } catch {
        // Rating endpoint unavailable — show placeholder
      } finally {
        if (!cancelled) {setLoadingRating(false);}
      }
    }

    fetchRating();
    return () => { cancelled = true; };
  }, []);

  // ------------------------------------------------------------------
  // Clean up SSE on unmount
  // ------------------------------------------------------------------
  useEffect(() => {
    return () => {
      sseRef.current?.close();
    };
  }, []);

  // ------------------------------------------------------------------
  // SSE subscription
  // ------------------------------------------------------------------
  const subscribeSSE = useCallback((sid: string) => {
    sseRef.current?.close();

    const es = new EventSource(`/api/v1/duel/stream/${sid}`);
    sseRef.current = es;

    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleSseEvent(data);
      } catch {
        // Malformed event — ignore
      }
    };

    es.onerror = () => {
      // SSE error — close connection; game continues via polling if needed
      es.close();
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // ------------------------------------------------------------------
  // SSE event dispatcher
  // ------------------------------------------------------------------
  function handleSseEvent(data: Record<string, unknown>) {
    const type = data.type as string;

    switch (type) {
      case 'connected':
        // SSE stream established — server will push match_found next
        break;

      case 'match_found': {
        const qList = (data.questions as DuelQuestion[] | undefined) ?? [];
        setQuestions(qList.length > 0 ? qList : AI_BOT_QUESTIONS);
        setCurrentQIndex(0);
        setMyScore(0);
        setOpponentScore(0);
        setOpponentAnswered(false);
        setRoundHistory([]);
        setPhase('playing');
        questionStartMs.current = Date.now();
        break;
      }

      case 'question': {
        // Server pushing next question
        const q = data.question as DuelQuestion | undefined;
        if (q) {
          setQuestions(prev => {
            const next = [...prev];
            const idx = data.index as number ?? prev.length;
            next[idx] = q;
            return next;
          });
        }
        setCurrentQIndex(data.index as number ?? currentQIndex + 1);
        setSelectedAnswer(null);
        setOpponentAnswered(false);
        setPhase('playing');
        questionStartMs.current = Date.now();
        break;
      }

      case 'answer': {
        // Opponent submitted an answer
        const playerId = data.player_id as string;
        const isSelf = data.is_self as boolean | undefined;
        if (!isSelf && playerId) {
          setOpponentAnswered(true);
          setOpponentScore(data.player2_score as number ?? opponentScore);
        }
        break;
      }

      case 'opponent_answered':
        setOpponentAnswered(true);
        break;

      case 'round_complete': {
        setMyScore(data.player1_score as number ?? myScore);
        setOpponentScore(data.player2_score as number ?? opponentScore);
        break;
      }

      case 'finished':
      case 'duel_complete': {
        setMyScore(data.player1_score as number ?? myScore);
        setOpponentScore(data.player2_score as number ?? opponentScore);
        setPhase('finished');
        sseRef.current?.close();
        // Refresh ELO after game
        apiRequest<DuelRating>('/api/v1/duel/rating')
          .then(r => setRating(r))
          .catch(() => {});
        break;
      }

      default:
        break;
    }
  }

  // ------------------------------------------------------------------
  // Matchmaking
  // ------------------------------------------------------------------
  const handleFindMatch = useCallback(async () => {
    setPhase('matchmaking');
    setMatchmakeError(null);
    setMyScore(0);
    setOpponentScore(0);
    setRoundHistory([]);

    try {
      const result = await apiRequest<MatchmakeResponse>('/api/v1/duel/matchmake', {
        method: 'POST',
        body: JSON.stringify({ subject }),
      });

      if (result.status === 'matched' && result.session_id) {
        setSessionId(result.session_id);
        setUseAiBot(false);
        setPhase('waiting');
        subscribeSSE(result.session_id);
        // Give SSE 3s to deliver match_found; if not, fall through to playing with SSE
      } else {
        // Queued — wait for match via SSE
        // Create a temporary placeholder session; real session_id comes via SSE
        setPhase('waiting');
      }
    } catch {
      // API unavailable — fall back to AI bot
      setMatchmakeError(null);
      startAiBot();
    }
  }, [subject, subscribeSSE]); // eslint-disable-line react-hooks/exhaustive-deps

  // ------------------------------------------------------------------
  // AI Bot mode
  // ------------------------------------------------------------------
  const startAiBot = useCallback(() => {
    setUseAiBot(true);
    setSessionId(null);
    setQuestions(AI_BOT_QUESTIONS);
    setCurrentQIndex(0);
    setMyScore(0);
    setOpponentScore(0);
    setOpponentAnswered(false);
    setRoundHistory([]);
    setSelectedAnswer(null);
    setPhase('ai_playing');
    questionStartMs.current = Date.now();
  }, []);

  // ------------------------------------------------------------------
  // Answer submission
  // ------------------------------------------------------------------
  const handleSubmitAnswer = useCallback(async (answer: string | null) => {
    if (answerSubmitting) {return;}
    const elapsed = Date.now() - questionStartMs.current;
    const currentQ = questions[currentQIndex];
    if (!currentQ) {return;}

    setSelectedAnswer(answer ?? '');
    setAnswerSubmitting(true);

    if (useAiBot || !sessionId) {
      // AI bot logic — client-side correctness check
      const correct = AI_BOT_CORRECT[currentQ.id] ?? 'A';
      const isCorrect = answer !== null && answer === correct;
      const botAnswer = aiBotAnswer(currentQ.id);
      const botCorrect = botAnswer === correct;

      const newMyScore = myScore + (isCorrect ? 1 : 0);
      const newOppScore = opponentScore + (botCorrect ? 1 : 0);
      setMyScore(newMyScore);
      setOpponentScore(newOppScore);
      setOpponentAnswered(true);

      const result: RoundResult = {
        questionOrder: currentQIndex,
        myAnswer: answer ?? '',
        isCorrect,
        myScore: newMyScore,
        opponentScore: newOppScore,
        opponentAnswered: true,
      };
      setRoundResult(result);
      setRoundHistory(prev => [...prev, result]);
      setPhase('round_result');
      setAnswerSubmitting(false);
      return;
    }

    // Real multiplayer — POST to backend
    try {
      const res = await apiRequest<DuelAnswerResponse>(
        `/api/v1/duel/${sessionId}/answer`,
        {
          method: 'POST',
          body: JSON.stringify({
            question_order: currentQIndex,
            answer: answer ?? 'A',
            time_ms: elapsed,
          }),
        },
      );

      setMyScore(res.player1_score);
      setOpponentScore(res.player2_score);

      const result: RoundResult = {
        questionOrder: currentQIndex,
        myAnswer: answer ?? '',
        isCorrect: res.is_correct,
        myScore: res.player1_score,
        opponentScore: res.player2_score,
        opponentAnswered: res.round_complete,
      };
      setRoundResult(result);
      setRoundHistory(prev => [...prev, result]);

      if (res.round_complete) {
        setPhase('round_result');
      }
    } catch {
      // Server error — treat as incorrect, show round result
      const result: RoundResult = {
        questionOrder: currentQIndex,
        myAnswer: answer ?? '',
        isCorrect: false,
        myScore,
        opponentScore,
        opponentAnswered: false,
      };
      setRoundResult(result);
      setRoundHistory(prev => [...prev, result]);
      setPhase('round_result');
    } finally {
      setAnswerSubmitting(false);
    }
  }, [answerSubmitting, questions, currentQIndex, useAiBot, sessionId, myScore, opponentScore]);

  // ------------------------------------------------------------------
  // Advance to next round
  // ------------------------------------------------------------------
  const handleNextRound = useCallback(() => {
    const nextIdx = currentQIndex + 1;
    setRoundResult(null);
    setSelectedAnswer(null);
    setOpponentAnswered(false);

    if (nextIdx >= questions.length) {
      setPhase('finished');
      sseRef.current?.close();
      if (!useAiBot) {
        apiRequest<DuelRating>('/api/v1/duel/rating')
          .then(r => setRating(r))
          .catch(() => {});
      }
    } else {
      setCurrentQIndex(nextIdx);
      setPhase(useAiBot ? 'ai_playing' : 'playing');
      questionStartMs.current = Date.now();
    }
  }, [currentQIndex, questions.length, useAiBot]);

  // ------------------------------------------------------------------
  // Reset
  // ------------------------------------------------------------------
  const handleReset = useCallback(() => {
    sseRef.current?.close();
    sseRef.current = null;
    setPhase('idle');
    setSessionId(null);
    setUseAiBot(false);
    setMatchmakeError(null);
    setMyScore(0);
    setOpponentScore(0);
    setRoundHistory([]);
    setRoundResult(null);
    setSelectedAnswer(null);
    setCurrentQIndex(0);
    setQuestions([]);
  }, []);

  // ------------------------------------------------------------------
  // Derived
  // ------------------------------------------------------------------
  const currentQuestion = questions[currentQIndex] ?? null;
  const totalRounds = questions.length || AI_BOT_QUESTIONS.length;
  const roundProgress = questions.length > 0
    ? Math.round((currentQIndex / questions.length) * 100)
    : 0;

  const eloDisplay = rating
    ? Math.round(rating.elo_rating)
    : null;

  // ------------------------------------------------------------------
  // Render helpers
  // ------------------------------------------------------------------

  function renderIdle() {
    return (
      <Box sx={{ textAlign: 'center', py: 3 }}>
        <SportsEsports sx={{ fontSize: 48, color: '#6366f1', mb: 1 }} />
        <Typography variant="h6" fontWeight={800} sx={{ mb: 0.5 }}>
          1v1 Düello
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2.5 }}>
          Diğer öğrencilerle gerçek zamanlı yarış veya AI Bot ile pratik yap.
        </Typography>

        {/* ELO badge */}
        {loadingRating ? (
          <CircularProgress size={18} sx={{ mb: 2 }} />
        ) : eloDisplay !== null ? (
          <Chip
            icon={<EmojiEvents sx={{ fontSize: 16 }} />}
            label={`ELO: ${eloDisplay} · ${rating?.wins}K/${rating?.losses}M/${rating?.draws}B`}
            size="small"
            sx={{
              mb: 2.5,
              fontWeight: 700,
              fontSize: 12,
              backgroundColor: 'rgba(99,102,241,0.1)',
              color: '#6366f1',
            }}
          />
        ) : null}

        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5, maxWidth: 280, mx: 'auto' }}>
          <Button
            variant="contained"
            startIcon={<Wifi />}
            onClick={handleFindMatch}
            sx={{
              fontWeight: 700,
              borderRadius: 2,
              background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
              '&:hover': { background: 'linear-gradient(135deg, #4f46e5, #7c3aed)' },
            }}
          >
            Rakip Bul
          </Button>

          <Button
            variant="outlined"
            startIcon={<SmartToy />}
            onClick={startAiBot}
            sx={{ fontWeight: 700, borderRadius: 2, borderColor: '#94a3b8' }}
          >
            AI Bot ile Oyna
          </Button>
        </Box>

        {matchmakeError && (
          <Alert severity="error" sx={{ mt: 2, textAlign: 'left', fontSize: 12 }}>
            {matchmakeError}
          </Alert>
        )}
      </Box>
    );
  }

  function renderMatchmaking() {
    return (
      <Box sx={{ textAlign: 'center', py: 4 }}>
        <CircularProgress size={40} sx={{ mb: 2, color: '#6366f1' }} />
        <Typography variant="subtitle1" fontWeight={700}>
          Rakip Aranıyor...
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5, mb: 3 }}>
          {subject} konusunda uygun rakip bekleniyor.
        </Typography>
        <Button variant="outlined" size="small" onClick={handleReset} sx={{ borderRadius: 2 }}>
          İptal
        </Button>
      </Box>
    );
  }

  function renderWaiting() {
    return (
      <Box sx={{ textAlign: 'center', py: 4 }}>
        <CircularProgress size={40} sx={{ mb: 2, color: '#22c55e' }} />
        <Typography variant="subtitle1" fontWeight={700}>
          Kuyruğa Alındı
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5, mb: 3 }}>
          Eşleşme bulunduğunda düello başlayacak...
        </Typography>
        <Button variant="outlined" size="small" onClick={handleReset} sx={{ borderRadius: 2 }}>
          İptal
        </Button>
      </Box>
    );
  }

  function renderPlaying() {
    if (!currentQuestion) {return null;}

    const timerColor = timeLeft > 10 ? '#22c55e' : timeLeft > 5 ? '#f59e0b' : '#ef4444';

    return (
      <Box>
        {/* Top bar: scores + timer */}
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          {/* My score */}
          <Box sx={{ textAlign: 'center' }}>
            <Person sx={{ fontSize: 18, color: '#6366f1' }} />
            <Typography variant="h6" fontWeight={800} sx={{ color: '#6366f1', lineHeight: 1 }}>
              {myScore}
            </Typography>
            <Typography variant="caption" color="text.secondary">Ben</Typography>
          </Box>

          {/* Timer */}
          <Box sx={{ textAlign: 'center' }}>
            <Box
              sx={{
                width: 48,
                height: 48,
                borderRadius: '50%',
                border: `3px solid ${timerColor}`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                mx: 'auto',
              }}
            >
              <Typography variant="h6" fontWeight={900} sx={{ color: timerColor, lineHeight: 1 }}>
                {timeLeft}
              </Typography>
            </Box>
            <Typography variant="caption" color="text.secondary" sx={{ mt: 0.25, display: 'block' }}>
              {currentQIndex + 1}/{totalRounds}
            </Typography>
          </Box>

          {/* Opponent score */}
          <Box sx={{ textAlign: 'center' }}>
            {useAiBot ? (
              <SmartToy sx={{ fontSize: 18, color: '#f59e0b' }} />
            ) : (
              <Person sx={{ fontSize: 18, color: '#f59e0b' }} />
            )}
            <Typography variant="h6" fontWeight={800} sx={{ color: '#f59e0b', lineHeight: 1 }}>
              {opponentScore}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {useAiBot ? 'Bot' : 'Rakip'}
            </Typography>
          </Box>
        </Box>

        {/* Round progress */}
        <LinearProgress
          variant="determinate"
          value={roundProgress}
          sx={{
            mb: 2,
            height: 4,
            borderRadius: 2,
            bgcolor: 'rgba(0,0,0,0.06)',
            '& .MuiLinearProgress-bar': { borderRadius: 2, backgroundColor: '#6366f1' },
          }}
        />

        {/* Opponent answered indicator */}
        {opponentAnswered && (
          <Chip
            icon={<CheckCircle sx={{ fontSize: 14 }} />}
            label={useAiBot ? 'Bot cevapladı' : 'Rakip cevapladı!'}
            size="small"
            sx={{
              mb: 1.5,
              fontSize: 11,
              fontWeight: 600,
              backgroundColor: 'rgba(245,158,11,0.1)',
              color: '#f59e0b',
            }}
          />
        )}

        {/* Question */}
        <Box
          sx={{
            p: 2,
            mb: 2,
            borderRadius: 2,
            backgroundColor: 'rgba(99,102,241,0.04)',
            border: '1px solid rgba(99,102,241,0.15)',
          }}
        >
          <Chip
            label={currentQuestion.subject}
            size="small"
            sx={{ mb: 1, fontSize: 10, height: 18, fontWeight: 600 }}
          />
          <Typography variant="body2" fontWeight={600}>
            {currentQuestion.content}
          </Typography>
        </Box>

        {/* Options */}
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.75 }}>
          {currentQuestion.options.map(opt => {
            const isSelected = selectedAnswer === opt.key;
            return (
              <Box
                key={opt.key}
                component="button"
                onClick={() => {
                  if (!selectedAnswer && !answerSubmitting) {
                    handleSubmitAnswer(opt.key);
                  }
                }}
                disabled={!!selectedAnswer || answerSubmitting}
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1.5,
                  p: 1.25,
                  border: `1.5px solid ${isSelected ? '#6366f1' : 'rgba(0,0,0,0.1)'}`,
                  borderRadius: 1.5,
                  backgroundColor: isSelected ? 'rgba(99,102,241,0.08)' : 'rgba(255,255,255,0.7)',
                  cursor: selectedAnswer || answerSubmitting ? 'default' : 'pointer',
                  textAlign: 'left',
                  width: '100%',
                  transition: 'all 0.15s ease',
                  '&:hover:not(:disabled)': {
                    borderColor: '#6366f1',
                    backgroundColor: 'rgba(99,102,241,0.04)',
                  },
                  '&:disabled': { opacity: selectedAnswer ? 1 : 0.6 },
                }}
              >
                <Box
                  sx={{
                    width: 28,
                    height: 28,
                    borderRadius: '50%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontWeight: 800,
                    fontSize: 13,
                    flexShrink: 0,
                    backgroundColor: isSelected ? '#6366f1' : 'rgba(0,0,0,0.06)',
                    color: isSelected ? '#fff' : 'text.primary',
                  }}
                >
                  {opt.key}
                </Box>
                <Typography variant="body2" sx={{ flex: 1 }}>
                  {opt.text}
                </Typography>
                {answerSubmitting && isSelected && <CircularProgress size={16} />}
              </Box>
            );
          })}
        </Box>
      </Box>
    );
  }

  function renderRoundResult() {
    if (!roundResult || !currentQuestion) {return null;}

    const correct = AI_BOT_CORRECT[currentQuestion.id] ?? null;
    const isLastRound = currentQIndex >= questions.length - 1;

    return (
      <Box sx={{ textAlign: 'center' }}>
        {/* Result icon */}
        <Box sx={{ mb: 2 }}>
          {roundResult.isCorrect ? (
            <CheckCircle sx={{ fontSize: 48, color: '#22c55e' }} />
          ) : (
            <Cancel sx={{ fontSize: 48, color: '#ef4444' }} />
          )}
          <Typography variant="h6" fontWeight={800} sx={{ mt: 0.5 }}>
            {roundResult.isCorrect ? 'Doğru!' : 'Yanlış'}
          </Typography>
          {!roundResult.isCorrect && correct && (
            <Typography variant="body2" color="text.secondary">
              Doğru cevap: <strong>{correct}</strong>
            </Typography>
          )}
        </Box>

        {/* Score comparison */}
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'space-around',
            p: 2,
            borderRadius: 2,
            backgroundColor: 'rgba(0,0,0,0.03)',
            mb: 2.5,
          }}
        >
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="h5" fontWeight={900} sx={{ color: '#6366f1' }}>
              {roundResult.myScore}
            </Typography>
            <Typography variant="caption" color="text.secondary">Ben</Typography>
          </Box>
          <Divider orientation="vertical" flexItem />
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="h5" fontWeight={900} sx={{ color: '#f59e0b' }}>
              {roundResult.opponentScore}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {useAiBot ? 'Bot' : 'Rakip'}
            </Typography>
          </Box>
        </Box>

        <Button
          variant="contained"
          onClick={isLastRound ? () => setPhase('finished') : handleNextRound}
          sx={{
            fontWeight: 700,
            borderRadius: 2,
            background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
          }}
        >
          {isLastRound ? 'Sonuçları Gör' : 'Sonraki Soru'}
        </Button>
      </Box>
    );
  }

  function renderFinished() {
    const myTotal = myScore;
    const oppTotal = opponentScore;
    const won = myTotal > oppTotal;
    const draw = myTotal === oppTotal;

    return (
      <Box sx={{ textAlign: 'center', py: 2 }}>
        <Typography variant="h4" sx={{ mb: 0.5 }}>
          {won ? '🏆' : draw ? '🤝' : '😔'}
        </Typography>
        <Typography variant="h6" fontWeight={800} sx={{ mb: 0.5 }}>
          {won ? 'Kazandın!' : draw ? 'Berabere!' : 'Kaybettin'}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {myTotal} – {oppTotal} ({totalRounds} soru)
        </Typography>

        {/* Updated ELO */}
        {rating && (
          <Chip
            icon={<EmojiEvents sx={{ fontSize: 16 }} />}
            label={`ELO: ${Math.round(rating.elo_rating)}`}
            size="small"
            sx={{
              mb: 2.5,
              fontWeight: 700,
              backgroundColor: 'rgba(99,102,241,0.1)',
              color: '#6366f1',
            }}
          />
        )}

        {/* Round summary */}
        <Box sx={{ mb: 2.5, textAlign: 'left' }}>
          <Typography variant="caption" fontWeight={700} color="text.secondary" sx={{ display: 'block', mb: 0.75 }}>
            Tur Özeti
          </Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
            {roundHistory.map((r, i) => (
              <Box
                key={i}
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1,
                  p: 0.75,
                  borderRadius: 1,
                  backgroundColor: r.isCorrect ? 'rgba(34,197,94,0.06)' : 'rgba(239,68,68,0.06)',
                }}
              >
                {r.isCorrect
                  ? <CheckCircle sx={{ fontSize: 14, color: '#22c55e' }} />
                  : <Cancel sx={{ fontSize: 14, color: '#ef4444' }} />}
                <Typography variant="caption" sx={{ flex: 1 }}>
                  Soru {r.questionOrder + 1}
                </Typography>
                <Typography variant="caption" fontWeight={700}>
                  {r.myAnswer || '—'}
                </Typography>
              </Box>
            ))}
          </Box>
        </Box>

        <Box sx={{ display: 'flex', gap: 1.5, justifyContent: 'center' }}>
          <Button
            variant="contained"
            onClick={handleReset}
            sx={{
              fontWeight: 700,
              borderRadius: 2,
              background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
            }}
          >
            Yeni Düello
          </Button>
        </Box>
      </Box>
    );
  }

  // ------------------------------------------------------------------
  // Main render
  // ------------------------------------------------------------------
  return (
    <GlassCard glassIntensity="light">
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <SportsEsports sx={{ fontSize: 20, color: '#6366f1' }} />
          <Typography variant="subtitle1" fontWeight={700}>
            Düello
          </Typography>
          {useAiBot && (
            <Chip
              icon={<SmartToy sx={{ fontSize: 13 }} />}
              label="AI Bot"
              size="small"
              sx={{ fontSize: 10, height: 20, fontWeight: 600, backgroundColor: 'rgba(245,158,11,0.1)', color: '#f59e0b' }}
            />
          )}
          {!useAiBot && sessionId && (
            <Chip
              icon={<Wifi sx={{ fontSize: 13 }} />}
              label="Gerçek Rakip"
              size="small"
              sx={{ fontSize: 10, height: 20, fontWeight: 600, backgroundColor: 'rgba(34,197,94,0.1)', color: '#22c55e' }}
            />
          )}
        </Box>

        {phase !== 'idle' && phase !== 'matchmaking' && phase !== 'waiting' && (
          <Box
            component="button"
            onClick={handleReset}
            sx={{
              border: 'none',
              background: 'transparent',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              color: 'text.secondary',
              p: 0.5,
              borderRadius: 1,
              fontSize: 12,
              fontWeight: 600,
              '&:hover': { backgroundColor: 'rgba(0,0,0,0.04)' },
            }}
          >
            <WifiOff sx={{ fontSize: 16, mr: 0.5 }} />
            Çık
          </Box>
        )}
      </Box>

      {/* Phase content */}
      {phase === 'idle' && renderIdle()}
      {phase === 'matchmaking' && renderMatchmaking()}
      {phase === 'waiting' && renderWaiting()}
      {(phase === 'playing' || phase === 'ai_playing') && renderPlaying()}
      {phase === 'round_result' && renderRoundResult()}
      {phase === 'finished' && renderFinished()}
    </GlassCard>
  );
}

export default DuelMode;
