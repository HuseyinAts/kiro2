/**
 * Path Loading State Component
 *
 * Displays loading state for learning path
 * Extracted from LearningPathPage.tsx
 */

import React from 'react'
import { Container, Box, CircularProgress, Typography } from '@mui/material'

/**
 * Loading state component for learning path
 *
 * Shows spinner and loading messages
 */
export const PathLoadingState: React.FC = () => {
  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Box
        className="flex flex-col items-center justify-center"
        sx={{ minHeight: '60vh' }}
      >
        <CircularProgress size={60} thickness={4} />
        <Typography variant="h6" sx={{ mt: 3 }} color="text.secondary">
          Öğrenme yolunuz hazırlanıyor...
        </Typography>
        <Typography variant="body2" sx={{ mt: 1 }} color="text.secondary">
          Kişiselleştirilmiş içerikler yükleniyor
        </Typography>
      </Box>
    </Container>
  )
}

export default PathLoadingState
