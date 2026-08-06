import React from 'react';
import { Box, Typography, Alert, CircularProgress, Grid } from '@mui/material';
import { PlayCircleFilled, Search } from '@mui/icons-material';

import { GlassCard } from '@/components/ui/GlassCard';
import { ModernButton } from '@/components/ui/ModernButton';

import type { UseLearningPathVideosReturn } from '@/hooks/useLearningPathVideos';

interface Props {
  videoData: UseLearningPathVideosReturn;
}

export const ModernVideoResourcesTab: React.FC<Props> = ({ videoData }) => {
  const { videos, videosLoading, videosError } = videoData;

  return (
    <Box sx={{ p: 1 }}>
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
        <Typography variant="h5" fontWeight={700}>Konu Anlatım Videoları</Typography>
        <ModernButton variant="glass" icon={<Search />}>Daha Fazla Ara</ModernButton>
      </Box>

      {videosError && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {videosError}
        </Alert>
      )}

      {videosLoading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
          <CircularProgress />
        </Box>
      ) : videos && Object.keys(videos).length > 0 ? (
        <Grid container spacing={3}>
          {Object.entries(videos).map(([topic, topicVideos]) => (
            <React.Fragment key={topic}>
              <Grid item xs={12}>
                <Typography variant="h6" fontWeight={600} sx={{ mt: 2, mb: 1, textTransform: 'capitalize' }}>
                  {topic.replace(/_/g, ' ')}
                </Typography>
              </Grid>
              {(topicVideos as unknown as any[]).map((video) => (
                <Grid item xs={12} sm={6} md={4} key={video.video_id}>
                  <GlassCard glassIntensity="light" hoverable sx={{ height: '100%', display: 'flex', flexDirection: 'column', p: 0, overflow: 'hidden' }}>
                    <Box sx={{ position: 'relative', paddingTop: '56.25%', backgroundColor: '#000' }}>
                      <img src={video.thumbnail || `https://img.youtube.com/vi/${video.video_id}/mqdefault.jpg`} alt={video.title} style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', objectFit: 'cover', opacity: 0.8 }} />
                      <PlayCircleFilled sx={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', color: 'white', fontSize: 48, opacity: 0.9, filter: 'drop-shadow(0 4px 8px rgba(0,0,0,0.3))' }} />
                      <Box sx={{ position: 'absolute', bottom: 8, right: 8, backgroundColor: 'rgba(0,0,0,0.8)', color: 'white', px: 1, py: 0.5, borderRadius: 1, fontSize: '0.75rem', fontWeight: 600 }}>
                        {video.duration || 'Bilinmiyor'}
                      </Box>
                    </Box>
                    <Box sx={{ p: 2, flex: 1, display: 'flex', flexDirection: 'column' }}>
                      <Typography variant="subtitle2" fontWeight={700} sx={{ mb: 1, display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                        {video.title}
                      </Typography>
                      <Typography variant="caption" color="text.secondary" sx={{ mt: 'auto', display: 'flex', justifyContent: 'space-between' }}>
                        <span>{video.channel}</span>
                        <span>{video.difficulty || 'Orta'}</span>
                      </Typography>
                    </Box>
                  </GlassCard>
                </Grid>
              ))}
            </React.Fragment>
          ))}
        </Grid>
      ) : (
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <PlayCircleFilled sx={{ fontSize: 64, color: 'text.secondary', mb: 2, opacity: 0.5 }} />
          <Typography variant="h6" color="text.secondary">Önerilen video bulunamadı</Typography>
        </Box>
      )}
    </Box>
  );
};
