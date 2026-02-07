/**
 * Progress Tracking Tab Component
 *
 * Displays overall and module-based progress tracking
 * Extracted from LearningPathPage.tsx
 */

import { Box, Typography, Paper, Chip, Alert } from '@mui/material';
import * as React from 'react';
import {  useMemo  } from 'react';

import {
  calculateOverallProgress,
  calculateTotalTime,
} from '../../../../utils/learningPathHelpers';
import { PathNodeData } from '../../PathNode';
import { ModuleProgressCard } from '../ModuleProgressCard';

export interface ProgressTrackingTabProps {
  pathNodes: PathNodeData[]
  hasPath: boolean
}

/**
 * Tab component for progress tracking
 *
 * Shows overall progress, module progress, and detailed statistics
 *
 * Performance: Memoized with React.memo to prevent unnecessary re-renders
 */
export const ProgressTrackingTab = React.memo<ProgressTrackingTabProps>(({
  pathNodes,
  hasPath,
}) => {
  // Memoize expensive calculations - hooks must be called before any early returns
  const overallProgress = useMemo(() => hasPath ? calculateOverallProgress(pathNodes) : 0, [pathNodes, hasPath]);
  const totalTime = useMemo(() => hasPath ? calculateTotalTime(pathNodes) : 0, [pathNodes, hasPath]);

  // Memoize filtered counts
  const counts = useMemo(
    () => hasPath ? ({
      completed: pathNodes.filter(n => n.status === 'completed').length,
      current: pathNodes.filter(n => n.status === 'current').length,
      available: pathNodes.filter(n => n.status === 'available').length,
    }) : { completed: 0, current: 0, available: 0 },
    [pathNodes, hasPath],
  );

  const { completed: completedCount, current: currentCount, available: availableCount } = counts;

  if (!hasPath) {
    return (
      <Box sx={{ px: 2 }}>
        <Alert severity="info">
          Henüz öğrenme yolu oluşturulmamış. Lütfen &quot;Yol Haritası&quot; sekmesinden
          başlayın.
        </Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ px: 2 }}>
      <Typography variant="h5" fontWeight="bold" gutterBottom>
        📊 İlerleme Takibi
      </Typography>

      {/* Overall Progress Card */}
      <Paper
        elevation={2}
        sx={{
          p: 3,
          mb: 3,
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
        }}
      >
        <Box className="flex items-center justify-between mb-2">
          <Typography variant="h6" fontWeight="bold">
            Genel İlerlemeniz
          </Typography>
          <Chip
            label={`${overallProgress}%`}
            sx={{
              backgroundColor: 'rgba(255,255,255,0.3)',
              color: 'white',
              fontWeight: 'bold',
              fontSize: '1rem',
            }}
          />
        </Box>

        <Box sx={{ mt: 2, mb: 1 }}>
          <Box className="flex justify-between mb-1">
            <Typography variant="body2">
              {completedCount} / {pathNodes.length} Konu Tamamlandı
            </Typography>
            <Typography variant="body2">{currentCount} Devam Ediyor</Typography>
          </Box>
          <Box
            sx={{
              width: '100%',
              height: 12,
              backgroundColor: 'rgba(255,255,255,0.3)',
              borderRadius: 2,
              overflow: 'hidden',
            }}
          >
            <Box
              sx={{
                width: `${overallProgress}%`,
                height: '100%',
                backgroundColor: 'white',
                transition: 'width 0.5s ease',
              }}
            />
          </Box>
        </Box>

        <Box className="flex gap-4 mt-3">
          <Box>
            <Typography variant="caption" sx={{ opacity: 0.8 }}>
              Toplam Modül
            </Typography>
            <Typography variant="h5" fontWeight="bold">
              3
            </Typography>
          </Box>
          <Box>
            <Typography variant="caption" sx={{ opacity: 0.8 }}>
              Toplam Konu
            </Typography>
            <Typography variant="h5" fontWeight="bold">
              {pathNodes.length}
            </Typography>
          </Box>
          <Box>
            <Typography variant="caption" sx={{ opacity: 0.8 }}>
              Tahmini Süre
            </Typography>
            <Typography variant="h5" fontWeight="bold">
              {totalTime} dk
            </Typography>
          </Box>
        </Box>
      </Paper>

      {/* Module Progress */}
      <Typography variant="h6" fontWeight="bold" gutterBottom sx={{ mt: 4 }}>
        Modül Bazında İlerleme
      </Typography>

      {Array.from({ length: 3 }, (_, moduleIndex) => {
        const moduleId = `MOD${moduleIndex + 1}`;
        const moduleNodes = pathNodes.filter(node => node.id.startsWith(moduleId));

        return (
          <ModuleProgressCard
            key={moduleId}
            moduleIndex={moduleIndex}
            moduleNodes={moduleNodes}
          />
        );
      })}

      {/* Detailed Statistics */}
      <Paper elevation={2} sx={{ p: 3, mt: 3, backgroundColor: '#f5f5f5' }}>
        <Typography variant="h6" fontWeight="bold" gutterBottom>
          📈 Detaylı İstatistikler
        </Typography>
        <Box className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-3">
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="h4" color="success.main" fontWeight="bold">
              {completedCount}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Tamamlanan Konular
            </Typography>
          </Box>
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="h4" color="primary.main" fontWeight="bold">
              {currentCount}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Devam Eden
            </Typography>
          </Box>
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="h4" color="text.secondary" fontWeight="bold">
              {availableCount}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Bekleyen
            </Typography>
          </Box>
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="h4" color="warning.main" fontWeight="bold">
              {overallProgress}%
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Tamamlanma Oranı
            </Typography>
          </Box>
        </Box>
      </Paper>
    </Box>
  );
});

// Display name for React DevTools
ProgressTrackingTab.displayName = 'ProgressTrackingTab';

export default ProgressTrackingTab;
