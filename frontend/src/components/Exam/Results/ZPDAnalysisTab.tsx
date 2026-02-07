/**
 * ZPD Analizi Tab
 * Zone of Proximal Development Analysis Tab
 */
import { Box, Typography, Alert } from '@mui/material';
import * as React from 'react';

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
      <Typography variant="h6" gutterBottom>
        🎯 ZPD (Zone of Proximal Development) Analizi
      </Typography>
      <Typography variant="body2" color="textSecondary">
        Yakınsal Gelişim Alanı analiz sonuçları burada gösterilecek
      </Typography>
      {/* TODO: Implement full ZPD analysis UI */}
    </Box>
  );
};

export default ZPDAnalysisTab;
