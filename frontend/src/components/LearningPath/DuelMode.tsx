/**
 * DuelMode — F1 1v1 Düello
 *
 * Refactored to AUGUST 2026 ULTRA standards.
 * Uses duelReducer and child components with Framer Motion.
 */

import { useEffect, useRef, useCallback, useReducer, useState } from 'react';
import {
  Box,
  Typography,
  Button,
  Chip,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  SportsEsports,
  SmartToy,
  EmojiEvents,
  Wifi,
  WifiOff,
} from '@mui/icons-material';
import { GlassCard } from '../ui/GlassCard';
import { apiRequest } from '../../utils/apiHelpers';

import { 
  duelReducer, 
  initialDuelState,
  DuelRating,
  DuelQuestion,
  RoundResult
} from './duelReducer';

import DuelArena from './DuelArena';
import DuelHud from './DuelHud';
import DuelResults from './DuelResults';

// --- AI Bot Mock Data ---
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
];

const AI_BOT_CORRECT: Record<string, string> = {
  'ai-q1': 'C',
  'ai-q2': 'B',
  'ai-q3': 'C',
};

function aiBotAnswer(questionId: string): string {
  const correct = AI_BOT_CORRECT[questionId] ?? 'A';
  const roll = Math.random();
  if (roll < 0.70) return correct;
  const options = ['A', 'B', 'C', 'D', 'E'].filter(o => o !== correct);
  return options[Math.floor(Math.random() * options.length)];
}

// --- Timer Hook ---
function useCountdown(initialSeconds: number, active: boolean, onExpire: () => void) {
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

interface DuelModeProps {
  subject?: string;
}

const QUESTION_TIME_SEC = 30;

export function DuelMode({ subject = 'MATEMATIK' }: DuelModeProps) {
  const [state, dispatch] = useReducer(duelReducer, initialDuelState);
  const questionStartMs = useRef<number>(Date.now());
  const sseRef = useRef<EventSource | null>(null);

  // Timer
  const timerActive = state.phase === 'playing' || state.phase === 'ai_playing';
  const timeLeft = useCountdown(QUESTION_TIME_SEC, timerActive, () => {
    if (timerActive && !state.selectedAnswer) {
      handleSubmitAnswer(null);
    }
  });

  useEffect(() => {
    let cancelled = false;
    async function fetchRating() {
      dispatch({ type: 'SET_LOADING_RATING', payload: true });
      try {
        const data = await apiRequest<DuelRating>('/api/v1/duel/rating');
        if (!cancelled) dispatch({ type: 'SET_RATING', payload: data });
      } catch {
        // Fallback or ignore
      } finally {
        if (!cancelled) dispatch({ type: 'SET_LOADING_RATING', payload: false });
      }
    }
    fetchRating();
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    return () => sseRef.current?.close();
  }, []);

  const subscribeSSE = useCallback((sid: string) => {
    sseRef.current?.close();
    const es = new EventSource(`/api/v1/duel/stream/${sid}`);
    sseRef.current = es;

    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleSseEvent(data);
      } catch {
        // Ignore
      }
    };
    es.onerror = () => es.close();
  }, []);

  function handleSseEvent(data: Record<string, unknown>) {
    const type = data.type as string;
    switch (type) {
      case 'match_found': {
        const qList = (data.questions as DuelQuestion[] | undefined) ?? [];
        dispatch({
          type: 'MATCH_FOUND',
          payload: { sessionId: data.session_id as string, questions: qList.length > 0 ? qList : AI_BOT_QUESTIONS }
        });
        questionStartMs.current = Date.now();
        break;
      }
      case 'question': {
        const q = data.question as DuelQuestion | undefined;
        const idx = data.index as number ?? state.currentQIndex + 1;
        if (q) {
          dispatch({ type: 'UPDATE_QUESTION', payload: { index: idx, question: q } });
        }
        dispatch({ type: 'NEXT_QUESTION', payload: idx });
        questionStartMs.current = Date.now();
        break;
      }
      case 'answer': {
        const isSelf = data.is_self as boolean | undefined;
        if (!isSelf && data.player_id) {
          dispatch({ type: 'OPPONENT_ANSWERED', payload: { score: data.player2_score as number } });
        }
        break;
      }
      case 'opponent_answered':
        dispatch({ type: 'OPPONENT_ANSWERED', payload: {} });
        break;
      case 'round_complete':
        dispatch({ type: 'ROUND_COMPLETE', payload: { myScore: data.player1_score as number ?? state.myScore, opponentScore: data.player2_score as number ?? state.opponentScore } });
        break;
      case 'finished':
      case 'duel_complete':
        dispatch({ type: 'FINISH_DUEL', payload: { myScore: data.player1_score as number ?? state.myScore, opponentScore: data.player2_score as number ?? state.opponentScore } });
        sseRef.current?.close();
        apiRequest<DuelRating>('/api/v1/duel/rating')
          .then(r => dispatch({ type: 'SET_RATING', payload: r }))
          .catch(() => {});
        break;
    }
  }

  const handleFindMatch = useCallback(async () => {
    dispatch({ type: 'START_MATCHMAKING' });
    try {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const result = await apiRequest<any>('/api/v1/duel/matchmake', {
        method: 'POST',
        body: JSON.stringify({ subject }),
      });
      if (result.status === 'matched' && result.session_id) {
        dispatch({ type: 'MATCH_FOUND', payload: { sessionId: result.session_id } });
        subscribeSSE(result.session_id);
      } else {
        dispatch({ type: 'MATCH_FOUND', payload: { sessionId: 'waiting_session' } });
      }
    } catch {
      startAiBot();
    }
  }, [subject, subscribeSSE]);

  const startAiBot = useCallback(() => {
    dispatch({ type: 'START_AI_BOT', payload: { questions: AI_BOT_QUESTIONS } });
    questionStartMs.current = Date.now();
  }, []);

  const handleSubmitAnswer = useCallback(async (answer: string | null) => {
    if (state.answerSubmitting) return;
    const currentQ = state.questions[state.currentQIndex];
    if (!currentQ) return;

    dispatch({ type: 'SUBMIT_ANSWER', payload: answer ?? '' });
    const elapsed = Date.now() - questionStartMs.current;

    if (state.useAiBot || !state.sessionId) {
      const correct = AI_BOT_CORRECT[currentQ.id] ?? 'A';
      const isCorrect = answer !== null && answer === correct;
      const botAnswer = aiBotAnswer(currentQ.id);
      const botCorrect = botAnswer === correct;
      
      const newMyScore = state.myScore + (isCorrect ? 1 : 0);
      const newOppScore = state.opponentScore + (botCorrect ? 1 : 0);
      
      const result: RoundResult = {
        questionOrder: state.currentQIndex,
        myAnswer: answer ?? '',
        isCorrect,
        myScore: newMyScore,
        opponentScore: newOppScore,
        opponentAnswered: true,
      };
      dispatch({ type: 'ANSWER_RESULT', payload: result });
      return;
    }

    try {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const res = await apiRequest<any>(
        `/api/v1/duel/${state.sessionId}/answer`,
        {
          method: 'POST',
          body: JSON.stringify({ question_order: state.currentQIndex, answer: answer ?? 'A', time_ms: elapsed }),
        },
      );
      
      const result: RoundResult = {
        questionOrder: state.currentQIndex,
        myAnswer: answer ?? '',
        isCorrect: res.is_correct,
        myScore: res.player1_score,
        opponentScore: res.player2_score,
        opponentAnswered: res.round_complete,
      };
      dispatch({ type: 'ANSWER_RESULT', payload: result });
    } catch {
      const result: RoundResult = {
        questionOrder: state.currentQIndex,
        myAnswer: answer ?? '',
        isCorrect: false,
        myScore: state.myScore,
        opponentScore: state.opponentScore,
        opponentAnswered: false,
      };
      dispatch({ type: 'ANSWER_RESULT', payload: result });
    }
  }, [state]);

  const handleNextRound = useCallback(() => {
    const nextIdx = state.currentQIndex + 1;
    if (nextIdx >= state.questions.length) {
      dispatch({ type: 'FINISH_DUEL', payload: { myScore: state.myScore, opponentScore: state.opponentScore } });
      sseRef.current?.close();
      if (!state.useAiBot) {
        apiRequest<DuelRating>('/api/v1/duel/rating').then(r => dispatch({ type: 'SET_RATING', payload: r })).catch(() => {});
      }
    } else {
      dispatch({ type: 'NEXT_QUESTION', payload: nextIdx });
      questionStartMs.current = Date.now();
    }
  }, [state]);

  const handleReset = useCallback(() => {
    sseRef.current?.close();
    sseRef.current = null;
    dispatch({ type: 'RESET_GAME' });
  }, []);

  const currentQuestion = state.questions[state.currentQIndex] ?? null;
  const totalRounds = state.questions.length || AI_BOT_QUESTIONS.length;
  const eloDisplay = state.rating ? Math.round(state.rating.elo_rating) : null;

  function renderIdle() {
    return (
      <Box sx={{ textAlign: 'center', py: 3 }}>
        <SportsEsports sx={{ fontSize: 48, color: '#6366f1', mb: 1 }} />
        <Typography variant="h6" fontWeight={800} sx={{ mb: 0.5 }}>1v1 Düello</Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2.5 }}>
          Diğer öğrencilerle gerçek zamanlı yarış veya AI Bot ile pratik yap.
        </Typography>

        {state.loadingRating ? (
          <CircularProgress size={18} sx={{ mb: 2 }} />
        ) : eloDisplay !== null ? (
          <Chip
            icon={<EmojiEvents sx={{ fontSize: 16 }} />}
            label={`ELO: ${eloDisplay} · ${state.rating?.wins}K/${state.rating?.losses}M/${state.rating?.draws}B`}
            size="small"
            sx={{ mb: 2.5, fontWeight: 700, fontSize: 12, backgroundColor: 'rgba(99,102,241,0.1)', color: '#6366f1' }}
          />
        ) : null}

        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5, maxWidth: 280, mx: 'auto' }}>
          <Button variant="contained" startIcon={<Wifi />} onClick={handleFindMatch} sx={{ fontWeight: 700, borderRadius: 2, background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', '&:hover': { background: 'linear-gradient(135deg, #4f46e5, #7c3aed)' } }}>Rakip Bul</Button>
          <Button variant="outlined" startIcon={<SmartToy />} onClick={startAiBot} sx={{ fontWeight: 700, borderRadius: 2, borderColor: '#94a3b8' }}>AI Bot ile Oyna</Button>
        </Box>
        {state.matchmakeError && <Alert severity="error" sx={{ mt: 2, textAlign: 'left', fontSize: 12 }}>{state.matchmakeError}</Alert>}
      </Box>
    );
  }

  function renderMatchmaking() {
    return (
      <Box sx={{ textAlign: 'center', py: 4 }}>
        <CircularProgress size={40} sx={{ mb: 2, color: '#6366f1' }} />
        <Typography variant="subtitle1" fontWeight={700}>Rakip Aranıyor...</Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5, mb: 3 }}>{subject} konusunda uygun rakip bekleniyor.</Typography>
        <Button variant="outlined" size="small" onClick={handleReset} sx={{ borderRadius: 2 }}>İptal</Button>
      </Box>
    );
  }

  function renderWaiting() {
    return (
      <Box sx={{ textAlign: 'center', py: 4 }}>
        <CircularProgress size={40} sx={{ mb: 2, color: '#22c55e' }} />
        <Typography variant="subtitle1" fontWeight={700}>Kuyruğa Alındı</Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5, mb: 3 }}>Eşleşme bulunduğunda düello başlayacak...</Typography>
        <Button variant="outlined" size="small" onClick={handleReset} sx={{ borderRadius: 2 }}>İptal</Button>
      </Box>
    );
  }

  return (
    <GlassCard glassIntensity="light">
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <SportsEsports sx={{ fontSize: 20, color: '#6366f1' }} />
          <Typography variant="subtitle1" fontWeight={700}>Düello</Typography>
          {state.useAiBot && <Chip icon={<SmartToy sx={{ fontSize: 13 }} />} label="AI Bot" size="small" sx={{ fontSize: 10, height: 20, fontWeight: 600, backgroundColor: 'rgba(245,158,11,0.1)', color: '#f59e0b' }} />}
          {!state.useAiBot && state.sessionId && <Chip icon={<Wifi sx={{ fontSize: 13 }} />} label="Gerçek Rakip" size="small" sx={{ fontSize: 10, height: 20, fontWeight: 600, backgroundColor: 'rgba(34,197,94,0.1)', color: '#22c55e' }} />}
        </Box>
        {state.phase !== 'idle' && state.phase !== 'matchmaking' && state.phase !== 'waiting' && (
          <Box component="button" onClick={handleReset} sx={{ border: 'none', background: 'transparent', cursor: 'pointer', display: 'flex', alignItems: 'center', color: 'text.secondary', p: 0.5, borderRadius: 1, fontSize: 12, fontWeight: 600, '&:hover': { backgroundColor: 'rgba(0,0,0,0.04)' } }}>
            <WifiOff sx={{ fontSize: 16, mr: 0.5 }} /> Çık
          </Box>
        )}
      </Box>
      {state.phase === 'idle' && renderIdle()}
      {state.phase === 'matchmaking' && renderMatchmaking()}
      {state.phase === 'waiting' && renderWaiting()}
      
      {(state.phase === 'playing' || state.phase === 'ai_playing') && currentQuestion && (
        <Box>
          <DuelHud myScore={state.myScore} opponentScore={state.opponentScore} isBot={state.useAiBot} timeLeft={timeLeft} currentRound={state.currentQIndex + 1} totalRounds={totalRounds} />
          <DuelArena question={currentQuestion} selectedAnswer={state.selectedAnswer} isSubmitting={state.answerSubmitting} onAnswer={handleSubmitAnswer} opponentAnswered={state.opponentAnswered} isBot={state.useAiBot} />
        </Box>
      )}
      
      {state.phase === 'round_result' && state.roundResult && currentQuestion && (
        <DuelResults 
          type="round"
          roundResult={state.roundResult} 
          correctAnswer={AI_BOT_CORRECT[currentQuestion.id]} 
          myScore={state.myScore}
          opponentScore={state.opponentScore}
          isBot={state.useAiBot}
          totalRounds={totalRounds}
          onNextRound={handleNextRound} 
          onFinish={() => dispatch({ type: 'FINISH_DUEL', payload: { myScore: state.myScore, opponentScore: state.opponentScore } })} 
        />
      )}
      
      {state.phase === 'finished' && (
        <DuelResults
          type="final"
          myScore={state.myScore}
          opponentScore={state.opponentScore}
          isBot={state.useAiBot}
          totalRounds={totalRounds}
          rating={state.rating}
          roundHistory={state.roundHistory}
          onReset={handleReset}
        />
      )}
    </GlassCard>
  );
}

export default DuelMode;
