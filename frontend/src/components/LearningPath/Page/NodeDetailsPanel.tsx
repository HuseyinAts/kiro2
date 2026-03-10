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
} from '@mui/material';
import * as React from 'react';

import { formatDifficulty } from '../../../utils/learningPathHelpers';
import { PathNodeData } from '../PathNode';

export interface NodeDetailsPanelProps {
  node: PathNodeData
  onClose: () => void
  onStartQuiz?: (node: PathNodeData) => void
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
}) => {
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
          {onStartQuiz && node.status !== 'completed' && (
            <Button
              variant="contained"
              color="primary"
              size="small"
              onClick={() => onStartQuiz(node)}
              sx={{ mt: 1 }}
            >
              Quiz Başlat
            </Button>
          )}
        </Alert>
      )}

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
