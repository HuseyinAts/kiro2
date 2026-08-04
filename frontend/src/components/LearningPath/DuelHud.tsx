import { Box, Typography } from '@mui/material';
import { Person, SmartToy } from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import DuelTimer from './DuelTimer';

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
    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
      <Box sx={{ textAlign: 'center', minWidth: 60 }}>
        <Person sx={{ fontSize: 24, color: '#6366f1', mb: 0.5 }} />
        <AnimatePresence mode="popLayout">
          <motion.div
            key={myScore}
            initial={{ y: -10, opacity: 0, scale: 0.8 }}
            animate={{ y: 0, opacity: 1, scale: 1 }}
            exit={{ y: 10, opacity: 0, scale: 0.8 }}
            transition={{ type: 'spring', stiffness: 300, damping: 20 }}
          >
            <Typography variant="h5" fontWeight={900} sx={{ color: '#6366f1', lineHeight: 1 }}>
              {myScore}
            </Typography>
          </motion.div>
        </AnimatePresence>
        <Typography variant="caption" color="text.secondary" fontWeight={700}>Ben</Typography>
      </Box>

      <Box sx={{ textAlign: 'center', flex: 1 }}>
        <DuelTimer timeLeft={timeLeft} />
        <Typography variant="caption" color="text.secondary" fontWeight={700} sx={{ mt: 1, display: 'block' }}>
          Soru {currentRound} / {totalRounds}
        </Typography>
      </Box>

      <Box sx={{ textAlign: 'center', minWidth: 60 }}>
        {isBot ? <SmartToy sx={{ fontSize: 24, color: '#f59e0b', mb: 0.5 }} /> : <Person sx={{ fontSize: 24, color: '#f59e0b', mb: 0.5 }} />}
        <AnimatePresence mode="popLayout">
          <motion.div
            key={opponentScore}
            initial={{ y: -10, opacity: 0, scale: 0.8 }}
            animate={{ y: 0, opacity: 1, scale: 1 }}
            exit={{ y: 10, opacity: 0, scale: 0.8 }}
            transition={{ type: 'spring', stiffness: 300, damping: 20 }}
          >
            <Typography variant="h5" fontWeight={900} sx={{ color: '#f59e0b', lineHeight: 1 }}>
              {opponentScore}
            </Typography>
          </motion.div>
        </AnimatePresence>
        <Typography variant="caption" color="text.secondary" fontWeight={700}>{isBot ? 'Bot' : 'Rakip'}</Typography>
      </Box>
    </Box>
  );
}
