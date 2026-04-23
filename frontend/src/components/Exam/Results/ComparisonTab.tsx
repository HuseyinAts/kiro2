/**
 * ÖSYM/ETS Karşılaştırma Tab
 * ÖSYM/ETS Comparison Tab
 */
import { Box, Alert } from '@mui/material';
import * as React from 'react';

import { AnalysisTabPlaceholder } from './AnalysisTabPlaceholder';

interface ComparisonTabProps {
  analiz: any;
}

export const ComparisonTab: React.FC<ComparisonTabProps> = ({ analiz }) => {
  if (!analiz) {
    return (
      <Alert severity="info">
        ÖSYM/ETS karşılaştırma analizi henüz mevcut değil
      </Alert>
    );
  }

  return (
    <Box>
      <AnalysisTabPlaceholder title="ÖSYM / standart test karşılaştırması" />
    </Box>
  );
};

export default ComparisonTab;
