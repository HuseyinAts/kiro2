/**
 * Results Empty State Component
 *
 * Displays message when no results are found
 */

import { Alert } from '@mui/material';
import * as React from 'react';

export const ResultsEmptyState: React.FC = () => {
  return (
    <Alert severity="info" sx={{ m: 2 }}>
      Sonuç bulunamadı
    </Alert>
  );
};

export default ResultsEmptyState;
