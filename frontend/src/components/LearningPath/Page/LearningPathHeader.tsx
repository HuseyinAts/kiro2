/**
 * Learning Path Header Component
 *
 * Displays page header with title and refresh button
 * Extracted from LearningPathPage.tsx
 */

import React from 'react'
import { Box, Typography, Button } from '@mui/material'
import { Refresh } from '@mui/icons-material'

export interface LearningPathHeaderProps {
  onRefresh: () => void
}

/**
 * Header component for learning path page
 *
 * Shows title, description, and refresh button
 */
export const LearningPathHeader: React.FC<LearningPathHeaderProps> = ({ onRefresh }) => {
  return (
    <Box sx={{ mb: 4 }}>
      <Box className="flex items-center justify-between mb-2">
        <Typography variant="h4" component="h1" fontWeight="bold">
          🎯 Öğrenme Yolunuz
        </Typography>
        <Button variant="outlined" startIcon={<Refresh />} onClick={onRefresh}>
          Yenile
        </Button>
      </Box>

      <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
        Kişiselleştirilmiş öğrenme yolunuz ve size özel kaynaklar
      </Typography>
    </Box>
  )
}

export default LearningPathHeader
