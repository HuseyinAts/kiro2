/**
 * IRT + Morfoloji Analizi Tab
 * IRT and Morphology Analysis Tab
 */
import { Box, Typography, Alert } from '@mui/material';
import * as React from 'react';

interface IRTMorphologyTabProps {
  analiz: any;
}

export const IRTMorphologyTab: React.FC<IRTMorphologyTabProps> = ({ analiz }) => {
  if (!analiz) {
    return (
      <Alert severity="info">
        IRT ve Morfoloji analizi henüz mevcut değil
      </Alert>
    );
  }

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        🔬 IRT + Morfoloji Analizi
      </Typography>
      <Typography variant="body2" color="textSecondary">
        Gelişmiş IRT ve morfolojik analiz sonuçları burada gösterilecek
      </Typography>
      {/* TODO: Implement full IRT + Morphology analysis UI */}
    </Box>
  );
};

export default IRTMorphologyTab;
