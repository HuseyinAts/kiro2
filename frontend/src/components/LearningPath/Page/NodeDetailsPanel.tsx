/**
 * Node Details Panel Component
 *
 * Displays detailed information for a selected node
 * Extracted from LearningPathPage.tsx
 */

import {
  Paper,
  Box,
  Typography,
  Button,
  Divider,
  Chip,
  Alert,
  CircularProgress,
} from '@mui/material';
import { VideoLibrary, OpenInNew, SmartToy, Science } from '@mui/icons-material';
import * as React from 'react';

import type { VideoResponse } from '../../../api';
import { formatDifficulty } from '../../../utils/learningPathHelpers';
import { PathNodeData } from '../PathNode';
import { NodeChatPanel } from '../NodeChatPanel';

export interface NodeDetailsPanelProps {
  node: PathNodeData
  onClose: () => void
  onStartQuiz?: (node: PathNodeData) => void
  onStartProductiveFailure?: (node: PathNodeData) => void
  resources?: VideoResponse[]
  resourcesLoading?: boolean
<<<<<<< Updated upstream
  quizLoading?: boolean
=======
>>>>>>> Stashed changes
}

/**
 * Panel showing detailed information about a path node
 *
 * Displays node metadata, progress, quiz info, and resources
 */
export const NodeDetailsPanel: React.FC<NodeDetailsPanelProps> = ({
  node,
  onClose,
  onStartQuiz,
  onStartProductiveFailure,
  resources = [],
  resourcesLoading = false,
<<<<<<< Updated upstream
  quizLoading = false,
=======
>>>>>>> Stashed changes
}) => {
  const [showChat, setShowChat] = React.useState(false);

  return (
    <Paper elevation={3} sx={{ p: 3, mb: 3, position: 'relative' }}>
      <Button
        size="small"
        onClick={onClose}
        sx={{ position: 'absolute', top: 16, right: 16 }}
      >
        ✕ Kapat
      </Button>

      <Box className="flex items-start gap-3 mb-3">
        <Box
          sx={{
            width: 48,
            height: 48,
            borderRadius: 2,
            backgroundColor:
              node.status === 'completed'
                ? 'success.light'
                : node.status === 'current'
                ? 'primary.light'
                : 'grey.300',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '1.5rem',
          }}
        >
          📚
        </Box>
        <Box flex={1}>
          <Typography variant="h5" fontWeight="bold" gutterBottom>
            {node.title}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {node.description}
          </Typography>
        </Box>
      </Box>

      <Divider sx={{ my: 2 }} />

      <Box className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-3">
        <Box
          sx={{
            textAlign: 'center',
            p: 2,
            backgroundColor: 'grey.100',
            borderRadius: 2,
          }}
        >
          <Typography variant="caption" color="text.secondary">
            Süre
          </Typography>
          <Typography variant="h6" fontWeight="bold">
            {node.estimatedTime}
          </Typography>
        </Box>
        <Box
          sx={{
            textAlign: 'center',
            p: 2,
            backgroundColor: 'grey.100',
            borderRadius: 2,
          }}
        >
          <Typography variant="caption" color="text.secondary">
            Zorluk
          </Typography>
          <Typography variant="h6" fontWeight="bold">
            {formatDifficulty(node.difficulty)}
          </Typography>
        </Box>
        <Box
          sx={{
            textAlign: 'center',
            p: 2,
            backgroundColor: 'grey.100',
            borderRadius: 2,
          }}
        >
          <Typography variant="caption" color="text.secondary">
            İlerleme
          </Typography>
          <Typography variant="h6" fontWeight="bold">
            {node.progress}%
          </Typography>
        </Box>
        <Box
          sx={{
            textAlign: 'center',
            p: 2,
            backgroundColor: 'grey.100',
            borderRadius: 2,
          }}
        >
          <Typography variant="caption" color="text.secondary">
            Kaynaklar
          </Typography>
          <Typography variant="h6" fontWeight="bold">
            {node.resources || 0}
          </Typography>
        </Box>
      </Box>

      {/* Theta Gauge + ZPD Badge */}
      {node.theta !== undefined && (
        <Box sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 2 }}>
          <Box sx={{ flex: 1 }}>
            <Typography variant="caption" color="text.secondary">
              Yetenek Skoru (theta)
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Box
                sx={{
                  flex: 1,
                  height: 8,
                  borderRadius: 4,
                  backgroundColor: 'grey.200',
                  position: 'relative',
                  overflow: 'hidden',
                }}
              >
                <Box
                  sx={{
                    position: 'absolute',
                    left: `${Math.max(0, Math.min(100, ((node.theta + 4) / 8) * 100))}%`,
                    top: 0,
                    width: 12,
                    height: 8,
                    borderRadius: 4,
                    backgroundColor:
                      node.zpd_zone === 'MASTERED'
                        ? 'success.main'
                        : node.zpd_zone === 'FRUSTRATION'
                          ? 'error.main'
                          : 'warning.main',
                    transform: 'translateX(-50%)',
                  }}
                />
              </Box>
              <Typography variant="body2" fontWeight="bold">
                {node.theta.toFixed(2)}
              </Typography>
            </Box>
            {node.theta_se !== undefined && (
              <Typography variant="caption" color="text.secondary">
                Guven: {((1 - Math.min(1, node.theta_se)) * 100).toFixed(0)}%
              </Typography>
            )}
          </Box>
          {node.zpd_zone && (
            <Chip
              label={
                node.zpd_zone === 'MASTERED'
                  ? 'Uzman'
                  : node.zpd_zone === 'ZPD_ACTIVE'
                    ? 'ZPD Aktif'
                    : 'Destek Gerekli'
              }
              color={
                node.zpd_zone === 'MASTERED'
                  ? 'success'
                  : node.zpd_zone === 'FRUSTRATION'
                    ? 'error'
                    : 'warning'
              }
              size="small"
              variant="filled"
            />
          )}
        </Box>
      )}

      {node.quiz && (
        <Alert severity="info" sx={{ mb: 2 }}>
          <Typography variant="body2" fontWeight="bold" gutterBottom>
            📝 Quiz Bilgisi
          </Typography>
          <Box className="flex gap-4 mb-1">
            <Typography variant="body2">
              <strong>Soru Sayısı:</strong> {node.quiz.question_count}
            </Typography>
            <Typography variant="body2">
              <strong>Geçme Notu:</strong> {node.quiz.passing_score}%
            </Typography>
          </Box>
          {node.status !== 'completed' && (
            <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
              {onStartQuiz && (
                <Button
                  variant="contained"
                  color="primary"
                  size="small"
                  onClick={() => onStartQuiz(node)}
<<<<<<< Updated upstream
                  disabled={quizLoading}
                >
                  {quizLoading ? 'Yükleniyor...' : 'Quiz Başlat'}
=======
                >
                  Quiz Başlat
>>>>>>> Stashed changes
                </Button>
              )}
              {onStartProductiveFailure && (
                <Button
                  variant="outlined"
                  color="secondary"
                  size="small"
                  startIcon={<Science sx={{ fontSize: 16 }} />}
                  onClick={() => onStartProductiveFailure(node)}
                >
                  Önce Dene
                </Button>
              )}
            </Box>
          )}
        </Alert>
      )}

      {/* Inline Resources */}
      {(resourcesLoading || resources.length > 0) && (
        <Box sx={{ mb: 2 }}>
          <Divider sx={{ my: 2 }} />
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1.5 }}>
            <VideoLibrary sx={{ color: '#3b82f6', fontSize: 20 }} />
            <Typography variant="subtitle2" fontWeight={700}>
              Önerilen Kaynaklar
            </Typography>
          </Box>
          {resourcesLoading ? (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, py: 2 }}>
              <CircularProgress size={20} />
              <Typography variant="body2" color="text.secondary">Kaynaklar yükleniyor...</Typography>
            </Box>
          ) : (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              {resources.slice(0, 5).map((resource, idx) => (
                <Box
                  key={resource.video_id || idx}
                  component="a"
                  href={resource.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 1.5,
                    p: 1.5,
                    borderRadius: 1.5,
                    backgroundColor: 'grey.50',
                    textDecoration: 'none',
                    color: 'inherit',
                    transition: 'background-color 0.2s',
                    '&:hover': { backgroundColor: 'grey.100' },
                  }}
                >
                  {resource.thumbnail ? (
                    <Box
                      component="img"
                      src={resource.thumbnail}
                      alt=""
                      sx={{ width: 64, height: 36, borderRadius: 1, objectFit: 'cover', flexShrink: 0 }}
                    />
                  ) : (
                    <VideoLibrary sx={{ color: '#ef4444', fontSize: 24, flexShrink: 0 }} />
                  )}
                  <Box sx={{ flex: 1, minWidth: 0 }}>
                    <Typography variant="body2" fontWeight={600} noWrap>
                      {resource.title}
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                      <Typography variant="caption" color="text.secondary">
                        {resource.channel}
                      </Typography>
                      {resource.duration && (
                        <Typography variant="caption" color="text.secondary">
                          · {resource.duration}
                        </Typography>
                      )}
                      {resource.scores?.final_score != null && (
                        <Chip
                          label={`${Math.round(resource.scores.final_score * 100)}%`}
                          size="small"
                          sx={{ height: 18, fontSize: 10, fontWeight: 700 }}
                        />
                      )}
                    </Box>
                  </Box>
                  <OpenInNew sx={{ fontSize: 16, color: 'text.secondary', flexShrink: 0 }} />
                </Box>
              ))}
            </Box>
          )}
        </Box>
      )}

      {/* AI Chat */}
      <Divider sx={{ my: 2 }} />
      <Box sx={{ mb: 2 }}>
        <Button
          size="small"
          startIcon={<SmartToy />}
          onClick={() => setShowChat(prev => !prev)}
          sx={{ fontWeight: 600, textTransform: 'none', mb: showChat ? 1.5 : 0 }}
        >
          {showChat ? 'AI Sohbeti Kapat' : 'AI\'ya Sor'}
        </Button>
        {showChat && (
          <NodeChatPanel nodeTitle={node.title} nodeDescription={node.description} />
        )}
      </Box>

      <Box className="flex gap-2">
        {node.status === 'completed' && (
          <Chip label="✓ Tamamlandı" color="success" />
        )}
        {node.status === 'current' && (
          <Chip label="🎯 Devam Ediyor" color="primary" />
        )}
        {node.points && (
          <Chip label={`⭐ ${node.points} Puan`} variant="outlined" />
        )}
      </Box>
    </Paper>
  );
};

export default NodeDetailsPanel;
