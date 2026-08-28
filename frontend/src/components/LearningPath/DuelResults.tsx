import { Box, Typography, Button, Divider, Chip } from '@mui/material';
import { CheckCircle, Cancel, EmojiEvents } from '@mui/icons-material';
import { motion } from 'framer-motion';
import { RoundResult, DuelRating } from './duelReducer';
import modernColors from '../../theme/modern-colors';

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
            <CheckCircle sx={{ fontSize: 80, color: modernColors.success[500], filter: 'drop-shadow(0 0 16px rgba(34,197,94,0.5))' }} />
          ) : (
            <Cancel sx={{ fontSize: 80, color: modernColors.error[500], filter: 'drop-shadow(0 0 16px rgba(239,68,68,0.5))' }} />
          )}
        </motion.div>

        <Typography variant="h4" fontWeight={900} sx={{ mt: 0.5, mb: 1, color: roundResult.isCorrect ? modernColors.success[500] : modernColors.error[500], textShadow: '0 2px 10px rgba(0,0,0,0.05)' }}>
          {roundResult.isCorrect ? 'MÜKEMMEL!' : 'YANLIŞ CEVAP'}
        </Typography>

        {!roundResult.isCorrect && correctAnswer && (
          <Typography variant="body1" color="text.secondary" sx={{ mb: 4, fontWeight: 500 }}>
            Doğru cevap: <strong style={{ color: '#1e293b', fontSize: '1.1em' }}>{correctAnswer}</strong>
          </Typography>
        )}

        <Box sx={{ 
          display: 'flex', justifyContent: 'space-around', alignItems: 'center', 
          p: 3, borderRadius: 4, 
          background: 'linear-gradient(145deg, rgba(255,255,255,0.9), rgba(255,255,255,0.5))', 
          backdropFilter: 'blur(20px)', mb: 4, 
          border: '1px solid rgba(255,255,255,0.8)', 
          boxShadow: '0 10px 40px rgba(0,0,0,0.08), inset 0 2px 4px rgba(255,255,255,0.8)' 
        }}>
          <Box sx={{ textAlign: 'center', flex: 1 }}>
            <Typography variant="h3" fontWeight={900} sx={{ color: modernColors.primary[500] }}>{roundResult.myScore}</Typography>
            <Typography variant="subtitle2" color="text.secondary" fontWeight={800} textTransform="uppercase" letterSpacing={1.5}>Ben</Typography>
          </Box>
          <Divider orientation="vertical" flexItem sx={{ opacity: 0.6, mx: 2, borderColor: 'rgba(0,0,0,0.1)' }} />
          <Box sx={{ textAlign: 'center', flex: 1 }}>
            <Typography variant="h3" fontWeight={900} sx={{ color: modernColors.error[500] }}>{roundResult.opponentScore}</Typography>
            <Typography variant="subtitle2" color="text.secondary" fontWeight={800} textTransform="uppercase" letterSpacing={1.5}>{isBot ? 'Bot' : 'Rakip'}</Typography>
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
            background: modernColors.gradients.primary,
            boxShadow: '0 8px 25px rgba(99,102,241,0.4)',
            transition: 'all 0.3s ease',
            '&:hover': {
              background: modernColors.gradients.primary,
              transform: 'translateY(-3px)',
              boxShadow: '0 15px 35px rgba(99,102,241,0.5)',
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
      <Box sx={{ textAlign: 'center', py: 3 }} component={motion.div} initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ type: 'spring', damping: 20 }}>
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: 'spring', bounce: 0.6, delay: 0.2 }}
        >
          <Typography variant="h1" sx={{ mb: 2, filter: 'drop-shadow(0 15px 25px rgba(0,0,0,0.15))', fontSize: '6rem' }}>
            {won ? '🏆' : draw ? '🤝' : '😔'}
          </Typography>
        </motion.div>

        <Typography variant="h2" fontWeight={900} sx={{ 
          mb: 1, 
          background: won ? modernColors.gradients.success : draw ? modernColors.gradients.sunset : modernColors.gradients.error, 
          WebkitBackgroundClip: 'text', 
          WebkitTextFillColor: 'transparent',
          filter: 'drop-shadow(0 4px 8px rgba(0,0,0,0.1))'
        }}>
          {won ? 'ZAFER SENİN!' : draw ? 'KIYASIYA BERABERLİK!' : 'KAYBETTİN'}
        </Typography>

        <Typography variant="h6" color="text.secondary" fontWeight={800} sx={{ mb: 5, letterSpacing: 1 }}>
          SKOR: {myScore} – {opponentScore} <span style={{ opacity: 0.5, fontSize: '0.85em' }}>({totalRounds} Soru)</span>
        </Typography>

        {rating && (
          <motion.div initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.5, type: 'spring' }}>
            <Chip
              icon={<EmojiEvents sx={{ fontSize: 24 }} />}
              label={`YENİ ELO: ${Math.round(rating.elo_rating)}`}
              sx={{
                mb: 6,
                px: 3,
                py: 4,
                fontSize: 20,
                fontWeight: 900,
                background: 'linear-gradient(135deg, rgba(99,102,241,0.15), rgba(99,102,241,0.05))',
                color: modernColors.primary[600],
                border: `2px solid ${modernColors.primary[200]}`,
                boxShadow: '0 8px 30px rgba(99,102,241,0.2)',
                borderRadius: 4
              }}
            />
          </motion.div>
        )}

        {roundHistory && roundHistory.length > 0 && (
          <Box sx={{ 
            mb: 6, textAlign: 'left', 
            background: 'linear-gradient(145deg, rgba(255,255,255,0.8), rgba(255,255,255,0.4))', 
            backdropFilter: 'blur(20px)', borderRadius: 4, p: 4, 
            border: '1px solid rgba(255,255,255,0.9)', 
            boxShadow: '0 12px 40px rgba(0,0,0,0.06)' 
          }}>
            <Typography variant="overline" fontWeight={900} color="#64748b" sx={{ display: 'block', mb: 3, letterSpacing: 2, fontSize: '0.9rem' }}>
              MAÇ ÖZETİ
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              {roundHistory.map((r, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.6 + i * 0.1, type: 'spring' }}
                >
                  <Box
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 2.5,
                      p: 2.5,
                      borderRadius: 3,
                      background: r.isCorrect ? 'linear-gradient(135deg, rgba(34,197,94,0.15), rgba(34,197,94,0.05))' : 'linear-gradient(135deg, rgba(239,68,68,0.15), rgba(239,68,68,0.05))',
                      border: `1px solid ${r.isCorrect ? 'rgba(34,197,94,0.3)' : 'rgba(239,68,68,0.3)'}`,
                      boxShadow: 'inset 0 2px 5px rgba(255,255,255,0.5)'
                    }}
                  >
                    {r.isCorrect ? <CheckCircle sx={{ fontSize: 24, color: modernColors.success[500] }} /> : <Cancel sx={{ fontSize: 24, color: modernColors.error[500] }} />}
                    <Typography variant="body1" fontWeight={800} sx={{ flex: 1, color: '#1e293b', letterSpacing: 0.5 }}>
                      Soru {r.questionOrder + 1}
                    </Typography>
                    <Typography variant="body1" fontWeight={900} sx={{ color: r.isCorrect ? modernColors.success[500] : modernColors.error[500], fontSize: '1.1rem' }}>
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
            fontSize: '18px',
            borderRadius: 4,
            px: 8,
            py: 2.5,
            background: modernColors.gradients.primary,
            boxShadow: '0 10px 30px rgba(99,102,241,0.4)',
            transition: 'all 0.3s ease',
            '&:hover': {
              background: modernColors.gradients.primary,
              transform: 'translateY(-4px)',
              boxShadow: '0 20px 40px rgba(99,102,241,0.6)',
            }
          }}
        >
          YENİ DÜELLO BAŞLAT
        </Button>
      </Box>
    );
  }

  return null;
}
