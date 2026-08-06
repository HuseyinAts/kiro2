import { useState, useEffect } from 'react';
import { Box, Typography, Paper, IconButton } from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';
import { Close, Psychology } from '@mui/icons-material';
import modernColors from '../../theme/modern-colors';
import { useSensoryFeedback } from '../../hooks/useSensoryFeedback';

interface SocraticAIAvatarProps {
  message?: string;
  state?: 'idle' | 'thinking' | 'speaking';
  onClose?: () => void;
}

/**
 * 2026 Socratic AI Avatar (Kiro)
 * Holographic, liquid UI orb that guides the user via the Socratic method.
 * Uses CSS & Framer Motion instead of heavy Three.js for instant loading.
 */
export function SocraticAIAvatar({ message, state = 'idle', onClose }: SocraticAIAvatarProps) {
  const [isOpen, setIsOpen] = useState(!!message);
  const { playHover, playClick } = useSensoryFeedback();

  useEffect(() => {
    if (message) setIsOpen(true);
  }, [message]);

  const handleToggle = () => {
    playClick();
    if (isOpen && onClose) onClose();
    setIsOpen(!isOpen);
  };

  // Liquid Orb variants
  const orbVariants = {
    idle: {
      scale: [1, 1.05, 1],
      boxShadow: [
        `0px 0px 20px ${modernColors.primary[400]}40`,
        `0px 0px 40px ${modernColors.primary[500]}60`,
        `0px 0px 20px ${modernColors.primary[400]}40`
      ],
      transition: { duration: 4, repeat: Infinity, ease: 'easeInOut' }
    },
    thinking: {
      scale: [1, 1.15, 0.95, 1],
      boxShadow: [
        `0px 0px 20px ${modernColors.secondary[400]}80`,
        `0px 0px 60px ${modernColors.secondary[500]}AA`,
        `0px 0px 20px ${modernColors.secondary[400]}80`
      ],
      rotate: [0, 90, 180, 360],
      transition: { duration: 2, repeat: Infinity, ease: 'linear' }
    },
    speaking: {
      scale: [1, 1.1, 1, 1.05, 1],
      boxShadow: [
        `0px 0px 30px ${modernColors.primary[400]}80`,
        `0px 0px 70px ${modernColors.primary[300]}AA`,
        `0px 0px 30px ${modernColors.primary[400]}80`
      ],
      transition: { duration: 1.5, repeat: Infinity, ease: 'easeInOut' }
    }
  };

  return (
    <Box sx={{ position: 'fixed', bottom: 32, right: 32, zIndex: 9999, display: 'flex', alignItems: 'flex-end', gap: 2 }}>
      
      {/* Dialogue Bubble */}
      <AnimatePresence>
        {isOpen && message && (
          <motion.div
            initial={{ opacity: 0, x: 20, scale: 0.9 }}
            animate={{ opacity: 1, x: 0, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
          >
            <Paper
              elevation={0}
              sx={{
                p: 3,
                maxWidth: 320,
                borderRadius: 4,
                borderBottomRightRadius: 0,
                background: 'rgba(255, 255, 255, 0.85)',
                backdropFilter: 'blur(20px)',
                border: '1px solid rgba(255, 255, 255, 0.4)',
                boxShadow: '0 20px 40px rgba(0,0,0,0.1)',
                position: 'relative'
              }}
            >
              <IconButton 
                size="small" 
                onClick={handleToggle}
                onMouseEnter={playHover}
                sx={{ position: 'absolute', top: 8, right: 8, opacity: 0.5, '&:hover': { opacity: 1 } }}
              >
                <Close fontSize="small" />
              </IconButton>
              
              <Typography variant="subtitle2" fontWeight={800} color="primary" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <Psychology fontSize="small" /> Kiro AI
              </Typography>
              <Typography variant="body2" color="text.secondary" fontWeight={500} sx={{ lineHeight: 1.6 }}>
                {message}
              </Typography>
            </Paper>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Holographic Orb */}
      <motion.div
        variants={orbVariants}
        animate={state}
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.95 }}
        onClick={handleToggle}
        onMouseEnter={playHover}
        style={{
          width: 64,
          height: 64,
          borderRadius: '50%',
          background: `radial-gradient(circle at 30% 30%, ${modernColors.primary[300]}, ${modernColors.primary[600]})`,
          border: `2px solid rgba(255, 255, 255, 0.4)`,
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'white',
        }}
      >
        <Psychology sx={{ fontSize: 32, opacity: 0.9 }} />
      </motion.div>
    </Box>
  );
}
