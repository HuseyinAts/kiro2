/**
 * PathVisualizationTab Component
 * Learning path visualization tab with node details
 */

import { Box, Typography } from '@mui/material';
import * as React from 'react';

import { LearningPathVisualizer } from './LearningPathVisualizer';
import { PathNodeData } from './PathNode';
import { PathNodeDetails } from './PathNodeDetails';

interface PathVisualizationTabProps {
  pathNodes: PathNodeData[];
  currentNodeId: string;
  showNodeDetails: boolean;
  onNodeClick: (node: PathNodeData) => void;
  onCloseNodeDetails: () => void;
}

// Helper function to generate connections between nodes
function generateConnections(nodes: PathNodeData[]) {
  const connections: Array<{ from: string; to: string }> = [];

  nodes.forEach((node, index) => {
    if (index < nodes.length - 1) {
      connections.push({
        from: node.id,
        to: nodes[index + 1].id,
      });
    }
  });

  return connections;
}

export const PathVisualizationTab: React.FC<PathVisualizationTabProps> = ({
  pathNodes,
  currentNodeId,
  showNodeDetails,
  onNodeClick,
  onCloseNodeDetails,
}) => {
  const currentNode = pathNodes.find((n) => n.id === currentNodeId);

  return (
    <Box>
      {/* Node Detail Panel */}
      {showNodeDetails && (
        <PathNodeDetails node={currentNode || null} onClose={onCloseNodeDetails} />
      )}

      {/* Path Visualization */}
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
};

export default PathVisualizationTab;
