/**
 * Öğrenme Stili Tab
 * Hybrid Learning Style Analysis Tab
 */
import { Box, Typography, Alert } from '@mui/material';
import * as React from 'react';

interface LearningStyleTabProps {
  analiz: any;
}

export const LearningStyleTab: React.FC<LearningStyleTabProps> = ({ analiz }) => {
  if (!analiz) {
    return (
      <Alert severity="info">
        Hibrit öğrenme stili analizi henüz mevcut değil
      </Alert>
    );
  }

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        📚 Hibrit Öğrenme Stili Analizi
      </Typography>
      <Typography variant="body2" color="textSecondary">
        Kişisel öğrenme stili analiz sonuçları burada gösterilecek
      </Typography>
      {/* TODO: Implement full learning style analysis UI */}
    </Box>
  );
};

export default LearningStyleTab;
