/**
 * SubjectThetaCards — Dashboard seviye kartları
 * GET /api/v1/estimate/thetas  →  her ders için theta + seviye
 */
import { Box, Chip, CircularProgress, Grid, LinearProgress, Stack, Typography } from '@mui/material';
import { AutoAwesome } from '@mui/icons-material';
import { useQuery } from 'react-query';
import { motion } from 'framer-motion';
import { apiRequest } from '../../utils/apiHelpers';
import { GlassCard } from '../ui/GlassCard';
import { useSensoryFeedback } from '../../hooks/useSensoryFeedback';

interface DersTheta {
  ders_kodu: string;
  ders_adi:  string;
  theta:     number;
  se:        number;
  seviye:    string;
}

const SEVİYE_RENK: Record<string, 'error' | 'warning' | 'info' | 'success' | 'primary'> = {
  'Temel':       'error',
  'Orta-Temel':  'warning',
  'Orta':        'info',
  'Orta-İleri':  'primary',
  'İleri':       'success',
};

// θ [-3, +3] → [0, 100]
function thetaToPercent(theta: number) {
  return Math.min(100, Math.max(0, ((theta + 3) / 6) * 100));
}

const MotionGrid = motion(Grid);

export default function SubjectThetaCards() {
  const { playHover, playClick } = useSensoryFeedback();

  const { data = [], isLoading: loading } = useQuery<DersTheta[]>({
    queryKey: ['dashboard-thetas'],
    queryFn: async () => {
      const res = await apiRequest<DersTheta[]>('/api/v1/estimate/thetas');
      return Array.isArray(res) ? res : [];
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  if (loading) {return <CircularProgress size={28} />;}
  if (!data.length) {return (
    <Typography variant="body2" color="text.secondary">
      Henüz tamamlanmış ders testi yok. CAT veya Seviye Tespiti yap.
    </Typography>
  );}

  return (
    <Box>
      <Stack direction="row" spacing={1} alignItems="center" mb={3}>
        <AutoAwesome sx={{ color: 'var(--k-coral)', fontSize: 28 }} />
        <Typography variant="h5" fontWeight={800} letterSpacing={-0.5} sx={{ color: 'var(--k-text)' }}>
          Derin Öğrenme Analizin
        </Typography>
      </Stack>
      <Grid container spacing={2}>
        {data.map((d: DersTheta, index: number) => {
          const pct   = thetaToPercent(d.theta);
          const renk  = SEVİYE_RENK[d.seviye] ?? 'info';
          return (
            <MotionGrid 
              item xs={12} sm={6} md={4} key={d.ders_kodu}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1, type: 'spring', stiffness: 300, damping: 24 }}
            >
              <GlassCard 
                onMouseEnter={playHover} 
                onClick={playClick}
                sx={{ 
                  borderRadius: 4, 
                  cursor: 'pointer',
                  p: 3, 
                  borderLeft: `6px solid var(--k-${renk === 'primary' ? 'coral' : renk === 'error' ? 'risk' : renk === 'warning' ? 'risk' : renk === 'info' ? 'subj-mat' : 'success'})`,
                  '&:hover': {
                    transform: 'translateY(-4px)',
                  }
                }}
              >
                <Stack direction="row" justifyContent="space-between" alignItems="center">
                  <Typography variant="subtitle1" fontWeight={700}>{d.ders_adi}</Typography>
                  <Chip size="small" label={d.seviye} color={renk} sx={{ fontWeight: 800, borderRadius: 2 }} />
                </Stack>
                <LinearProgress
                  variant="determinate" value={pct} color={renk}
                  sx={{ mt: 2, mb: 1, height: 6, borderRadius: 3 }}
                />
                <Typography variant="caption" fontWeight={600} color="text.secondary">
                  Beceri Seviyesi (θ): {d.theta.toFixed(2)} <span style={{ opacity: 0.5 }}>| Hassasiyet (SE): {d.se.toFixed(2)}</span>
                </Typography>
              </GlassCard>
            </MotionGrid>
          );
        })}
      </Grid>
    </Box>
  );
}
