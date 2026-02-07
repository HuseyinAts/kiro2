/**
 * Page Skeleton Loader
 *
 * Better UX than spinner for page lazy loading
 * Shows placeholder structure while page loads
 */

import { Container, Box, Skeleton, Paper } from '@mui/material';
import * as React from 'react';

/**
 * Generic page skeleton loader
 *
 * Provides better perceived performance than a spinner
 * by showing the expected page structure
 */
export const PageSkeleton: React.FC = () => {
  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Page Header */}
      <Box sx={{ mb: 4 }}>
        <Skeleton variant="text" width="40%" height={48} sx={{ mb: 1 }} />
        <Skeleton variant="text" width="60%" height={24} />
      </Box>

      {/* Action Bar */}
      <Box sx={{ mb: 3, display: 'flex', gap: 2, justifyContent: 'space-between' }}>
        <Skeleton variant="rectangular" width={200} height={40} sx={{ borderRadius: 1 }} />
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Skeleton variant="rectangular" width={120} height={40} sx={{ borderRadius: 1 }} />
          <Skeleton variant="rectangular" width={100} height={40} sx={{ borderRadius: 1 }} />
        </Box>
      </Box>

      {/* Main Content Cards */}
      <Box className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-4">
        {[1, 2, 3].map((i) => (
          <Paper key={i} elevation={2} sx={{ p: 3 }}>
            <Skeleton variant="text" width="70%" height={28} sx={{ mb: 2 }} />
            <Skeleton variant="rectangular" width="100%" height={120} sx={{ mb: 2, borderRadius: 1 }} />
            <Box sx={{ display: 'flex', gap: 1, mb: 1 }}>
              <Skeleton variant="rectangular" width="30%" height={24} sx={{ borderRadius: 1 }} />
              <Skeleton variant="rectangular" width="40%" height={24} sx={{ borderRadius: 1 }} />
            </Box>
            <Skeleton variant="text" width="90%" height={20} />
          </Paper>
        ))}
      </Box>

      {/* Data Table/List */}
      <Paper elevation={2} sx={{ p: 3 }}>
        <Skeleton variant="text" width="30%" height={32} sx={{ mb: 3 }} />
        {[1, 2, 3, 4, 5].map((i) => (
          <Box key={i} sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 2 }}>
            <Skeleton variant="circular" width={40} height={40} />
            <Box sx={{ flex: 1 }}>
              <Skeleton variant="text" width="60%" height={24} sx={{ mb: 0.5 }} />
              <Skeleton variant="text" width="40%" height={20} />
            </Box>
            <Skeleton variant="rectangular" width={80} height={32} sx={{ borderRadius: 1 }} />
          </Box>
        ))}
      </Paper>
    </Container>
  );
};

PageSkeleton.displayName = 'PageSkeleton';

export default PageSkeleton;
