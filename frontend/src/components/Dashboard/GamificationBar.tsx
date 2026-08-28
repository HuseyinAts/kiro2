import { memo } from 'react';
import { Box, Container, Typography, Stack, LinearProgress } from '@mui/material';
import { LocalFireDepartment, WorkspacePremium, EmojiEvents } from '@mui/icons-material';
import { motion } from 'framer-motion';
import modernColors from '@/theme/modern-colors';
import { GamificationProfile } from './types';

interface GamificationBarProps {
  gamification: GamificationProfile;
}

export const GamificationBar = memo(({ gamification }: GamificationBarProps) => {
  return (
    <Container maxWidth="xl" sx={{ mt: 0, position: 'relative', zIndex: 2, mb: 4 }}>
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8, delay: 0.3, ease: [0.16, 1, 0.3, 1] }}>
        <Box
          sx={{
            background: 'color-mix(in srgb, var(--k-surface) 30%, transparent)',
            backdropFilter: 'blur(20px)',
            borderRadius: '24px',
            border: '1px solid var(--k-border-faint)',
            color: 'var(--k-text)',
            px: 4,
            py: 3,
          }}
        >
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} alignItems={{ xs: 'stretch', sm: 'center' }} justifyContent="space-between">
            {/* XP + Level */}
            <Stack direction="row" spacing={2} alignItems="center" flex={1}>
              <Box
                sx={{
                  width: 44, height: 44, borderRadius: '12px', background: 'var(--k-coral)', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: modernColors.shadow.sm,
                }}
              >
                <Typography sx={{ color: 'white', fontWeight: 800, fontSize: 16 }}>
                  {gamification.current_level}
                </Typography>
              </Box>
              <Box flex={1} minWidth={120}>
                <Stack direction="row" justifyContent="space-between" mb={0.5}>
                  <Typography variant="caption" fontWeight={600} color="text.secondary">
                    Seviye {gamification.current_level}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {gamification.total_xp.toLocaleString('tr-TR')} / {gamification.xp_for_next_level.toLocaleString('tr-TR')} XP
                  </Typography>
                </Stack>
                <LinearProgress
                  variant="determinate"
                  value={Math.min(100, (gamification.total_xp / Math.max(1, gamification.xp_for_next_level)) * 100)}
                  sx={{
                    height: 8, borderRadius: 4, bgcolor: 'var(--k-border)', '& .MuiLinearProgress-bar': { borderRadius: 4, background: 'var(--k-coral)' },
                  }}
                />
              </Box>
            </Stack>

            {/* Badges and Streak */}
            <Stack direction="row" spacing={3} alignItems="center" justifyContent={{ xs: 'space-between', sm: 'flex-start' }}>
              <Stack direction="row" spacing={0.5} alignItems="center">
                <LocalFireDepartment sx={{ fontSize: 24, color: gamification.streak_active_today ? '#FF6B35' : '#ccc' }} />
                <Typography variant="body2" fontWeight={700}>{gamification.streak}</Typography>
                <Typography variant="caption" color="text.secondary">gun seri</Typography>
              </Stack>
              <Stack direction="row" spacing={0.5} alignItems="center">
                <WorkspacePremium sx={{ fontSize: 24, color: '#ffc107' }} />
                <Typography variant="body2" fontWeight={700}>{gamification.total_badges}</Typography>
                <Typography variant="caption" color="text.secondary">rozet</Typography>
              </Stack>
              {gamification.leaderboard_rank && (
                <Stack direction="row" spacing={0.5} alignItems="center">
                  <EmojiEvents sx={{ fontSize: 24, color: '#4caf50' }} />
                  <Typography variant="body2" fontWeight={700}>#{gamification.leaderboard_rank}</Typography>
                  <Typography variant="caption" color="text.secondary">siralama</Typography>
                </Stack>
              )}
            </Stack>
          </Stack>
        </Box>
      </motion.div>
    </Container>
  );
});

GamificationBar.displayName = 'GamificationBar';
