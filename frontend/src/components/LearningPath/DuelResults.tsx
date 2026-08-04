import { Box, Typography, Button, Divider, Chip } from '@mui/material';
import { CheckCircle, Cancel, EmojiEvents } from '@mui/icons-material';
import { motion } from 'framer-motion';
import { RoundResult, DuelRating } from './duelReducer';

interface DuelResultsProps {
  type: 'round' | 'final';
  roundResult?: RoundResult;
  correctAnswer?: string;
  myScore: number;
  opponentScore: number;
  isBot: boolean;
  totalRounds: number;
  rating?: DuelRating | null;
  roundHistory?: RoundResult[];
  onNextRound?: () => void;
  onFinish?: () => void;
  onReset?: () => void;
}

export default function DuelResults({
  type,
  roundResult,
  correctAnswer,
  myScore,
  opponentScore,
  isBot,
  totalRounds,
  rating,
  roundHistory,
  onNextRound,
  onFinish,
  onReset,
}: DuelResultsProps) {
  if (type === 'round' && roundResult) {
    const isLastRound = roundResult.questionOrder >= totalRounds - 1;
    return (
      <Box sx={{ textAlign: 'center', py: 2 }} component={motion.div} initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }}>
        <motion.div
          initial={{ scale: 0, rotate: -180 }}
          animate={{ scale: 1, rotate: 0 }}
          transition={{ type: 'spring', damping: 15 }}
          style={{ marginBottom: '16px' }}
        >
          {roundResult.isCorrect ? (
            <CheckCircle sx={{ fontSize: 72, color: '#22c55e', filter: 'drop-shadow(0 0 12px rgba(34,197,94,0.4))' }} />
          ) : (
            <Cancel sx={{ fontSize: 72, color: '#ef4444', filter: 'drop-shadow(0 0 12px rgba(239,68,68,0.4))' }} />
          )}
        </motion.div>
        
        <Typography variant="h4" fontWeight={900} sx={{ mt: 0.5, mb: 1, color: roundResult.isCorrect ? '#16a34a' : '#dc2626' }}>
          {roundResult.isCorrect ? 'Mükemmel!' : 'Yanlış Cevap'}
        </Typography>
        
        {!roundResult.isCorrect && correctAnswer && (
          <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
            Doğru cevap: <strong style={{ color: '#1e293b' }}>{correctAnswer}</strong>
          </Typography>
        )}

        <Box sx={{ display: 'flex', justifyContent: 'space-around', alignItems: 'center', p: 3, borderRadius: 4, backgroundColor: 'rgba(255,255,255,0.6)', backdropFilter: 'blur(12px)', mb: 4, border: '1px solid rgba(255,255,255,0.8)', boxShadow: '0 8px 32px rgba(0,0,0,0.06)' }}>
          <Box sx={{ textAlign: 'center', flex: 1 }}>
            <Typography variant="h3" fontWeight={900} sx={{ color: '#6366f1' }}>{roundResult.myScore}</Typography>
            <Typography variant="subtitle2" color="text.secondary" fontWeight={700} textTransform="uppercase" letterSpacing={1}>Ben</Typography>
          </Box>
          <Divider orientation="vertical" flexItem sx={{ opacity: 0.6, mx: 2 }} />
          <Box sx={{ textAlign: 'center', flex: 1 }}>
            <Typography variant="h3" fontWeight={900} sx={{ color: '#f59e0b' }}>{roundResult.opponentScore}</Typography>
            <Typography variant="subtitle2" color="text.secondary" fontWeight={700} textTransform="uppercase" letterSpacing={1}>{isBot ? 'Bot' : 'Rakip'}</Typography>
          </Box>
        </Box>

        <Button
          variant="contained"
          onClick={isLastRound ? onFinish : onNextRound}
          sx={{
            fontWeight: 800,
            fontSize: '16px',
            borderRadius: 3,
            px: 6,
            py: 1.5,
            background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
            boxShadow: '0 8px 20px rgba(99,102,241,0.4)',
            transition: 'all 0.2s',
            '&:hover': {
              background: 'linear-gradient(135deg, #4f46e5, #7c3aed)',
              transform: 'translateY(-2px)',
              boxShadow: '0 12px 25px rgba(99,102,241,0.5)',
            }
          }}
        >
          {isLastRound ? 'Sonuçları Gör' : 'Sonraki Soru'}
        </Button>
      </Box>
    );
  }

  if (type === 'final') {
    const won = myScore > opponentScore;
    const draw = myScore === opponentScore;

    return (
      <Box sx={{ textAlign: 'center', py: 3 }} component={motion.div} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: 'spring', bounce: 0.5, delay: 0.2 }}
        >
          <Typography variant="h1" sx={{ mb: 2, filter: 'drop-shadow(0 10px 15px rgba(0,0,0,0.1))', fontSize: '5rem' }}>
            {won ? '🏆' : draw ? '🤝' : '😔'}
          </Typography>
        </motion.div>

        <Typography variant="h3" fontWeight={900} sx={{ mb: 1, background: won ? 'linear-gradient(135deg, #22c55e, #10b981)' : draw ? 'linear-gradient(135deg, #f59e0b, #fbbf24)' : 'linear-gradient(135deg, #ef4444, #f43f5e)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
          {won ? 'Zafer Senin!' : draw ? 'Kıyasıya Beraberlik!' : 'Kaybettin'}
        </Typography>

        <Typography variant="h6" color="text.secondary" fontWeight={700} sx={{ mb: 4 }}>
          Skor: {myScore} – {opponentScore} <span style={{ opacity: 0.6, fontSize: '0.9em' }}>({totalRounds} Soru)</span>
        </Typography>

        {rating && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.5 }}>
            <Chip
              icon={<EmojiEvents sx={{ fontSize: 20 }} />}
              label={`Yeni ELO: ${Math.round(rating.elo_rating)}`}
              sx={{
                mb: 5,
                px: 2,
                py: 3,
                fontSize: 16,
                fontWeight: 900,
                backgroundColor: 'rgba(99,102,241,0.1)',
                color: '#6366f1',
                border: '1px solid rgba(99,102,241,0.2)',
                boxShadow: '0 4px 15px rgba(99,102,241,0.15)'
              }}
            />
          </motion.div>
        )}

        {roundHistory && roundHistory.length > 0 && (
          <Box sx={{ mb: 5, textAlign: 'left', backgroundColor: 'rgba(255,255,255,0.6)', backdropFilter: 'blur(12px)', borderRadius: 4, p: 3, border: '1px solid rgba(255,255,255,0.8)', boxShadow: '0 8px 32px rgba(0,0,0,0.04)' }}>
            <Typography variant="overline" fontWeight={900} color="text.secondary" sx={{ display: 'block', mb: 2, letterSpacing: 1.5, fontSize: '0.85rem' }}>
              Maç Özeti
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
              {roundHistory.map((r, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -15 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.6 + i * 0.1 }}
                >
                  <Box
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 2,
                      p: 2,
                      borderRadius: 3,
                      backgroundColor: r.isCorrect ? 'rgba(34,197,94,0.1)' : 'rgba(239,68,68,0.1)',
                      border: `1px solid ${r.isCorrect ? 'rgba(34,197,94,0.25)' : 'rgba(239,68,68,0.25)'}`,
                    }}
                  >
                    {r.isCorrect ? <CheckCircle sx={{ fontSize: 20, color: '#22c55e' }} /> : <Cancel sx={{ fontSize: 20, color: '#ef4444' }} />}
                    <Typography variant="body1" fontWeight={700} sx={{ flex: 1, color: '#1e293b' }}>
                      Soru {r.questionOrder + 1}
                    </Typography>
                    <Typography variant="body1" fontWeight={800} sx={{ color: r.isCorrect ? '#16a34a' : '#dc2626' }}>
                      {r.myAnswer || 'Cevapsız'}
                    </Typography>
                  </Box>
                </motion.div>
              ))}
            </Box>
          </Box>
        )}

        <Button
          variant="contained"
          onClick={onReset}
          sx={{
            fontWeight: 800,
            fontSize: '16px',
            borderRadius: 3,
            px: 6,
            py: 2,
            background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
            boxShadow: '0 8px 24px rgba(99,102,241,0.4)',
            transition: 'all 0.2s',
            '&:hover': {
              background: 'linear-gradient(135deg, #4f46e5, #7c3aed)',
              transform: 'translateY(-2px)',
              boxShadow: '0 12px 30px rgba(99,102,241,0.5)',
            }
          }}
        >
          Yeni Düello Başlat
        </Button>
      </Box>
    );
  }

  return null;
}
