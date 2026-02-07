import {
  ZoomIn,
  ZoomOut,
  CenterFocusStrong,
  Timeline,
  Map as MapIcon,
  ViewModule,
  PlayArrow,
  Info,
} from '@mui/icons-material';
import {
  Paper,
  IconButton,
  Chip,
  ButtonGroup,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import clsx from 'clsx';
import { AnimatePresence } from 'framer-motion';
import { useState, useRef } from 'react';

import { PathConnection } from './PathConnection';
import { PathNode, PathNodeData } from './PathNode';

interface Connection {
  from: string
  to: string
}

interface LearningPathVisualizerProps {
  nodes: PathNodeData[]
  connections: Connection[]
  currentNodeId?: string
  onNodeClick?: (node: PathNodeData) => void
  className?: string
  viewMode?: 'tree' | 'map' | 'linear'
}

export function LearningPathVisualizer({
  nodes,
  connections,
  currentNodeId,
  onNodeClick,
  className,
  viewMode: initialViewMode = 'tree',
}: LearningPathVisualizerProps) {
  const [zoom, setZoom] = useState(1);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [selectedNode, setSelectedNode] = useState<PathNodeData | null>(null);
  const [viewMode, setViewMode] = useState(initialViewMode);
  const [filter, setFilter] = useState<'all' | 'available' | 'completed'>('all');
  const [detailsOpen, setDetailsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Calculate layout based on view mode
  const calculateLayout = () => {
    const layoutNodes = [...nodes];

    switch (viewMode) {
      case 'tree': {
        // Tree layout algorithm
        const levels: Map<string, number> = new Map();
        const visited: Set<string> = new Set();

        const calculateLevel = (nodeId: string, level: number = 0) => {
          if (visited.has(nodeId)) {return;}
          visited.add(nodeId);
          levels.set(nodeId, Math.max(levels.get(nodeId) || 0, level));

          connections
            .filter(c => c.from === nodeId)
            .forEach(c => calculateLevel(c.to, level + 1));
        };

        // Find root nodes (no incoming connections)
        const rootNodes = nodes.filter(n =>
          !connections.some(c => c.to === n.id),
        );

        rootNodes.forEach(n => calculateLevel(n.id));

        // Position nodes
        const levelGroups: Map<number, string[]> = new Map();
        levels.forEach((level: number, nodeId: string) => {
          if (!levelGroups.has(level)) {
            levelGroups.set(level, []);
          }
          levelGroups.get(level)!.push(nodeId);
        });

        layoutNodes.forEach(node => {
          const level = levels.get(node.id) || 0;
          const group = levelGroups.get(level) || [];
          const index = group.indexOf(node.id);
          const count = group.length;

          node.position = {
            x: 100 + level * 250,
            y: 100 + (index - (count - 1) / 2) * 150,
          };
        });
        break;
      }

      case 'map': {
        // Circular/radial layout
        const centerX = 400;
        const centerY = 300;
        const radius = 200;

        layoutNodes.forEach((node, index) => {
          const angle = (index / nodes.length) * 2 * Math.PI;
          node.position = {
            x: centerX + radius * Math.cos(angle),
            y: centerY + radius * Math.sin(angle),
          };
        });
        break;
      }

      case 'linear': {
        // Linear layout
        layoutNodes.forEach((node, index) => {
          node.position = {
            x: 100 + index * 200,
            y: 300,
          };
        });
        break;
      }
    }

    return layoutNodes;
  };

  const layoutNodes = calculateLayout();
  const filteredNodes = layoutNodes.filter(node => {
    if (filter === 'all') {return true;}
    if (filter === 'available') {return node.status !== 'locked';}
    if (filter === 'completed') {return node.status === 'completed';}
    return true;
  });

  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX - offset.x, y: e.clientY - offset.y });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) {return;}
    setOffset({
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y,
    });
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const handleZoomIn = () => setZoom(prev => Math.min(prev + 0.1, 2));
  const handleZoomOut = () => setZoom(prev => Math.max(prev - 0.1, 0.5));
  const handleReset = () => {
    setZoom(1);
    setOffset({ x: 0, y: 0 });
  };

  const handleNodeClick = (node: PathNodeData) => {
    setSelectedNode(node);
    setDetailsOpen(true);
    onNodeClick?.(node);
  };

  const getProgress = () => {
    const completed = nodes.filter(n => n.status === 'completed').length;
    return Math.round((completed / nodes.length) * 100);
  };

  const getTotalPoints = () => {
    return nodes
      .filter(n => n.status === 'completed')
      .reduce((sum, n) => sum + (n.points || 0), 0);
  };

  return (
    <Paper
      elevation={3}
      className={clsx('relative overflow-hidden bg-gray-50', className)}
    >
      {/* Header Controls */}
      <div className="absolute top-4 left-4 right-4 z-20 flex justify-between items-start">
        {/* View Mode Selector */}
        <ButtonGroup variant="contained" size="small">
          <Button
            onClick={() => setViewMode('tree')}
            startIcon={<Timeline />}
            variant={viewMode === 'tree' ? 'contained' : 'outlined'}
          >
            Ağaç
          </Button>
          <Button
            onClick={() => setViewMode('map')}
            startIcon={<MapIcon />}
            variant={viewMode === 'map' ? 'contained' : 'outlined'}
          >
            Harita
          </Button>
          <Button
            onClick={() => setViewMode('linear')}
            startIcon={<ViewModule />}
            variant={viewMode === 'linear' ? 'contained' : 'outlined'}
          >
            Doğrusal
          </Button>
        </ButtonGroup>

        {/* Stats */}
        <div className="flex gap-2">
          <Chip
            label={`İlerleme: %${getProgress()}`}
            color="primary"
            icon={<PlayArrow />}
          />
          <Chip
            label={`${getTotalPoints()} Puan`}
            color="secondary"
            variant="outlined"
          />
          <Chip
            label={`${nodes.filter(n => n.status === 'completed').length}/${nodes.length} Tamamlandı`}
            variant="outlined"
          />
        </div>
      </div>

      {/* Zoom Controls */}
      <div className="absolute bottom-4 right-4 z-20 flex flex-col gap-2">
        <IconButton
          onClick={handleZoomIn}
          className="bg-white shadow-md hover:bg-gray-100"
        >
          <ZoomIn />
        </IconButton>
        <IconButton
          onClick={handleZoomOut}
          className="bg-white shadow-md hover:bg-gray-100"
        >
          <ZoomOut />
        </IconButton>
        <IconButton
          onClick={handleReset}
          className="bg-white shadow-md hover:bg-gray-100"
        >
          <CenterFocusStrong />
        </IconButton>
      </div>

      {/* Filter Controls */}
      <div className="absolute bottom-4 left-4 z-20">
        <ButtonGroup size="small" variant="outlined">
          <Button
            onClick={() => setFilter('all')}
            variant={filter === 'all' ? 'contained' : 'outlined'}
          >
            Tümü
          </Button>
          <Button
            onClick={() => setFilter('available')}
            variant={filter === 'available' ? 'contained' : 'outlined'}
          >
            Erişilebilir
          </Button>
          <Button
            onClick={() => setFilter('completed')}
            variant={filter === 'completed' ? 'contained' : 'outlined'}
          >
            Tamamlanan
          </Button>
        </ButtonGroup>
      </div>

      {/* Visualization Area */}
      <div
        ref={containerRef}
        className="relative w-full h-full cursor-move"
        style={{
          minHeight: '600px',
        }}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        <div
          style={{
            transform: `translate(${offset.x}px, ${offset.y}px) scale(${zoom})`,
            transformOrigin: 'center',
            transition: isDragging ? 'none' : 'transform 0.3s ease',
          }}
        >
          {/* Render Connections */}
          {connections.map((connection, index) => {
            const fromNode = layoutNodes.find(n => n.id === connection.from);
            const toNode = layoutNodes.find(n => n.id === connection.to);

            if (!fromNode || !toNode) {return null;}

            const isActive =
              fromNode.status === 'completed' &&
              (toNode.status === 'current' || toNode.status === 'available');

            const isCompleted =
              fromNode.status === 'completed' &&
              toNode.status === 'completed';

            return (
              <PathConnection
                key={`${connection.from}-${connection.to}-${index}`}
                from={{
                  x: fromNode.position.x + 100,
                  y: fromNode.position.y + 40,
                }}
                to={{
                  x: toNode.position.x + 100,
                  y: toNode.position.y + 40,
                }}
                isActive={isActive}
                isCompleted={isCompleted}
                curved={viewMode !== 'linear'}
                animated={true}
              />
            );
          })}

          {/* Render Nodes */}
          <AnimatePresence>
            {filteredNodes.map((node) => (
              <PathNode
                key={node.id}
                node={node}
                onClick={handleNodeClick}
                isHighlighted={node.id === currentNodeId}
                showDetails={zoom >= 0.8}
              />
            ))}
          </AnimatePresence>
        </div>
      </div>

      {/* Node Details Dialog */}
      <Dialog
        open={detailsOpen}
        onClose={() => setDetailsOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        {selectedNode && (
          <>
            <DialogTitle>
              <div className="flex items-center gap-2">
                <Info />
                {selectedNode.title}
              </div>
            </DialogTitle>
            <DialogContent>
              <div className="space-y-4 pt-2">
                <p className="text-gray-600">{selectedNode.description}</p>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <strong>Durum:</strong> {selectedNode.status}
                  </div>
                  <div>
                    <strong>Zorluk:</strong> {selectedNode.difficulty}
                  </div>
                  <div>
                    <strong>Süre:</strong> {selectedNode.estimatedTime}
                  </div>
                  <div>
                    <strong>Puan:</strong> {selectedNode.points || 0}
                  </div>
                </div>

                {selectedNode.prerequisites && selectedNode.prerequisites.length > 0 && (
                  <div>
                    <strong>Önkoşullar:</strong>
                    <ul className="list-disc list-inside mt-1">
                      {selectedNode.prerequisites.map((req, i) => (
                        <li key={i} className="text-sm text-gray-600">{req}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setDetailsOpen(false)}>
                Kapat
              </Button>
              {selectedNode.status === 'available' && (
                <Button variant="contained" color="primary">
                  Başla
                </Button>
              )}
            </DialogActions>
          </>
        )}
      </Dialog>
    </Paper>
  );
}

export default LearningPathVisualizer;