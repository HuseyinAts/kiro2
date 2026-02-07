/**
 * ÖSYM/ETS Karşılaştırma Tab
 * ÖSYM/ETS Comparison Tab
 */
import { Box, Typography, Alert } from '@mui/material';
import * as React from 'react';

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
      <Typography variant="h6" gutterBottom>
        📊 ÖSYM/ETS Karşılaştırma
      </Typography>
      <Typography variant="body2" color="textSecondary">
        Standart test karşılaştırma sonuçları burada gösterilecek
      </Typography>
      {/* TODO: Implement full ÖSYM/ETS comparison UI */}
    </Box>
  );
};

export default ComparisonTab;
