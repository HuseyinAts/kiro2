/**
 * Video Analytics Card Component
 *
 * Displays video quality analytics and statistics
 * Extracted from LearningPathPage.tsx
 */

import { Card, CardContent, Box, Typography, Divider, Chip } from '@mui/material';
import * as React from 'react';
import {  useMemo  } from 'react';

import { VideoResponse } from '../../../api';

export interface VideoAnalyticsCardProps {
  videos: VideoResponse[]
}

/**
 * Calculate average score from videos
 */
const calculateAverageScore = (
  videos: VideoResponse[],
  scoreKey: 'turkish_score' | 'relevance_score' | 'quality_score' | 'final_score',
): number => {
  if (videos.length === 0) {return 0;}
  const sum = videos.reduce((acc, v) => acc + (v.scores?.[scoreKey] || 0), 0);
  return Math.round((sum / videos.length) * 100);
};

/**
 * Card showing video quality analytics
 *
 * Displays average scores and feature statistics
 *
 * Performance: Memoized with React.memo and useMemo for expensive calculations
 */
export const VideoAnalyticsCard = React.memo<VideoAnalyticsCardProps>(({
  videos,
}) => {
  const hasVideos = videos.length > 0;

  // Memoize expensive score calculations - hooks must be called before any early returns
  const scores = useMemo(
    () => hasVideos ? ({
      turkish: calculateAverageScore(videos, 'turkish_score'),
      relevance: calculateAverageScore(videos, 'relevance_score'),
      quality: calculateAverageScore(videos, 'quality_score'),
      final: calculateAverageScore(videos, 'final_score'),
    }) : { turkish: 0, relevance: 0, quality: 0, final: 0 },
    [videos, hasVideos],
  );

  // Memoize feature counts
  const counts = useMemo(
    () => hasVideos ? ({
      turkish: videos.filter(v => v.is_turkish).length,
      accessible: videos.filter(v => v.is_accessible).length,
      caption: videos.filter(v => v.caption_available).length,
      hd: videos.filter(v => v.definition === 'hd').length,
    }) : { turkish: 0, accessible: 0, caption: 0, hd: 0 },
    [videos, hasVideos],
  );

  const { turkish: turkishScore, relevance: relevanceScore, quality: qualityScore, final: finalScore } = scores;
  const { turkish: turkishCount, accessible: accessibleCount, caption: captionCount, hd: hdCount } = counts;

  if (!hasVideos) {return null;}

  return (
    <Card
      elevation={2}
      sx={{
        mb: 3,
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        color: 'white',
      }}
    >
      <CardContent>
        <Typography variant="h6" fontWeight="bold" gutterBottom>
          📊 Video Kalite Analizi
        </Typography>

        <Box className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-2">
          <Box
            sx={{
              textAlign: 'center',
              p: 2,
              backgroundColor: 'rgba(255,255,255,0.2)',
              borderRadius: 2,
            }}
          >
            <Typography variant="h4" fontWeight="bold">
              {turkishScore}%
            </Typography>
            <Typography variant="caption">Türkçe Skoru</Typography>
            <Typography
              variant="caption"
              display="block"
              sx={{ opacity: 0.8, mt: 0.5 }}
            >
              Ortalama
            </Typography>
          </Box>

          <Box
            sx={{
              textAlign: 'center',
              p: 2,
              backgroundColor: 'rgba(255,255,255,0.2)',
              borderRadius: 2,
            }}
          >
            <Typography variant="h4" fontWeight="bold">
              {relevanceScore}%
            </Typography>
            <Typography variant="caption">Konu Uygunluğu</Typography>
            <Typography
              variant="caption"
              display="block"
              sx={{ opacity: 0.8, mt: 0.5 }}
            >
              Ortalama
            </Typography>
          </Box>

          <Box
            sx={{
              textAlign: 'center',
              p: 2,
              backgroundColor: 'rgba(255,255,255,0.2)',
              borderRadius: 2,
            }}
          >
            <Typography variant="h4" fontWeight="bold">
              {qualityScore}%
            </Typography>
            <Typography variant="caption">Video Kalitesi</Typography>
            <Typography
              variant="caption"
              display="block"
              sx={{ opacity: 0.8, mt: 0.5 }}
            >
              Ortalama
            </Typography>
          </Box>

          <Box
            sx={{
              textAlign: 'center',
              p: 2,
              backgroundColor: 'rgba(255,255,255,0.2)',
              borderRadius: 2,
            }}
          >
            <Typography variant="h4" fontWeight="bold">
              {finalScore}%
            </Typography>
            <Typography variant="caption">Final Skor</Typography>
            <Typography
              variant="caption"
              display="block"
              sx={{ opacity: 0.8, mt: 0.5 }}
            >
              Ortalama
            </Typography>
          </Box>
        </Box>

        <Divider sx={{ my: 2, borderColor: 'rgba(255,255,255,0.3)' }} />

        <Box className="flex gap-2 flex-wrap">
          <Chip
            label={`✓ ${turkishCount} Türkçe Onaylı`}
            size="small"
            sx={{ backgroundColor: 'rgba(255,255,255,0.3)', color: 'white' }}
          />
          <Chip
            label={`✓ ${accessibleCount} Erişilebilir`}
            size="small"
            sx={{ backgroundColor: 'rgba(255,255,255,0.3)', color: 'white' }}
          />
          <Chip
            label={`✓ ${captionCount} Altyazılı`}
            size="small"
            sx={{ backgroundColor: 'rgba(255,255,255,0.3)', color: 'white' }}
          />
          <Chip
            label={`✓ ${hdCount} HD Kalite`}
            size="small"
            sx={{ backgroundColor: 'rgba(255,255,255,0.3)', color: 'white' }}
          />
        </Box>

        <Typography
          variant="caption"
          sx={{ mt: 2, display: 'block', opacity: 0.9 }}
        >
          Tüm videolar Türkçe içerik filtresi, konu uygunluğu ve erişilebilirlik
          kontrolünden geçirildi
        </Typography>
      </CardContent>
    </Card>
  );
});

// Display name for React DevTools
VideoAnalyticsCard.displayName = 'VideoAnalyticsCard';

export default VideoAnalyticsCard;
