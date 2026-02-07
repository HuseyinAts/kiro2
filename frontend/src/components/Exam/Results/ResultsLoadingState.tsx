/**
 * Results Loading State Component
 *
 * Displays loading spinner while fetching exam results
 */

import { Box, CircularProgress, Typography } from '@mui/material';
import * as React from 'react';

export const ResultsLoadingState: React.FC = () => {
  return (
    <Box
      display="flex"
      justifyContent="center"
      alignItems="center"
      minHeight="400px"
      flexDirection="column"
      gap={2}
    >
      <CircularProgress size={60} />
      <Typography variant="h6">Gelişmiş analiz yükleniyor...</Typography>
    </Box>
  );
};

export default ResultsLoadingState;
