import { memo } from 'react';
import { Box, Container, Typography, Skeleton } from '@mui/material';
import { LocalFireDepartment } from '@mui/icons-material';
import { motion } from 'framer-motion';
import { useAuthStore } from '@/store/authStore';
import { DashboardStats } from './types';

interface DashboardHeaderProps {
  stats: DashboardStats;
  loading: boolean;
}

export const DashboardHeader = memo(({ stats, loading }: DashboardHeaderProps) => {
  const { user } = useAuthStore();

  return (
    <Box
      sx={{
        pt: { xs: 8, md: 12 },
        pb: { xs: 4, md: 6 },
        position: 'relative',
        background: 'transparent',
      }}
    >
      <Container maxWidth="xl">
        <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, alignItems: { xs: 'flex-start', md: 'flex-end' }, justifyContent: 'space-between', gap: 4 }}>
          <Box>
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}>
              <Typography variant="h1" sx={{ fontFamily: 'var(--k-font-serif)', fontSize: { xs: '3.5rem', md: '6rem' }, fontWeight: 400, letterSpacing: '-0.03em', color: 'var(--k-text)', lineHeight: 0.9 }}>
                Hoş geldin,
                <br />
                <span style={{ color: 'var(--k-coral)' }}>{user?.ad || 'Öğrenci'}.</span>
              </Typography>
            </motion.div>
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8, delay: 0.1, ease: [0.16, 1, 0.3, 1] }}>
              <Typography variant="h5" sx={{ mt: 3, color: 'var(--k-text-muted)', fontFamily: 'var(--k-font-sans)', fontWeight: 400, maxWidth: 600, letterSpacing: '-0.01em', lineHeight: 1.5 }}>
                {stats.tamamlanan_sinavlar > 0
                  ? `${stats.tamamlanan_sinavlar} sefer fethe çıktınız. Mevcut bilgelik ortalamanız %${stats.ortalama_puan.toFixed(0)}.`
                  : 'Zihinsel uyanışınıza başlamak için ilk yolculuğunuza adım atın.'}
              </Typography>
            </motion.div>
          </Box>

          <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.8, delay: 0.2, ease: [0.16, 1, 0.3, 1] }}>
            <Box
              role="status"
              sx={{
                display: 'flex', alignItems: 'center', gap: 2,
                p: 3, borderRadius: '24px',
                background: 'color-mix(in srgb, var(--k-surface) 50%, transparent)',
                backdropFilter: 'blur(20px)',
                border: '1px solid var(--k-border-faint)',
              }}
            >
              <LocalFireDepartment sx={{ fontSize: 40, color: 'var(--k-coral)' }} />
              <Box>
                <Typography variant="h3" sx={{ fontWeight: 400, fontFamily: 'var(--k-font-serif)', color: 'var(--k-text)', lineHeight: 1 }}>
                  {loading ? <Skeleton width={40} /> : stats.gunluk_seri}
                </Typography>
                <Typography variant="body2" sx={{ color: 'var(--k-text-muted)', fontWeight: 500, letterSpacing: '0.05em', textTransform: 'uppercase', mt: 0.5 }}>
                  GÜN SERİSİ
                </Typography>
              </Box>
            </Box>
          </motion.div>
        </Box>
      </Container>
    </Box>
  );
});

DashboardHeader.displayName = 'DashboardHeader';
