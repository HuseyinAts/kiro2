import { Box, Typography } from '@mui/material';
import { Person, SmartToy } from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import DuelTimer from './DuelTimer';
import modernColors from '../../theme/modern-colors';

interface DuelHudProps {
  myScore: number;
  opponentScore: number;
  isBot: boolean;
  timeLeft: number;
  currentRound: number;
  totalRounds: number;
}

export default function DuelHud({ myScore, opponentScore, isBot, timeLeft, currentRound, totalRounds }: DuelHudProps) {
  return (
    <Box sx={{ 
      display: 'flex', alignItems: 'center', justifyContent: 'space-between', 
      mb: 4, p: 2, borderRadius: 4,
      background: 'rgba(255,255,255,0.4)',
      backdropFilter: 'blur(10px)',
      border: '1px solid rgba(255,255,255,0.5)',
      boxShadow: '0 4px 20px rgba(0,0,0,0.05)'
    }}>
      {/* Player Score */}
      <Box sx={{ textAlign: 'center', minWidth: 80, position: 'relative' }}>
        <Person sx={{ fontSize: 28, color: modernColors.primary[500], mb: 0.5, filter: 'drop-shadow(0 0 8px rgba(99,102,241,0.5))' }} />
        <AnimatePresence mode="popLayout">
          <motion.div
            key={myScore}
            initial={{ y: -20, opacity: 0, scale: 1.5, color: '#fff' }}
            animate={{ y: 0, opacity: 1, scale: 1, color: modernColors.primary[600] }}
            exit={{ y: 20, opacity: 0, scale: 0.5 }}
            transition={{ type: 'spring', stiffness: 500, damping: 25 }}
          >
            <Typography variant="h4" fontWeight={900} sx={{ lineHeight: 1, textShadow: '0 2px 10px rgba(99,102,241,0.3)' }}>
              {myScore}
            </Typography>
          </motion.div>
        </AnimatePresence>
        <Typography variant="caption" color="text.secondary" fontWeight={800} sx={{ letterSpacing: 1 }}>BEN</Typography>
      </Box>

      {/* Center Timer & Round */}
      <Box sx={{ textAlign: 'center', flex: 1, px: 2 }}>
        <DuelTimer timeLeft={timeLeft} />
        <Typography variant="caption" fontWeight={800} sx={{ mt: 1.5, display: 'inline-block', backgroundColor: 'rgba(0,0,0,0.05)', px: 2, py: 0.5, borderRadius: 2, color: '#64748b' }}>
          RAUND {currentRound} / {totalRounds}
        </Typography>
      </Box>

      {/* Opponent Score */}
      <Box sx={{ textAlign: 'center', minWidth: 80, position: 'relative' }}>
        {isBot 
          ? <SmartToy sx={{ fontSize: 28, color: modernColors.error[500], mb: 0.5, filter: 'drop-shadow(0 0 8px rgba(239,68,68,0.5))' }} /> 
          : <Person sx={{ fontSize: 28, color: modernColors.error[500], mb: 0.5, filter: 'drop-shadow(0 0 8px rgba(239,68,68,0.5))' }} />
        }
        <AnimatePresence mode="popLayout">
          <motion.div
            key={opponentScore}
            initial={{ y: -20, opacity: 0, scale: 1.5, color: '#fff' }}
            animate={{ y: 0, opacity: 1, scale: 1, color: modernColors.error[700] }}
            exit={{ y: 20, opacity: 0, scale: 0.5 }}
            transition={{ type: 'spring', stiffness: 500, damping: 25 }}
          >
            <Typography variant="h4" fontWeight={900} sx={{ lineHeight: 1, textShadow: '0 2px 10px rgba(239,68,68,0.3)' }}>
              {opponentScore}
            </Typography>
          </motion.div>
        </AnimatePresence>
        <Typography variant="caption" color="text.secondary" fontWeight={800} sx={{ letterSpacing: 1 }}>{isBot ? 'BOT' : 'RAKİP'}</Typography>
      </Box>
    </Box>
  );
}
