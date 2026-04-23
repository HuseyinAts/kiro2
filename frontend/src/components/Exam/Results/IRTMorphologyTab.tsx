/**
 * IRT + Morfoloji Analizi Tab
 * IRT and Morphology Analysis Tab
 */
import { Box, Alert } from '@mui/material';
import * as React from 'react';

import { AnalysisTabPlaceholder } from './AnalysisTabPlaceholder';

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
      <AnalysisTabPlaceholder title="IRT ve morfoloji analizi" />
    </Box>
  );
};

export default IRTMorphologyTab;
