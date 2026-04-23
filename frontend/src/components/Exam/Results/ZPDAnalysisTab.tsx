/**
 * ZPD Analizi Tab
 * Zone of Proximal Development Analysis Tab
 */
import { Box, Alert } from '@mui/material';
import * as React from 'react';

import { AnalysisTabPlaceholder } from './AnalysisTabPlaceholder';

interface ZPDAnalysisTabProps {
  analiz: any;
}

export const ZPDAnalysisTab: React.FC<ZPDAnalysisTabProps> = ({ analiz }) => {
  if (!analiz) {
    return (
      <Alert severity="info">
        ZPD analizi henüz mevcut değil
      </Alert>
    );
  }

  return (
    <Box>
      <AnalysisTabPlaceholder title="ZPD (yakınsal gelişim alanı) analizi" />
    </Box>
  );
};

export default ZPDAnalysisTab;
