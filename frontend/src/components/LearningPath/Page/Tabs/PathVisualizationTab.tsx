/**
 * Path Visualization Tab Component
 *
 * Displays learning path visualizer with node details
 * Extracted from LearningPathPage.tsx
 */

import { Box, Typography } from '@mui/material';
import * as React from 'react';

import { generateConnections } from '../../../../utils/learningPathHelpers';
import { LearningPathVisualizer } from '../../LearningPathVisualizer';
import { PathNodeData } from '../../PathNode';
import { NodeDetailsPanel } from '../NodeDetailsPanel';

export interface PathVisualizationTabProps {
  pathNodes: PathNodeData[]
  currentNodeId: string
  showNodeDetails: boolean
  selectedNode: PathNodeData | null
  onNodeClick: (node: PathNodeData) => void
  onCloseDetails: () => void
}

/**
 * Tab component for path visualization
 *
 * Shows learning path tree with optional node details panel
 *
 * Performance: Memoized with React.memo to prevent unnecessary re-renders
 */
export const PathVisualizationTab = React.memo<PathVisualizationTabProps>(({
  pathNodes,
  currentNodeId,
  showNodeDetails,
  selectedNode,
  onNodeClick,
  onCloseDetails,
}) => {
  return (
    <Box>
      {/* Node Details Panel (conditional) */}
      {showNodeDetails && selectedNode && (
        <NodeDetailsPanel node={selectedNode} onClose={onCloseDetails} />
      )}

      {/* Learning Path Visualizer */}
      {pathNodes.length > 0 ? (
        <LearningPathVisualizer
          nodes={pathNodes}
          connections={generateConnections(pathNodes)}
          currentNodeId={currentNodeId}
          onNodeClick={onNodeClick}
          viewMode="tree"
        />
      ) : (
        <Box className="flex flex-col items-center justify-center py-12">
          <Typography variant="h6" color="text.secondary">
            Henüz öğrenme yolu oluşturulmamış
          </Typography>
        </Box>
      )}
    </Box>
  );
});

// Display name for React DevTools
PathVisualizationTab.displayName = 'PathVisualizationTab';

export default PathVisualizationTab;
