import React from 'react';
import { Box, Typography, Grid, LinearProgress } from '@mui/material';
import { EmojiEvents, LocalFireDepartment, AutoAwesome } from '@mui/icons-material';

import { GlassCard } from '@/components/ui/GlassCard';

import type { UseLearningPathReturn } from '@/hooks/useLearningPath';

interface Props {
  learningPath: UseLearningPathReturn;
}

export const ModernProgressTrackingTab: React.FC<Props> = ({ learningPath }) => {
  const { pathNodes, currentNodeId, streak } = learningPath;

  const currentPathIdx = pathNodes.findIndex(n => n.id === currentNodeId);
  const pathProgress = pathNodes.length > 0 
    ? Math.round(((currentPathIdx === -1 ? pathNodes.filter(n => n.status === 'completed').length : currentPathIdx) / pathNodes.length) * 100) 
    : 0;
  
  const completedNodes = pathNodes.filter(n => n.status === 'completed').length;

  return (
    <Box sx={{ p: 1 }}>
      <Typography variant="h5" fontWeight={700} sx={{ mb: 4 }}>İlerleme ve İstatistikler</Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <GlassCard glassIntensity="medium" hoverable sx={{ height: '100%' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
              <Box sx={{ p: 1.5, borderRadius: 2, bgcolor: 'rgba(59, 130, 246, 0.1)', color: '#3b82f6' }}>
                <AutoAwesome sx={{ fontSize: 32 }} />
              </Box>
              <Box>
                <Typography variant="h4" fontWeight={800}>{pathProgress}%</Typography>
                <Typography variant="body2" color="text.secondary">Genel İlerleme</Typography>
              </Box>
            </Box>
            <LinearProgress variant="determinate" value={pathProgress} sx={{ height: 8, borderRadius: 4, bgcolor: 'rgba(0,0,0,0.05)', '& .MuiLinearProgress-bar': { borderRadius: 4, background: 'linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%)' } }} />
          </GlassCard>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <GlassCard glassIntensity="medium" hoverable sx={{ height: '100%' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Box sx={{ p: 1.5, borderRadius: 2, bgcolor: 'rgba(245, 158, 11, 0.1)', color: '#f59e0b' }}>
                <LocalFireDepartment sx={{ fontSize: 32 }} />
              </Box>
              <Box>
                <Typography variant="h4" fontWeight={800}>{streak?.dailyStreak || 0}</Typography>
                <Typography variant="body2" color="text.secondary">Günlük Seri (Streak)</Typography>
              </Box>
            </Box>
          </GlassCard>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <GlassCard glassIntensity="medium" hoverable sx={{ height: '100%' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Box sx={{ p: 1.5, borderRadius: 2, bgcolor: 'rgba(16, 185, 129, 0.1)', color: '#10b981' }}>
                <EmojiEvents sx={{ fontSize: 32 }} />
              </Box>
              <Box>
                <Typography variant="h4" fontWeight={800}>{completedNodes}</Typography>
                <Typography variant="body2" color="text.secondary">Tamamlanan Konu</Typography>
              </Box>
            </Box>
          </GlassCard>
        </Grid>
      </Grid>
    </Box>
  );
};
