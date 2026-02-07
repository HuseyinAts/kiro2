/**
 * PathProgressTab Component
 * Progress tracking tab for learning path
 */

import {
  Box,
  Typography,
  Paper,
  Chip,
  Alert,
  CircularProgress,
} from '@mui/material';
import * as React from 'react';

import learningPathService from '../../services/learningPathService';

import { PathNodeData } from './PathNode';

interface PathProgressTabProps {
  pathNodes: PathNodeData[];
}

export const PathProgressTab: React.FC<PathProgressTabProps> = ({ pathNodes }) => {
  const hasPath = learningPathService.getCurrentPath();

  if (!hasPath) {
    return (
      <Box sx={{ px: 2 }}>
        <Alert severity="info">
          Henüz öğrenme yolu oluşturulmamış. Lütfen &quot;Yol Haritası&quot; sekmesinden başlayın.
        </Alert>
      </Box>
    );
  }

  const completedCount = pathNodes.filter(n => n.status === 'completed').length;
  const currentCount = pathNodes.filter(n => n.status === 'current').length;
  const availableCount = pathNodes.filter(n => n.status === 'available').length;
  const completionPercentage = pathNodes.length > 0 ? (completedCount / pathNodes.length) * 100 : 0;

  const totalDuration = pathNodes.reduce((sum, node) => {
    const match = node.estimatedTime?.match(/(\d+)/);
    return sum + (match ? parseInt(match[1]) : 0);
  }, 0);

  const moduleTitles = ['Temel Kavramlar', 'Orta Seviye', 'İleri Seviye'];

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
            label={`${Math.round(completionPercentage)}%`}
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
                width: `${completionPercentage}%`,
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
              {totalDuration} dk
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
        const moduleNodes = pathNodes.filter((node) => node.id.startsWith(moduleId));
        const completedInModule = moduleNodes.filter((n) => n.status === 'completed').length;
        const moduleProgress = moduleNodes.length > 0 ? (completedInModule / moduleNodes.length) * 100 : 0;

        return (
          <Paper key={moduleId} elevation={1} sx={{ p: 3, mb: 2 }}>
            <Box className="flex items-center justify-between mb-2">
              <Box>
                <Typography variant="h6" fontWeight="bold">
                  Modül {moduleIndex + 1}: {moduleTitles[moduleIndex]}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {completedInModule} / {moduleNodes.length} Konu Tamamlandı
                </Typography>
              </Box>
              <Chip
                label={`${Math.round(moduleProgress)}%`}
                color={moduleProgress === 100 ? 'success' : moduleProgress > 0 ? 'primary' : 'default'}
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
                mb: 2,
              }}
            >
              <Box
                sx={{
                  width: `${moduleProgress}%`,
                  height: '100%',
                  backgroundColor: moduleProgress === 100 ? '#4caf50' : '#2196f3',
                  transition: 'width 0.5s ease',
                }}
              />
            </Box>

            {/* Topic List */}
            <Box className="flex flex-col gap-2">
              {moduleNodes.map((node) => (
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
                        : 'divider',
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
                      <Typography variant="body2" fontWeight={node.status === 'current' ? 'bold' : 'normal'}>
                        {node.title}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {node.estimatedTime}
                      </Typography>
                    </Box>
                  </Box>
                  <Box className="flex items-center gap-2">
                    {node.status === 'completed' && <Chip label="Tamamlandı" size="small" color="success" />}
                    {node.status === 'current' && <Chip label={`${node.progress}%`} size="small" color="primary" />}
                    {(node.resources ?? 0) > 0 && <Chip label={`${node.resources} Kaynak`} size="small" variant="outlined" />}
                  </Box>
                </Box>
              ))}
            </Box>
          </Paper>
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
              {Math.round(completionPercentage)}%
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Tamamlanma Oranı
            </Typography>
          </Box>
        </Box>
      </Paper>
    </Box>
  );
};

export default PathProgressTab;
