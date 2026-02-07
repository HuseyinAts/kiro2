/**
 * Tab Loading Skeleton Component
 *
 * Skeleton loader for lazy-loaded tab components
 * Provides smooth loading experience when switching tabs
 */

import { Box, Skeleton, Paper } from '@mui/material';
import * as React from 'react';

/**
 * Skeleton loader for tab content
 *
 * Generic skeleton that works for all tab types
 */
export const TabLoadingSkeleton: React.FC = () => {
  return (
    <Box sx={{ px: 2, py: 3 }}>
      {/* Title */}
      <Skeleton variant="text" width="40%" height={36} sx={{ mb: 3 }} />

      {/* Content Cards */}
      <Box className="flex flex-col gap-3">
        {[1, 2, 3].map((i) => (
          <Paper key={i} elevation={1} sx={{ p: 3 }}>
            <Box className="flex items-center justify-between mb-2">
              <Skeleton variant="text" width="50%" height={28} />
              <Skeleton variant="rectangular" width={80} height={32} sx={{ borderRadius: 2 }} />
            </Box>
            <Skeleton variant="rectangular" width="100%" height={8} sx={{ mb: 2, borderRadius: 1 }} />
            <Box className="flex gap-2">
              <Skeleton variant="rectangular" width={120} height={24} sx={{ borderRadius: 1 }} />
              <Skeleton variant="rectangular" width={100} height={24} sx={{ borderRadius: 1 }} />
              <Skeleton variant="rectangular" width={140} height={24} sx={{ borderRadius: 1 }} />
            </Box>
          </Paper>
        ))}
      </Box>
    </Box>
  );
};

// Display name for React DevTools
TabLoadingSkeleton.displayName = 'TabLoadingSkeleton';

export default TabLoadingSkeleton;
