/**
 * Video Resources Tab Component
 *
 * Displays personalized video resources
 * Extracted from LearningPathPage.tsx
 */

import React from 'react'
import { Box, Typography, Button, Alert } from '@mui/material'
import { VideoLibrary, Refresh } from '@mui/icons-material'
import { VideoResponse } from '../../../../api'
import { VideoLoadingState } from '../../../../services/VideoLoadingManager'
import { VideoLoadingUI } from '../../../VideoLoadingUI'
import { VideoResourceGrid } from '../../VideoResourceGrid'
import { VideoAnalyticsCard } from '../VideoAnalyticsCard'

export interface VideoResourcesTabProps {
  videos: VideoResponse[]
  videoLoadingState: VideoLoadingState
  loadingSubjects: string[]
  videosLoading: boolean
  onRetry: () => void
  onShowFallback: () => void
  onCancel: () => void
  onVideoPlay: (video: VideoResponse) => void
}

/**
 * Tab component for video resources
 *
 * Shows video analytics, loading UI, and video grid
 *
 * Performance: Memoized with React.memo to prevent unnecessary re-renders
 */
export const VideoResourcesTab = React.memo<VideoResourcesTabProps>(({
  videos,
  videoLoadingState,
  loadingSubjects,
  videosLoading,
  onRetry,
  onShowFallback,
  onCancel,
  onVideoPlay
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
            onClick={onRetry}
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
        <VideoAnalyticsCard videos={videos} />
      )}

      {/* VideoLoadingUI Component - Handles loading, success, error states */}
      <VideoLoadingUI
        state={videoLoadingState}
        onRetry={onRetry}
        onShowFallback={onShowFallback}
        onCancel={onCancel}
        subjects={loadingSubjects}
      />

      {/* Show video grid only when videos are successfully loaded */}
      {videoLoadingState.status === 'success' && videos.length > 0 && (
        <VideoResourceGrid
          videos={videos}
          loading={false}
          error={null}
          onVideoPlay={onVideoPlay}
        />
      )}

      {/* Show fallback message if no videos after success */}
      {videoLoadingState.status === 'success' && videos.length === 0 && (
        <Alert severity="info" sx={{ mt: 3 }}>
          Şu anda size özel video bulunamadı. Lütfen daha sonra tekrar deneyin.
        </Alert>
      )}
    </Box>
  )
})

// Display name for React DevTools
VideoResourcesTab.displayName = 'VideoResourcesTab'

export default VideoResourcesTab
