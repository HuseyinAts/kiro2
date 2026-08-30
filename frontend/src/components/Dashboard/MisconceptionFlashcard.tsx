import * as React from 'react';
import { useState } from 'react';
import { Box, Typography, Button, Paper, useTheme, alpha } from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';
import LightbulbOutlinedIcon from '@mui/icons-material/LightbulbOutlined';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import CloseIcon from '@mui/icons-material/Close';

interface MisconceptionFlashcardProps {
  misconceptionName: string;
  distractor: string;
  refutation: string;
  takeaway: string;
  onDismiss: () => void;
}

export const MisconceptionFlashcard: React.FC<MisconceptionFlashcardProps> = ({
  misconceptionName,
  distractor,
  refutation,
  takeaway,
  onDismiss,
}) => {
  const theme = useTheme();
  const [isFlipped, setIsFlipped] = useState(false);
  const [isVisible, setIsVisible] = useState(true);

  const handleFlip = () => {
    setIsFlipped((prev) => !prev);
  };

  const handleDismiss = () => {
    setIsVisible(false);
    setTimeout(onDismiss, 400); // Wait for exit animation
  };

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.9 }}
          transition={{ duration: 0.4, type: 'spring' }}
          style={{ width: '100%', marginBottom: theme.spacing(3), perspective: 1000 }}
        >
          <motion.div
            animate={{ rotateX: isFlipped ? 180 : 0 }}
            transition={{ duration: 0.6, type: 'spring', stiffness: 200, damping: 20 }}
            style={{ width: '100%', position: 'relative', transformStyle: 'preserve-3d' }}
          >
            {/* FRONT SIDE */}
            <Paper
              elevation={0}
              sx={{
                p: 3,
                borderRadius: 4,
                background: `linear-gradient(135deg, ${alpha(theme.palette.error.main, 0.05)} 0%, ${alpha(
                  theme.palette.background.paper,
                  0.8,
                )} 100%)`,
                backdropFilter: 'blur(10px)',
                border: `1px solid ${alpha(theme.palette.error.main, 0.2)}`,
                backfaceVisibility: 'hidden',
                position: isFlipped ? 'absolute' : 'relative',
                top: 0,
                left: 0,
                width: '100%',
                zIndex: isFlipped ? 0 : 1,
              }}
            >
              <Box display="flex" alignItems="flex-start" justifyContent="space-between" mb={2}>
                <Box display="flex" alignItems="center" gap={1.5}>
                  <Box
                    sx={{
                      bgcolor: alpha(theme.palette.error.main, 0.1),
                      p: 1,
                      borderRadius: 2,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    <LightbulbOutlinedIcon color="error" />
                  </Box>
                  <Box>
                    <Typography variant="overline" color="error.main" fontWeight="bold">
                      KAVRAM YANILGISI TESPİT EDİLDİ
                    </Typography>
                    <Typography variant="h6" fontWeight="bold" color="text.primary">
                      {misconceptionName}
                    </Typography>
                  </Box>
                </Box>
                <Button
                  onClick={handleDismiss}
                  size="small"
                  sx={{ minWidth: 0, p: 0.5, color: 'text.secondary' }}
                >
                  <CloseIcon fontSize="small" />
                </Button>
              </Box>

              <Typography variant="body1" color="text.secondary" mb={3} sx={{ fontStyle: 'italic' }}>
                &quot;Sık düşülen bir hata: {distractor}&quot;
              </Typography>

              <Button
                variant="contained"
                color="error"
                fullWidth
                endIcon={<ArrowForwardIcon />}
                onClick={handleFlip}
                sx={{ borderRadius: 2, textTransform: 'none', fontWeight: 600 }}
              >
                Nasıl Düzeltilir? Görmek İçin Çevir
              </Button>
            </Paper>

            {/* BACK SIDE */}
            <Paper
              elevation={4}
              sx={{
                p: 3,
                borderRadius: 4,
                background: `linear-gradient(135deg, ${alpha(theme.palette.success.main, 0.05)} 0%, ${alpha(
                  theme.palette.background.paper,
                  0.9,
                )} 100%)`,
                backdropFilter: 'blur(10px)',
                border: `1px solid ${alpha(theme.palette.success.main, 0.3)}`,
                backfaceVisibility: 'hidden',
                transform: 'rotateX(180deg)',
                position: isFlipped ? 'relative' : 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                zIndex: isFlipped ? 1 : 0,
              }}
            >
              <Box display="flex" alignItems="center" gap={1.5} mb={2}>
                <Box
                  sx={{
                    bgcolor: alpha(theme.palette.success.main, 0.1),
                    p: 1,
                    borderRadius: 2,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <CheckCircleOutlineIcon color="success" />
                </Box>
                <Box>
                  <Typography variant="overline" color="success.main" fontWeight="bold">
                    DOĞRU KAVRAM
                  </Typography>
                  <Typography variant="h6" fontWeight="bold" color="text.primary">
                    Hap Bilgi
                  </Typography>
                </Box>
              </Box>

              <Typography variant="body1" color="text.primary" mb={2} fontWeight={500}>
                {refutation}
              </Typography>

              <Box sx={{ p: 2, bgcolor: alpha(theme.palette.primary.main, 0.05), borderRadius: 2, mb: 3 }}>
                <Typography variant="body2" color="primary.main" fontWeight="bold">
                  Akılda Kalsın:
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {takeaway}
                </Typography>
              </Box>

              <Box display="flex" gap={2}>
                <Button
                  variant="outlined"
                  color="inherit"
                  fullWidth
                  onClick={handleFlip}
                  sx={{ borderRadius: 2, textTransform: 'none' }}
                >
                  Tekrar Bak
                </Button>
                <Button
                  variant="contained"
                  color="success"
                  fullWidth
                  onClick={handleDismiss}
                  sx={{ borderRadius: 2, textTransform: 'none', fontWeight: 600 }}
                >
                  Anladım
                </Button>
              </Box>
            </Paper>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};
