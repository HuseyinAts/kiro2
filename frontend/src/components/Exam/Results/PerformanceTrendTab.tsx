/**
 * Performans Trendi Tab
 * Performance Trend Analysis Tab
 */
import { Box, Typography, Alert } from '@mui/material';
import * as React from 'react';

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
      <Typography variant="h6" gutterBottom>
        📈 Performans Trendi
      </Typography>
      <Typography variant="body2" color="textSecondary">
        Zaman içinde performans gelişim sonuçları burada gösterilecek
      </Typography>
      {/* TODO: Implement full performance trend analysis UI */}
    </Box>
  );
};

export default PerformanceTrendTab;
