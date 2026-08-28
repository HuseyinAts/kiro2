import { memo } from 'react';
import { Grid, Box, Typography, CircularProgress, Chip } from '@mui/material';
import { Assessment, HourglassEmpty, ArrowForward } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { StaggerItem } from '@/components/Animations/PageTransition';
import { GlassCard } from '@/components/ui/GlassCard';
import { ModernButton } from '@/components/ui/ModernButton';
import { RecentExam } from './types';

interface RecentActivityProps {
  recentExams: RecentExam[];
  loading: boolean;
}

const formatRelativeTime = (dateStr: string): string => {
  const diff = Date.now() - new Date(dateStr).getTime();
  const minutes = Math.floor(diff / 60000);
  if (minutes < 60) { return `${minutes} dk önce`; }
  const hours = Math.floor(minutes / 60);
  if (hours < 24) { return `${hours} saat önce`; }
  const days = Math.floor(hours / 24);
  return `${days} gün önce`;
};

export const RecentActivity = memo(({ recentExams, loading }: RecentActivityProps) => {
  const navigate = useNavigate();

  return (
    <Grid container spacing={3} sx={{ mt: 2 }}>
      <Grid item xs={12}>
        <StaggerItem>
          <GlassCard title="Son Sinavlar" subtitle="Son yaptigin sinavlar" gradient="var(--k-coral)" elevated>
            {loading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                <CircularProgress />
              </Box>
            ) : recentExams.length === 0 ? (
              <Box sx={{ textAlign: 'center', py: 4 }}>
                <HourglassEmpty sx={{ fontSize: 48, color: 'text.disabled', mb: 1 }} />
                <Typography variant="body1" color="text.secondary">Henuz sinav yapmadiniz</Typography>
                <ModernButton variant="glass" onClick={() => navigate('/exam/start')} sx={{ mt: 2 }}>Ilk Sinavina Basla</ModernButton>
              </Box>
            ) : (
              <>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  {recentExams.map((exam) => (
                    <Box
                      key={exam.sinav_id}
                      onClick={() => navigate(`/exam/${exam.sinav_id}/results`)}
                      sx={{
                        display: 'flex', alignItems: 'center', justifyContent: 'space-between', p: 2,
                        background: 'color-mix(in srgb, var(--k-surface) 40%, transparent)', borderRadius: '12px', cursor: 'pointer',
                        transition: 'all 0.2s',
                        '&:hover': { background: 'color-mix(in srgb, var(--k-surface) 80%, transparent)', transform: 'translateX(4px)' },
                      }}
                    >
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                        <Box sx={{ width: 40, height: 40, borderRadius: '8px', background: 'var(--k-coral)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white' }}>
                          <Assessment />
                        </Box>
                        <Box>
                          <Typography variant="body2" fontWeight={600}>{exam.sinav_adi || `${exam.sinav_tipi} Sinavi`}</Typography>
                          <Typography variant="caption" color="text.secondary">
                            {formatRelativeTime(exam.tarih)} | D:{exam.dogru_sayisi} Y:{exam.yanlis_sayisi} B:{exam.bos_sayisi}
                          </Typography>
                        </Box>
                      </Box>
                      <Chip
                        label={`%${exam.puan.toFixed(0)}`}
                        size="small"
                        sx={{ background: exam.puan >= 70 ? 'var(--k-success)' : 'var(--k-risk)', color: 'white', fontWeight: 700 }}
                      />
                    </Box>
                  ))}
                </Box>
                <ModernButton variant="glass" fullWidth endIcon={<ArrowForward />} onClick={() => navigate('/exam/history')} sx={{ mt: 2 }}>
                  Tumunu Gor
                </ModernButton>
              </>
            )}
          </GlassCard>
        </StaggerItem>
      </Grid>
    </Grid>
  );
});

RecentActivity.displayName = 'RecentActivity';
