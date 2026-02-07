/**
 * Path Error State Component
 *
 * Displays error state for learning path
 * Extracted from LearningPathPage.tsx
 */

import { Refresh } from '@mui/icons-material';
import { Container, Alert, Button } from '@mui/material';
import * as React from 'react';

export interface PathErrorStateProps {
  error: string
  onRetry: () => void
}

/**
 * Error state component for learning path
 *
 * Shows error message and retry button
 */
export const PathErrorState: React.FC<PathErrorStateProps> = ({ error, onRetry }) => {
  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Alert severity="error" sx={{ mb: 3 }}>
        {error}
      </Alert>
      <Button variant="contained" onClick={onRetry} startIcon={<Refresh />}>
        Tekrar Dene
      </Button>
    </Container>
  );
};

export default PathErrorState;
