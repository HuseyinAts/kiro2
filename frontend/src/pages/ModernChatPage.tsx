/**
 * Modern Chat Page
 * Glassmorphism ile modern chat deneyimi
 */

import {
  Chat as ChatIcon,
  ArrowBack as BackIcon,
  Psychology as AIIcon,
  School as SchoolIcon,
} from '@mui/icons-material';
import {
  Container,
  Typography,
  Box,
  IconButton,
  Chip,
} from '@mui/material';
import { motion } from 'framer-motion';
import * as React from 'react';
import { useNavigate } from 'react-router-dom';

import { TurkishChatInterface } from '../components/Chat/TurkishChatInterface';
import { GlassCard } from '../components/ui/GlassCard';
import { useAuthStore } from '../store/authStore';
import { modernColors } from '../theme/modern-colors';

export const ModernChatPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuthStore();

  return (
    <Container maxWidth="xl" sx={{ py: 4, height: 'calc(100vh - 100px)' }}>
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <IconButton
              onClick={() => navigate('/dashboard')}
              sx={{
                background: 'rgba(255,255,255,0.9)',
                backdropFilter: 'blur(10px)',
                '&:hover': {
                  background: 'rgba(255,255,255,1)',
                },
              }}
            >
              <BackIcon />
            </IconButton>

            <Box
              sx={{
                width: 56,
                height: 56,
                borderRadius: '16px',
                background: modernColors.gradients.purple,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <ChatIcon sx={{ fontSize: 32, color: 'white' }} />
            </Box>

            <Box>
              <Typography
                variant="h5"
                sx={{
                  fontWeight: 700,
                  background: modernColors.gradients.purple,
                  backgroundClip: 'text',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                }}
              >
                AI Öğretmen Asistanı
              </Typography>
              <Box sx={{ display: 'flex', gap: 1, mt: 0.5 }}>
                <Chip
                  icon={<AIIcon sx={{ fontSize: 16 }} />}
                  label="Yapay Zeka Destekli"
                  size="small"
                  sx={{
                    background: modernColors.gradients.purple,
                    color: 'white',
                    '& .MuiChip-icon': { color: 'white' },
                  }}
                />
                <Chip
                  icon={<SchoolIcon sx={{ fontSize: 16 }} />}
                  label="Türkçe Eğitim"
                  size="small"
                  variant="outlined"
                />
              </Box>
            </Box>
          </Box>
        </Box>
      </motion.div>

      {/* Chat Interface */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        style={{ height: 'calc(100% - 100px)' }}
      >
        <GlassCard sx={{ height: '100%', display: 'flex', flexDirection: 'column', p: 0 }}>
          <TurkishChatInterface studentId={user?.id || 'anonymous'} />
        </GlassCard>
      </motion.div>
    </Container>
  );
};

export default ModernChatPage;
