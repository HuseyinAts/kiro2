/**
 * Öğrenme Stili Tab
 * Hybrid Learning Style Analysis Tab
 */
import { Box, Alert } from '@mui/material';
import * as React from 'react';

import { AnalysisTabPlaceholder } from './AnalysisTabPlaceholder';

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
      <AnalysisTabPlaceholder title="Hibrit öğrenme stili analizi" />
    </Box>
  );
};

export default LearningStyleTab;
