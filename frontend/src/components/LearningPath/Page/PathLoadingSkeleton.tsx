/**
 * Path Loading Skeleton Component
 *
 * Skeleton loader for LearningPathPage during lazy loading
 * Provides better UX than a blank screen or spinner
 */

import React from 'react'
import { Container, Paper, Box, Skeleton } from '@mui/material'

/**
 * Skeleton loader that mimics the LearningPathPage structure
 *
 * Shows placeholder UI while the actual component loads
 */
export const PathLoadingSkeleton: React.FC = () => {
  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header Skeleton */}
      <Box sx={{ mb: 3 }}>
        <Skeleton variant="text" width="40%" height={48} sx={{ mb: 1 }} />
        <Skeleton variant="text" width="60%" height={24} />
      </Box>

      {/* Learning Style Badge Skeleton */}
      <Paper elevation={2} sx={{ p: 2, mb: 3 }}>
        <Skeleton variant="text" width="30%" height={32} sx={{ mb: 2 }} />
        <Box className="flex gap-2">
          <Skeleton variant="rectangular" width={100} height={32} sx={{ borderRadius: 2 }} />
          <Skeleton variant="rectangular" width={120} height={32} sx={{ borderRadius: 2 }} />
          <Skeleton variant="rectangular" width={110} height={32} sx={{ borderRadius: 2 }} />
        </Box>
      </Paper>

      {/* Tabs Skeleton */}
      <Paper elevation={2}>
        {/* Tab Headers */}
        <Box sx={{ borderBottom: 1, borderColor: 'divider', p: 2 }}>
          <Box className="flex gap-4">
            <Skeleton variant="rectangular" width={150} height={40} sx={{ borderRadius: 1 }} />
            <Skeleton variant="rectangular" width={200} height={40} sx={{ borderRadius: 1 }} />
            <Skeleton variant="rectangular" width={120} height={40} sx={{ borderRadius: 1 }} />
          </Box>
        </Box>

        {/* Tab Content Skeleton */}
        <Box sx={{ p: 3 }}>
          {/* Grid of cards */}
          <Box className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <Paper key={i} elevation={1} sx={{ p: 2 }}>
                <Skeleton variant="circular" width={48} height={48} sx={{ mb: 2 }} />
                <Skeleton variant="text" width="80%" height={24} sx={{ mb: 1 }} />
                <Skeleton variant="text" width="60%" height={20} sx={{ mb: 2 }} />
                <Skeleton variant="rectangular" width="100%" height={100} />
              </Paper>
            ))}
          </Box>
        </Box>
      </Paper>
    </Container>
  )
}

// Display name for React DevTools
PathLoadingSkeleton.displayName = 'PathLoadingSkeleton'

export default PathLoadingSkeleton
