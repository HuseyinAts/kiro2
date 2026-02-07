/**
 * PathVideoResourcesTab Component
 * Video resources tab with loading states and analytics
 */

import { VideoLibrary, Refresh } from '@mui/icons-material';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  Chip,
  Divider,
  Alert,
} from '@mui/material';
import * as React from 'react';

import { VideoResponse } from '../../api';
import { VideoLoadingState } from '../../services/VideoLoadingManager';
import { VideoLoadingUI } from '../VideoLoadingUI';

import { VideoResourceGrid } from './VideoResourceGrid';

interface PathVideoResourcesTabProps {
  videos: VideoResponse[];
  videosLoading: boolean;
  videosError: string | null;
  videoLoadingState: VideoLoadingState;
  loadingSubjects: string[];
  onRetryVideos: () => void;
  onShowFallback: () => void;
  onCancelVideoLoad: () => void;
  onVideoPlay: (video: VideoResponse) => void;
}

export const PathVideoResourcesTab: React.FC<PathVideoResourcesTabProps> = ({
  videos,
  videosLoading,
  videosError: _videosError,
  videoLoadingState,
  loadingSubjects,
  onRetryVideos,
  onShowFallback,
  onCancelVideoLoad,
  onVideoPlay,
}) => {
  return (
    <Box sx={{ px: 2 }}>
      {/* Header */}
      <Box className="flex items-center justify-between mb-3">
        <Box className="flex items-center gap-2">
          <VideoLibrary color="primary" />
          <Typography variant="h5" fontWeight="bold">
            📹 Size Özel Video Kaynakları
          </Typography>
        </Box>

        {!videosLoading && videos.length > 0 && (
          <Button
            variant="outlined"
            size="small"
            startIcon={<Refresh />}
            onClick={onRetryVideos}
          >
            Yenile
          </Button>
        )}
      </Box>

      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
        Öğrenme stilinize ve seviyenize uygun, kaliteli eğitim videoları
      </Typography>

      {/* Video Analytics Card */}
      {videos.length > 0 && videoLoadingState.status === 'success' && (
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
                  {Math.round(
                    (videos.reduce((sum, v) => sum + (v.scores?.turkish_score || 0), 0) / videos.length) * 100,
                  )}
                  %
                </Typography>
                <Typography variant="caption">Türkçe Skoru</Typography>
                <Typography variant="caption" display="block" sx={{ opacity: 0.8, mt: 0.5 }}>
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
                  {Math.round(
                    (videos.reduce((sum, v) => sum + (v.scores?.relevance_score || 0), 0) / videos.length) * 100,
                  )}
                  %
                </Typography>
                <Typography variant="caption">Konu Uygunluğu</Typography>
                <Typography variant="caption" display="block" sx={{ opacity: 0.8, mt: 0.5 }}>
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
                  {Math.round(
                    (videos.reduce((sum, v) => sum + (v.scores?.quality_score || 0), 0) / videos.length) * 100,
                  )}
                  %
                </Typography>
                <Typography variant="caption">Video Kalitesi</Typography>
                <Typography variant="caption" display="block" sx={{ opacity: 0.8, mt: 0.5 }}>
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
                  {Math.round(
                    (videos.reduce((sum, v) => sum + (v.scores?.final_score || 0), 0) / videos.length) * 100,
                  )}
                  %
                </Typography>
                <Typography variant="caption">Final Skor</Typography>
                <Typography variant="caption" display="block" sx={{ opacity: 0.8, mt: 0.5 }}>
                  Ortalama
                </Typography>
              </Box>
            </Box>

            <Divider sx={{ my: 2, borderColor: 'rgba(255,255,255,0.3)' }} />

            <Box className="flex gap-2 flex-wrap">
              <Chip
                label={`✓ ${videos.filter((v) => v.is_turkish).length} Türkçe Onaylı`}
                size="small"
                sx={{ backgroundColor: 'rgba(255,255,255,0.3)', color: 'white' }}
              />
              <Chip
                label={`✓ ${videos.filter((v) => v.is_accessible).length} Erişilebilir`}
                size="small"
                sx={{ backgroundColor: 'rgba(255,255,255,0.3)', color: 'white' }}
              />
              <Chip
                label={`✓ ${videos.filter((v) => v.caption_available).length} Altyazılı`}
                size="small"
                sx={{ backgroundColor: 'rgba(255,255,255,0.3)', color: 'white' }}
              />
              <Chip
                label={`✓ ${videos.filter((v) => v.definition === 'hd').length} HD Kalite`}
                size="small"
                sx={{ backgroundColor: 'rgba(255,255,255,0.3)', color: 'white' }}
              />
            </Box>

            <Typography variant="caption" sx={{ mt: 2, display: 'block', opacity: 0.9 }}>
              Tüm videolar Türkçe içerik filtresi, konu uygunluğu ve erişilebilirlik kontrolünden geçirildi
            </Typography>
          </CardContent>
        </Card>
      )}

      {/* VideoLoadingUI Component */}
      <VideoLoadingUI
        state={videoLoadingState}
        onRetry={onRetryVideos}
        onShowFallback={onShowFallback}
        onCancel={onCancelVideoLoad}
        subjects={loadingSubjects}
      />

      {/* Show video grid only when videos are successfully loaded */}
      {videoLoadingState.status === 'success' && videos.length > 0 && (
        <VideoResourceGrid videos={videos} loading={false} error={undefined} onVideoPlay={onVideoPlay} />
      )}

      {/* Show fallback message if no videos after success */}
      {videoLoadingState.status === 'success' && videos.length === 0 && (
        <Alert severity="info" sx={{ mt: 3 }}>
          Şu anda size özel video bulunamadı. Lütfen daha sonra tekrar deneyin.
        </Alert>
      )}
    </Box>
  );
};

export default PathVideoResourcesTab;
