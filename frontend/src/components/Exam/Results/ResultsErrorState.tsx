/**
 * Results Error State Component
 *
 * Displays error message with retry button
 */

import { Refresh } from '@mui/icons-material';
import { Alert, Typography, Button } from '@mui/material';
import * as React from 'react';

export interface ResultsErrorStateProps {
  error: string
  onRetry: () => void
}

export const ResultsErrorState: React.FC<ResultsErrorStateProps> = ({ error, onRetry }) => {
  return (
    <Alert severity="error" sx={{ m: 2 }}>
      <Typography variant="h6">Hata</Typography>
      <Typography>{error}</Typography>
      <Button onClick={onRetry} startIcon={<Refresh />} sx={{ mt: 1 }}>
        Tekrar Dene
      </Button>
    </Alert>
  );
};

export default ResultsErrorState;
