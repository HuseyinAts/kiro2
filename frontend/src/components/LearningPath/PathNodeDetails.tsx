/**
 * PathNodeDetails Component
 * Displays detailed information about a selected path node
 */

import { Box, Typography, Button, Divider, Paper, Chip, Alert } from '@mui/material';
import * as React from 'react';

import { PathNodeData } from './PathNode';

interface PathNodeDetailsProps {
  node: PathNodeData | null;
  onClose: () => void;
}

export const PathNodeDetails: React.FC<PathNodeDetailsProps> = ({ node, onClose }) => {
  if (!node) {return null;}

  return (
    <Paper elevation={3} sx={{ p: 3, mb: 3, position: 'relative' }}>
      <Button
        size="small"
        onClick={onClose}
        sx={{ position: 'absolute', top: 16, right: 16 }}
      >
        ✕ Kapat
      </Button>

      <Box>
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
              {node.difficulty === 'beginner'
                ? 'Başlangıç'
                : node.difficulty === 'intermediate'
                ? 'Orta'
                : 'İleri'}
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
            <Box className="flex gap-4">
              <Typography variant="body2">
                <strong>Soru Sayısı:</strong> {node.quiz.question_count}
              </Typography>
              <Typography variant="body2">
                <strong>Geçme Notu:</strong> {node.quiz.passing_score}%
              </Typography>
            </Box>
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
      </Box>
    </Paper>
  );
};

export default PathNodeDetails;
