import { memo } from 'react';
import { Grid, Typography, Skeleton } from '@mui/material';
import { School, TrendingUp, EmojiEvents, Timeline } from '@mui/icons-material';
import { StaggerItem } from '@/components/Animations/PageTransition';
import { GlassCard } from '@/components/ui/GlassCard';
import { DashboardStats } from './types';

interface StatsOverviewProps {
  stats: DashboardStats;
  loading: boolean;
}

export const StatsOverview = memo(({ stats, loading }: StatsOverviewProps) => {
  return (
    <Grid container spacing={3} sx={{ mb: 4 }}>
      <Grid item xs={12} sm={6} md={3}>
        <StaggerItem>
          <GlassCard icon={<School sx={{ fontSize: 28 }} />} gradient="var(--k-coral)" hoverable>
            <Typography variant="h4" sx={{ fontWeight: 800, mb: 0.5 }}>
              {loading ? <Skeleton width={40} /> : stats.tamamlanan_dersler}
            </Typography>
            <Typography variant="body2" color="text.secondary">Tamamlanan Ders</Typography>
          </GlassCard>
        </StaggerItem>
      </Grid>
      <Grid item xs={12} sm={6} md={3}>
        <StaggerItem>
          <GlassCard icon={<TrendingUp sx={{ fontSize: 28 }} />} gradient="var(--k-success)" hoverable>
            <Typography variant="h4" sx={{ fontWeight: 800, mb: 0.5 }}>
              {loading ? <Skeleton width={40} /> : `${stats.ortalama_puan.toFixed(0)}%`}
            </Typography>
            <Typography variant="body2" color="text.secondary">Ortalama Basari</Typography>
          </GlassCard>
        </StaggerItem>
      </Grid>
      <Grid item xs={12} sm={6} md={3}>
        <StaggerItem>
          <GlassCard icon={<EmojiEvents sx={{ fontSize: 28 }} />} gradient="var(--k-risk)" hoverable>
            <Typography variant="h4" sx={{ fontWeight: 800, mb: 0.5 }}>
              {loading ? <Skeleton width={40} /> : stats.tamamlanan_sinavlar}
            </Typography>
            <Typography variant="body2" color="text.secondary">Tamamlanan Sinav</Typography>
          </GlassCard>
        </StaggerItem>
      </Grid>
      <Grid item xs={12} sm={6} md={3}>
        <StaggerItem>
          <GlassCard icon={<Timeline sx={{ fontSize: 28 }} />} gradient="var(--k-coral-2)" hoverable>
            <Typography variant="h4" sx={{ fontWeight: 800, mb: 0.5 }}>
              {loading ? <Skeleton width={40} /> : `${Math.floor(stats.toplam_calisma_suresi / 60)}sa`}
            </Typography>
            <Typography variant="body2" color="text.secondary">Toplam Calisma</Typography>
          </GlassCard>
        </StaggerItem>
      </Grid>
    </Grid>
  );
});

StatsOverview.displayName = 'StatsOverview';
