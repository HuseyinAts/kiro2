import { Typography } from '@mui/material';
import { motion } from 'framer-motion';

interface DuelTimerProps {
  timeLeft: number;
}

export default function DuelTimer({ timeLeft }: DuelTimerProps) {
  const timerColor = timeLeft > 10 ? '#22c55e' : timeLeft > 5 ? '#f59e0b' : '#ef4444';

  return (
    <motion.div
      animate={{ scale: timeLeft <= 5 ? [1, 1.1, 1] : 1 }}
      transition={{ repeat: timeLeft <= 5 ? Infinity : 0, duration: 1 }}
      style={{
        width: 48,
        height: 48,
        borderRadius: '50%',
        border: `3px solid ${timerColor}`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        margin: '0 auto',
        boxShadow: `0 0 15px ${timerColor}40`,
        transition: 'border-color 0.3s ease, box-shadow 0.3s ease',
      }}
    >
      <Typography variant="h6" fontWeight={900} sx={{ color: timerColor, lineHeight: 1 }}>
        {timeLeft}
      </Typography>
    </motion.div>
  );
}
