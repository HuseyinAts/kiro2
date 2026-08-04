import os

content = """/**
 * DuelMode — F1 1v1 Düello
 *
 * Refactored to AUGUST 2026 ULTRA standards.
 * Tech debt cleared by utilizing duelReducer.
 */

import { useEffect, useRef, useCallback, useReducer } from 'react';
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

import { 
  duelReducer, 
  initialDuelState,
  DuelRating,
  DuelQuestion,
  RoundResult
} from './duelReducer';

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
    content: 'Türkiye\\'nin en uzun nehri hangisidir?',
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
  const correct = AI_BOT_CORRECT[questionId] ?? 'A';
  const roll = Math.random();
  if (roll < 0.70) return correct;
  const options = ['A', 'B', 'C', 'D', 'E'].filter(o => o !== correct);
  return options[Math.floor(Math.random() * options.length)];
}

// ---------------------------------------------------------------------------
// Timer hook
// ---------------------------------------------------------------------------
import { useState } from 'react';
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

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

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
  }, [state, dispatch]);

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
  }, [state, dispatch]);

  const handleReset = useCallback(() => {
    sseRef.current?.close();
    sseRef.current = null;
    dispatch({ type: 'RESET_GAME' });
  }, []);

  const currentQuestion = state.questions[state.currentQIndex] ?? null;
  const totalRounds = state.questions.length || AI_BOT_QUESTIONS.length;
  const roundProgress = state.questions.length > 0 ? Math.round((state.currentQIndex / state.questions.length) * 100) : 0;
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

  function renderPlaying() {
    if (!currentQuestion) return null;
    const timerColor = timeLeft > 10 ? '#22c55e' : timeLeft > 5 ? '#f59e0b' : '#ef4444';

    return (
      <Box>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Box sx={{ textAlign: 'center' }}>
            <Person sx={{ fontSize: 18, color: '#6366f1' }} />
            <Typography variant="h6" fontWeight={800} sx={{ color: '#6366f1', lineHeight: 1 }}>{state.myScore}</Typography>
            <Typography variant="caption" color="text.secondary">Ben</Typography>
          </Box>
          <Box sx={{ textAlign: 'center' }}>
            <Box sx={{ width: 48, height: 48, borderRadius: '50%', border: `3px solid ${timerColor}`, display: 'flex', alignItems: 'center', justifyContent: 'center', mx: 'auto' }}>
              <Typography variant="h6" fontWeight={900} sx={{ color: timerColor, lineHeight: 1 }}>{timeLeft}</Typography>
            </Box>
            <Typography variant="caption" color="text.secondary" sx={{ mt: 0.25, display: 'block' }}>{state.currentQIndex + 1}/{totalRounds}</Typography>
          </Box>
          <Box sx={{ textAlign: 'center' }}>
            {state.useAiBot ? <SmartToy sx={{ fontSize: 18, color: '#f59e0b' }} /> : <Person sx={{ fontSize: 18, color: '#f59e0b' }} />}
            <Typography variant="h6" fontWeight={800} sx={{ color: '#f59e0b', lineHeight: 1 }}>{state.opponentScore}</Typography>
            <Typography variant="caption" color="text.secondary">{state.useAiBot ? 'Bot' : 'Rakip'}</Typography>
          </Box>
        </Box>

        <LinearProgress variant="determinate" value={roundProgress} sx={{ mb: 2, height: 4, borderRadius: 2, bgcolor: 'rgba(0,0,0,0.06)', '& .MuiLinearProgress-bar': { borderRadius: 2, backgroundColor: '#6366f1' } }} />

        {state.opponentAnswered && (
          <Chip icon={<CheckCircle sx={{ fontSize: 14 }} />} label={state.useAiBot ? 'Bot cevapladı' : 'Rakip cevapladı!'} size="small" sx={{ mb: 1.5, fontSize: 11, fontWeight: 600, backgroundColor: 'rgba(245,158,11,0.1)', color: '#f59e0b' }} />
        )}

        <Box sx={{ p: 2, mb: 2, borderRadius: 2, backgroundColor: 'rgba(99,102,241,0.04)', border: '1px solid rgba(99,102,241,0.15)' }}>
          <Chip label={currentQuestion.subject} size="small" sx={{ mb: 1, fontSize: 10, height: 18, fontWeight: 600 }} />
          <Typography variant="body2" fontWeight={600}>{currentQuestion.content}</Typography>
        </Box>

        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.75 }}>
          {currentQuestion.options.map(opt => {
            const isSelected = state.selectedAnswer === opt.key;
            return (
              <Box key={opt.key} component="button" onClick={() => { if (!state.selectedAnswer && !state.answerSubmitting) handleSubmitAnswer(opt.key); }} disabled={!!state.selectedAnswer || state.answerSubmitting} sx={{ display: 'flex', alignItems: 'center', gap: 1.5, p: 1.25, border: `1.5px solid ${isSelected ? '#6366f1' : 'rgba(0,0,0,0.1)'}`, borderRadius: 1.5, backgroundColor: isSelected ? 'rgba(99,102,241,0.08)' : 'rgba(255,255,255,0.7)', cursor: state.selectedAnswer || state.answerSubmitting ? 'default' : 'pointer', textAlign: 'left', width: '100%', transition: 'all 0.15s ease', '&:hover:not(:disabled)': { borderColor: '#6366f1', backgroundColor: 'rgba(99,102,241,0.04)' }, '&:disabled': { opacity: state.selectedAnswer ? 1 : 0.6 } }}>
                <Box sx={{ width: 28, height: 28, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, fontSize: 13, flexShrink: 0, backgroundColor: isSelected ? '#6366f1' : 'rgba(0,0,0,0.06)', color: isSelected ? '#fff' : 'text.primary' }}>{opt.key}</Box>
                <Typography variant="body2" sx={{ flex: 1 }}>{opt.text}</Typography>
                {state.answerSubmitting && isSelected && <CircularProgress size={16} />}
              </Box>
            );
          })}
        </Box>
      </Box>
    );
  }

  function renderRoundResult() {
    if (!state.roundResult || !currentQuestion) return null;
    const correct = AI_BOT_CORRECT[currentQuestion.id] ?? null;
    const isLastRound = state.currentQIndex >= state.questions.length - 1;

    return (
      <Box sx={{ textAlign: 'center' }}>
        <Box sx={{ mb: 2 }}>
          {state.roundResult.isCorrect ? <CheckCircle sx={{ fontSize: 48, color: '#22c55e' }} /> : <Cancel sx={{ fontSize: 48, color: '#ef4444' }} />}
          <Typography variant="h6" fontWeight={800} sx={{ mt: 0.5 }}>{state.roundResult.isCorrect ? 'Doğru!' : 'Yanlış'}</Typography>
          {!state.roundResult.isCorrect && correct && <Typography variant="body2" color="text.secondary">Doğru cevap: <strong>{correct}</strong></Typography>}
        </Box>
        <Box sx={{ display: 'flex', justifyContent: 'space-around', p: 2, borderRadius: 2, backgroundColor: 'rgba(0,0,0,0.03)', mb: 2.5 }}>
          <Box sx={{ textAlign: 'center' }}><Typography variant="h5" fontWeight={900} sx={{ color: '#6366f1' }}>{state.roundResult.myScore}</Typography><Typography variant="caption" color="text.secondary">Ben</Typography></Box>
          <Divider orientation="vertical" flexItem />
          <Box sx={{ textAlign: 'center' }}><Typography variant="h5" fontWeight={900} sx={{ color: '#f59e0b' }}>{state.roundResult.opponentScore}</Typography><Typography variant="caption" color="text.secondary">{state.useAiBot ? 'Bot' : 'Rakip'}</Typography></Box>
        </Box>
        <Button variant="contained" onClick={isLastRound ? () => dispatch({ type: 'FINISH_DUEL', payload: { myScore: state.myScore, opponentScore: state.opponentScore } }) : handleNextRound} sx={{ fontWeight: 700, borderRadius: 2, background: 'linear-gradient(135deg, #6366f1, #8b5cf6)' }}>{isLastRound ? 'Sonuçları Gör' : 'Sonraki Soru'}</Button>
      </Box>
    );
  }

  function renderFinished() {
    const won = state.myScore > state.opponentScore;
    const draw = state.myScore === state.opponentScore;
    return (
      <Box sx={{ textAlign: 'center', py: 2 }}>
        <Typography variant="h4" sx={{ mb: 0.5 }}>{won ? '🏆' : draw ? '🤝' : '😔'}</Typography>
        <Typography variant="h6" fontWeight={800} sx={{ mb: 0.5 }}>{won ? 'Kazandın!' : draw ? 'Berabere!' : 'Kaybettin'}</Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>{state.myScore} – {state.opponentScore} ({totalRounds} soru)</Typography>
        {state.rating && <Chip icon={<EmojiEvents sx={{ fontSize: 16 }} />} label={`ELO: ${Math.round(state.rating.elo_rating)}`} size="small" sx={{ mb: 2.5, fontWeight: 700, backgroundColor: 'rgba(99,102,241,0.1)', color: '#6366f1' }} />}
        <Box sx={{ mb: 2.5, textAlign: 'left' }}>
          <Typography variant="caption" fontWeight={700} color="text.secondary" sx={{ display: 'block', mb: 0.75 }}>Tur Özeti</Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
            {state.roundHistory.map((r, i) => (
              <Box key={i} sx={{ display: 'flex', alignItems: 'center', gap: 1, p: 0.75, borderRadius: 1, backgroundColor: r.isCorrect ? 'rgba(34,197,94,0.06)' : 'rgba(239,68,68,0.06)' }}>
                {r.isCorrect ? <CheckCircle sx={{ fontSize: 14, color: '#22c55e' }} /> : <Cancel sx={{ fontSize: 14, color: '#ef4444' }} />}
                <Typography variant="caption" sx={{ flex: 1 }}>Soru {r.questionOrder + 1}</Typography>
                <Typography variant="caption" fontWeight={700}>{r.myAnswer || '—'}</Typography>
              </Box>
            ))}
          </Box>
        </Box>
        <Box sx={{ display: 'flex', gap: 1.5, justifyContent: 'center' }}>
          <Button variant="contained" onClick={handleReset} sx={{ fontWeight: 700, borderRadius: 2, background: 'linear-gradient(135deg, #6366f1, #8b5cf6)' }}>Yeni Düello</Button>
        </Box>
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
      {(state.phase === 'playing' || state.phase === 'ai_playing') && renderPlaying()}
      {state.phase === 'round_result' && renderRoundResult()}
      {state.phase === 'finished' && renderFinished()}
    </GlassCard>
  );
}

export default DuelMode;
"""
with open('frontend/src/components/LearningPath/DuelMode.tsx', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated DuelMode.tsx")
