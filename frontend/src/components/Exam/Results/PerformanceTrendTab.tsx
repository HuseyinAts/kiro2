/**
 * Performans Trendi Tab
 * Performance Trend Analysis Tab
 */
import { Box, Alert } from '@mui/material';
import * as React from 'react';

import { AnalysisTabPlaceholder } from './AnalysisTabPlaceholder';

interface PerformanceTrendTabProps {
  trend: any;
}

export const PerformanceTrendTab: React.FC<PerformanceTrendTabProps> = ({ trend }) => {
  if (!trend) {
    return (
      <Alert severity="info">
        Performans trendi analizi henüz mevcut değil
      </Alert>
    );
  }

  return (
    <Box>
      <AnalysisTabPlaceholder title="Performans trendi" />
    </Box>
  );
};

export default PerformanceTrendTab;
