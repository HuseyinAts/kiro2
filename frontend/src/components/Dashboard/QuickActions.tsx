import { memo } from 'react';
import { Grid, Box, Typography } from '@mui/material';
import {
  Assessment, Chat, Timeline, MenuBook, TrendingUp,
  School, EmojiEvents, HourglassEmpty, LocalFireDepartment,
  SportsEsports, AutoStories, CalendarMonth, Map
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { StaggerItem } from '@/components/Animations/PageTransition';
import { GlassCard } from '@/components/ui/GlassCard';
import modernColors from '@/theme/modern-colors';

export const QuickActions = memo(() => {
  const navigate = useNavigate();

  const quickActions = [
    { title: 'Sınava Başla', icon: <Assessment sx={{ fontSize: 32 }} />, gradient: 'var(--k-coral)', path: '/exam/start' },
    { title: 'AI Sohbet', icon: <Chat sx={{ fontSize: 32 }} />, gradient: 'var(--k-subj-fiz)', path: '/chat' },
    { title: 'Öğrenme Yolu', icon: <Timeline sx={{ fontSize: 32 }} />, gradient: 'var(--k-success)', path: '/learning-path' },
    { title: 'Sınav Geçmişi', icon: <MenuBook sx={{ fontSize: 32 }} />, gradient: 'var(--k-risk)', path: '/exam/history' },
    { title: 'Adaptif Test', icon: <TrendingUp sx={{ fontSize: 32 }} />, gradient: 'var(--k-subj-mat)', path: '/cat' },
    { title: 'Seviye Tespiti', icon: <School sx={{ fontSize: 32 }} />, gradient: 'var(--k-subj-kim)', path: '/assessment' },
    { title: 'YKS Tahmini', icon: <EmojiEvents sx={{ fontSize: 32 }} />, gradient: 'var(--k-subj-tur)', path: '/estimate' },
    { title: 'Tekrar Et (FSRS)', icon: <HourglassEmpty sx={{ fontSize: 32 }} />, gradient: 'var(--k-subj-biy)', path: '/fsrs-review' },
    { title: 'Lig Sıralaması', icon: <LocalFireDepartment sx={{ fontSize: 32 }} />, gradient: 'var(--k-risk)', path: '/league' },
    { title: '1v1 Düello', icon: <SportsEsports sx={{ fontSize: 32 }} />, gradient: 'var(--k-subj-edb)', path: '/duel' },
    { title: 'KIRO Destanı', icon: <AutoStories sx={{ fontSize: 32 }} />, gradient: 'var(--k-subj-tar)', path: '/kiro-destan' },
    { title: 'Günlük Planım', icon: <CalendarMonth sx={{ fontSize: 32 }} />, gradient: 'var(--k-subj-cog)', path: '/daily-plan' },
    { title: 'Öğrenme Haritası', icon: <Map sx={{ fontSize: 32 }} />, gradient: 'var(--k-subj-fel)', path: '/learning-path-map' },
    { title: 'Veli Paneli', icon: <School sx={{ fontSize: 32 }} />, gradient: 'var(--k-subj-din)', path: '/parent-new' },
  ];

  return (
    <StaggerItem>
      <GlassCard title="Hizli Erisim" subtitle="Sik kullandigin ozelliklere hizlica git" gradient="var(--k-coral)" elevated>
        <Grid container spacing={2}>
          {quickActions.map((action, index) => (
            <Grid item xs={6} md={3} key={index}>
              <motion.div whileHover={{ scale: 1.05, y: -5 }} whileTap={{ scale: 0.95 }}>
                <Box
                  role="button"
                  aria-label={action.title}
                  tabIndex={0}
                  onClick={() => navigate(action.path)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      navigate(action.path);
                    }
                  }}
                  sx={{
                    background: action.gradient,
                    borderRadius: '16px',
                    p: 3,
                    textAlign: 'center',
                    cursor: 'pointer',
                    boxShadow: modernColors.shadow.md,
                    transition: 'all 0.3s',
                    '&:hover': { boxShadow: modernColors.shadow.lg },
                    '&:focus': { outline: '2px solid rgba(59, 130, 246, 0.5)', outlineOffset: '2px' },
                  }}
                >
                  <Box sx={{ color: 'white', mb: 1 }}>{action.icon}</Box>
                  <Typography variant="body2" sx={{ color: 'white', fontWeight: 600 }}>{action.title}</Typography>
                </Box>
              </motion.div>
            </Grid>
          ))}
        </Grid>
      </GlassCard>
    </StaggerItem>
  );
});

QuickActions.displayName = 'QuickActions';
