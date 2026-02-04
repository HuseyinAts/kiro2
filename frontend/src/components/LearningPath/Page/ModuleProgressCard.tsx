/**
 * Module Progress Card Component
 *
 * Displays progress for a single module
 * Extracted from LearningPathPage.tsx
 */

import React from 'react'
import { Paper, Box, Typography, Chip, CircularProgress } from '@mui/material'
import { PathNodeData } from '../PathNode'
import {
  calculateModuleProgress,
  getModuleTitle
} from '../../../utils/learningPathHelpers'

export interface ModuleProgressCardProps {
  moduleIndex: number
  moduleNodes: PathNodeData[]
}

/**
 * Card showing progress for a specific module
 *
 * Displays module title, progress bar, and topic list
 *
 * Performance: Memoized with React.memo since it's rendered in a list
 */
export const ModuleProgressCard = React.memo<ModuleProgressCardProps>(({
  moduleIndex,
  moduleNodes
}) => {
  const completedInModule = moduleNodes.filter(n => n.status === 'completed').length
  const moduleProgress = calculateModuleProgress(moduleNodes)
  const moduleTitle = getModuleTitle(moduleIndex)

  return (
    <Paper elevation={1} sx={{ p: 3, mb: 2 }}>
      <Box className="flex items-center justify-between mb-2">
        <Box>
          <Typography variant="h6" fontWeight="bold">
            Modül {moduleIndex + 1}: {moduleTitle}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {completedInModule} / {moduleNodes.length} Konu Tamamlandı
          </Typography>
        </Box>
        <Chip
          label={`${Math.round(moduleProgress)}%`}
          color={
            moduleProgress === 100
              ? 'success'
              : moduleProgress > 0
              ? 'primary'
              : 'default'
          }
          sx={{ fontWeight: 'bold' }}
        />
      </Box>

      <Box
        sx={{
          width: '100%',
          height: 8,
          backgroundColor: 'rgba(0,0,0,0.1)',
          borderRadius: 2,
          overflow: 'hidden',
          mb: 2
        }}
      >
        <Box
          sx={{
            width: `${moduleProgress}%`,
            height: '100%',
            backgroundColor: moduleProgress === 100 ? '#4caf50' : '#2196f3',
            transition: 'width 0.5s ease'
          }}
        />
      </Box>

      {/* Topic List */}
      <Box className="flex flex-col gap-2">
        {moduleNodes.map(node => (
          <Box
            key={node.id}
            className="flex items-center justify-between p-2 rounded"
            sx={{
              backgroundColor:
                node.status === 'completed'
                  ? 'rgba(76, 175, 80, 0.1)'
                  : node.status === 'current'
                  ? 'rgba(33, 150, 243, 0.1)'
                  : 'rgba(0,0,0,0.02)',
              border: '1px solid',
              borderColor:
                node.status === 'completed'
                  ? 'success.light'
                  : node.status === 'current'
                  ? 'primary.light'
                  : 'divider'
            }}
          >
            <Box className="flex items-center gap-2">
              {node.status === 'completed' ? (
                <Box sx={{ color: 'success.main' }}>✓</Box>
              ) : node.status === 'current' ? (
                <CircularProgress size={20} thickness={5} />
              ) : (
                <Box sx={{ color: 'text.disabled' }}>○</Box>
              )}
              <Box>
                <Typography
                  variant="body2"
                  fontWeight={node.status === 'current' ? 'bold' : 'normal'}
                >
                  {node.title}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {node.estimatedTime}
                </Typography>
              </Box>
            </Box>
            <Box className="flex items-center gap-2">
              {node.status === 'completed' && (
                <Chip label="Tamamlandı" size="small" color="success" />
              )}
              {node.status === 'current' && (
                <Chip label={`${node.progress}%`} size="small" color="primary" />
              )}
              {node.resources > 0 && (
                <Chip
                  label={`${node.resources} Kaynak`}
                  size="small"
                  variant="outlined"
                />
              )}
            </Box>
          </Box>
        ))}
      </Box>
    </Paper>
  )
})

// Display name for React DevTools
ModuleProgressCard.displayName = 'ModuleProgressCard'

export default ModuleProgressCard
