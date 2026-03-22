/**
 * Modern Learning Path Visualizer - Glassmorphism Design
 * Interactive visualization with modern UI and smooth animations
 */

import {
  ZoomIn,
  ZoomOut,
  CenterFocusStrong,
  Timeline,
  Map as MapIcon,
  ViewModule,
  PlayArrow,
  CheckCircle,
  RadioButtonUnchecked,
  Lock,
  Stars,
  Schedule,
} from '@mui/icons-material';
import {
  Box,
  IconButton,
  Chip,
  ButtonGroup,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Typography,
  LinearProgress,
  Grid,
  Alert,
} from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';
import { useState, useRef } from 'react';

import modernColors from '../../theme/modern-colors';
import { GlassCard } from '../ui/GlassCard';
import { ModernButton } from '../ui/ModernButton';

import { PathConnection } from './PathConnection';
import { PathNodeData } from './PathNode';

interface Connection {
  from: string
  to: string
}

interface ModernLearningPathVisualizerProps {
  nodes: PathNodeData[]
  connections: Connection[]
  currentNodeId?: string
  onNodeClick?: (node: PathNodeData) => void
  className?: string
  viewMode?: 'tree' | 'map' | 'linear'
}

export function ModernLearningPathVisualizer({
  nodes,
  connections,
  currentNodeId,
  onNodeClick,
  className,
  viewMode: initialViewMode = 'tree',
}: ModernLearningPathVisualizerProps) {
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

        const MAX_DEPTH = 50;
        const calculateLevel = (nodeId: string, level: number = 0) => {
          if (visited.has(nodeId) || level > MAX_DEPTH) {return;}
          visited.add(nodeId);
          levels.set(nodeId, Math.max(levels.get(nodeId) || 0, level));

          connections
            .filter((c) => c.from === nodeId)
            .forEach((c) => calculateLevel(c.to, level + 1));
        };

        // Find root nodes (no incoming connections)
        const rootNodes = nodes.filter((n) => !connections.some((c) => c.to === n.id));

        rootNodes.forEach((n) => calculateLevel(n.id));

        // Position nodes
        const levelGroups: Map<number, string[]> = new Map();
        levels.forEach((level: number, nodeId: string) => {
          if (!levelGroups.has(level)) {
            levelGroups.set(level, []);
          }
          levelGroups.get(level)!.push(nodeId);
        });

        layoutNodes.forEach((node) => {
          const level = levels.get(node.id) || 0;
          const group = levelGroups.get(level) || [];
          const index = group.indexOf(node.id);
          const count = group.length;

          node.position = {
            x: 100 + level * 300,
            y: 100 + (index - (count - 1) / 2) * 180,
          };
        });
        break;
      }

      case 'map': {
        // Circular/radial layout
        const centerX = 400;
        const centerY = 300;
        const radius = 220;

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
            x: 100 + index * 220,
            y: 300,
          };
        });
        break;
      }
    }

    return layoutNodes;
  };

  const layoutNodes = calculateLayout();
  const filteredNodes = layoutNodes.filter((node) => {
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

  const handleZoomIn = () => setZoom((prev) => Math.min(prev + 0.1, 2));
  const handleZoomOut = () => setZoom((prev) => Math.max(prev - 0.1, 0.5));
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
    const completed = nodes.filter((n) => n.status === 'completed').length;
    return Math.round((completed / nodes.length) * 100);
  };

  const getTotalPoints = () => {
    return nodes
      .filter((n) => n.status === 'completed')
      .reduce((sum, n) => sum + (n.points || 0), 0);
  };

  const getNodeGradient = (status: string) => {
    switch (status) {
      case 'completed':
        return modernColors.gradients.success;
      case 'current':
        return modernColors.gradients.primary;
      case 'available':
        return modernColors.gradients.ocean;
      default:
        return modernColors.gradients.sunset;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle sx={{ color: '#10b981' }} />;
      case 'current':
        return <PlayArrow sx={{ color: '#3b82f6' }} />;
      case 'locked':
        return <Lock sx={{ color: '#94a3b8' }} />;
      default:
        return <Stars sx={{ color: '#8b5cf6' }} />;
    }
  };

  const progress = getProgress();
  const totalPoints = getTotalPoints();

  return (
    <Box className={className}>
      {/* Header with Stats */}
      <Box sx={{ mb: 3 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} md={4}>
            <GlassCard
              glassIntensity="light"
              hoverable
              gradient={modernColors.gradients.primary}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <PlayArrow sx={{ fontSize: 32, color: '#3b82f6' }} />
                <Box sx={{ flex: 1 }}>
                  <Typography variant="h4" sx={{ fontWeight: 800, mb: 0.5 }}>
                    {progress}%
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    İlerleme
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={progress}
                    sx={{
                      mt: 1,
                      height: 6,
                      borderRadius: 3,
                      backgroundColor: modernColors.glass.black.light,
                      '& .MuiLinearProgress-bar': {
                        borderRadius: 3,
                        background: modernColors.gradients.primary,
                      },
                    }}
                  />
                </Box>
              </Box>
            </GlassCard>
          </Grid>

          <Grid item xs={12} md={4}>
            <GlassCard
              glassIntensity="light"
              hoverable
              gradient={modernColors.gradients.warning}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Stars sx={{ fontSize: 32, color: '#f59e0b' }} />
                <Box>
                  <Typography variant="h4" sx={{ fontWeight: 800, mb: 0.5 }}>
                    {totalPoints}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Toplam Puan
                  </Typography>
                </Box>
              </Box>
            </GlassCard>
          </Grid>

          <Grid item xs={12} md={4}>
            <GlassCard
              glassIntensity="light"
              hoverable
              gradient={modernColors.gradients.success}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <CheckCircle sx={{ fontSize: 32, color: '#10b981' }} />
                <Box>
                  <Typography variant="h4" sx={{ fontWeight: 800, mb: 0.5 }}>
                    {nodes.filter((n) => n.status === 'completed').length}/{nodes.length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Tamamlanan
                  </Typography>
                </Box>
              </Box>
            </GlassCard>
          </Grid>
        </Grid>
      </Box>

      {/* Visualization Area */}
      <GlassCard glassIntensity="medium" elevated>
        {/* Controls Bar */}
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            mb: 2,
            flexWrap: 'wrap',
            gap: 2,
          }}
        >
          {/* View Mode Selector */}
          <ButtonGroup variant="contained" size="small">
            <Button
              onClick={() => setViewMode('tree')}
              startIcon={<Timeline />}
              sx={{
                background:
                  viewMode === 'tree'
                    ? modernColors.gradients.primary
                    : modernColors.glass.white.medium,
                color: viewMode === 'tree' ? 'white' : 'text.primary',
                '&:hover': {
                  background:
                    viewMode === 'tree' ? modernColors.gradients.primary : undefined,
                },
              }}
            >
              Ağaç
            </Button>
            <Button
              onClick={() => setViewMode('map')}
              startIcon={<MapIcon />}
              sx={{
                background:
                  viewMode === 'map'
                    ? modernColors.gradients.primary
                    : modernColors.glass.white.medium,
                color: viewMode === 'map' ? 'white' : 'text.primary',
                '&:hover': {
                  background:
                    viewMode === 'map' ? modernColors.gradients.primary : undefined,
                },
              }}
            >
              Harita
            </Button>
            <Button
              onClick={() => setViewMode('linear')}
              startIcon={<ViewModule />}
              sx={{
                background:
                  viewMode === 'linear'
                    ? modernColors.gradients.primary
                    : modernColors.glass.white.medium,
                color: viewMode === 'linear' ? 'white' : 'text.primary',
                '&:hover': {
                  background:
                    viewMode === 'linear' ? modernColors.gradients.primary : undefined,
                },
              }}
            >
              Doğrusal
            </Button>
          </ButtonGroup>

          {/* Filter Controls */}
          <ButtonGroup size="small">
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
        </Box>

        {/* Canvas Area */}
        <Box
          ref={containerRef}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          sx={{
            position: 'relative',
            width: '100%',
            minHeight: '600px',
            background: modernColors.gradients.mesh,
            borderRadius: 2,
            overflow: 'hidden',
            cursor: isDragging ? 'grabbing' : 'grab',
          }}
        >
          <motion.div
            style={{
              transform: `translate(${offset.x}px, ${offset.y}px) scale(${zoom})`,
              transformOrigin: 'center',
              transition: isDragging ? 'none' : 'transform 0.3s ease',
            }}
          >
            {/* Render Connections */}
            {connections.map((connection, index) => {
              const fromNode = layoutNodes.find((n) => n.id === connection.from);
              const toNode = layoutNodes.find((n) => n.id === connection.to);

              if (!fromNode || !toNode) {return null;}

              const isActive =
                fromNode.status === 'completed' &&
                (toNode.status === 'current' || toNode.status === 'available');

              const isCompleted =
                fromNode.status === 'completed' && toNode.status === 'completed';

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
              {filteredNodes.map((node, index) => (
                <motion.div
                  key={node.id}
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.8 }}
                  transition={{ duration: 0.3, delay: index * 0.05 }}
                  style={{
                    position: 'absolute',
                    left: node.position.x,
                    top: node.position.y,
                    width: 200,
                  }}
                  onClick={() => handleNodeClick(node)}
                >
                  <GlassCard
                    glassIntensity="light"
                    hoverable
                    gradient={getNodeGradient(node.status)}
                    sx={{
                      cursor: 'pointer',
                      border:
                        node.id === currentNodeId
                          ? '3px solid #3b82f6'
                          : '1px solid rgba(255, 255, 255, 0.2)',
                      transition: 'all 0.3s ease',
                    }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1, mb: 1 }}>
                      {getStatusIcon(node.status)}
                      <Typography variant="h6" sx={{ fontWeight: 700, flex: 1, fontSize: 14 }}>
                        {node.title}
                      </Typography>
                    </Box>

                    {zoom >= 0.8 && (
                      <>
                        <Typography
                          variant="body2"
                          color="text.secondary"
                          sx={{ mb: 1, fontSize: 11 }}
                        >
                          {node.description}
                        </Typography>

                        <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                          <Chip
                            label={node.difficulty}
                            size="small"
                            sx={{ fontSize: 10, height: 20 }}
                          />
                          {node.points && (
                            <Chip
                              icon={<Stars sx={{ fontSize: 12 }} />}
                              label={`${node.points}p`}
                              size="small"
                              color="warning"
                              sx={{ fontSize: 10, height: 20 }}
                            />
                          )}
                        </Box>
                      </>
                    )}
                  </GlassCard>
                </motion.div>
              ))}
            </AnimatePresence>
          </motion.div>

          {/* Zoom Controls */}
          <Box
            sx={{
              position: 'absolute',
              bottom: 16,
              right: 16,
              display: 'flex',
              flexDirection: 'column',
              gap: 1,
            }}
          >
            <IconButton
              onClick={handleZoomIn}
              sx={{
                background: modernColors.glass.white.medium,
                backdropFilter: 'blur(16px)',
                '&:hover': {
                  background: modernColors.glass.white.light,
                },
              }}
            >
              <ZoomIn />
            </IconButton>
            <IconButton
              onClick={handleZoomOut}
              sx={{
                background: modernColors.glass.white.medium,
                backdropFilter: 'blur(16px)',
                '&:hover': {
                  background: modernColors.glass.white.light,
                },
              }}
            >
              <ZoomOut />
            </IconButton>
            <IconButton
              onClick={handleReset}
              sx={{
                background: modernColors.glass.white.medium,
                backdropFilter: 'blur(16px)',
                '&:hover': {
                  background: modernColors.glass.white.light,
                },
              }}
            >
              <CenterFocusStrong />
            </IconButton>
          </Box>
        </Box>
      </GlassCard>

      {/* Node Details Dialog */}
      <Dialog
        open={detailsOpen}
        onClose={() => setDetailsOpen(false)}
        maxWidth="sm"
        fullWidth
        PaperProps={{
          sx: {
            background: modernColors.glass.white.light,
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(255, 255, 255, 0.2)',
          },
        }}
      >
        {selectedNode && (
          <>
            <DialogTitle>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                {getStatusIcon(selectedNode.status)}
                <Typography variant="h6" sx={{ fontWeight: 700 }}>
                  {selectedNode.title}
                </Typography>
              </Box>
            </DialogTitle>
            <DialogContent>
              <Box sx={{ pt: 2 }}>
                <Typography variant="body1" sx={{ mb: 3 }}>
                  {selectedNode.description}
                </Typography>

                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <GlassCard glassIntensity="light">
                      <Typography variant="caption" color="text.secondary">
                        Durum
                      </Typography>
                      <Typography variant="body1" sx={{ fontWeight: 600 }}>
                        {selectedNode.status === 'completed'
                          ? 'Tamamlandı'
                          : selectedNode.status === 'current'
                          ? 'Devam Ediyor'
                          : selectedNode.status === 'available'
                          ? 'Erişilebilir'
                          : 'Kilitli'}
                      </Typography>
                    </GlassCard>
                  </Grid>

                  <Grid item xs={6}>
                    <GlassCard glassIntensity="light">
                      <Typography variant="caption" color="text.secondary">
                        Zorluk
                      </Typography>
                      <Typography variant="body1" sx={{ fontWeight: 600 }}>
                        {selectedNode.difficulty}
                      </Typography>
                    </GlassCard>
                  </Grid>

                  <Grid item xs={6}>
                    <GlassCard glassIntensity="light">
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Schedule fontSize="small" />
                        <Box>
                          <Typography variant="caption" color="text.secondary">
                            Süre
                          </Typography>
                          <Typography variant="body1" sx={{ fontWeight: 600 }}>
                            {selectedNode.estimatedTime}
                          </Typography>
                        </Box>
                      </Box>
                    </GlassCard>
                  </Grid>

                  <Grid item xs={6}>
                    <GlassCard glassIntensity="light">
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Stars fontSize="small" color="warning" />
                        <Box>
                          <Typography variant="caption" color="text.secondary">
                            Puan
                          </Typography>
                          <Typography variant="body1" sx={{ fontWeight: 600 }}>
                            {selectedNode.points || 0}
                          </Typography>
                        </Box>
                      </Box>
                    </GlassCard>
                  </Grid>
                </Grid>

                {selectedNode.prerequisites && selectedNode.prerequisites.length > 0 && (
                  <Box sx={{ mt: 3 }}>
                    <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 1 }}>
                      Önkoşullar:
                    </Typography>
                    {selectedNode.status === 'locked' && (
                      <Alert severity="warning" sx={{ mb: 1.5, borderRadius: 2 }}>
                        Bu konuya başlamak için önce aşağıdakileri tamamlayın:
                      </Alert>
                    )}
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                      {selectedNode.prerequisites.map((reqId, i) => {
                        const prereqNode = nodes.find(n => n.id === reqId || n.title === reqId);
                        const isComplete = prereqNode?.status === 'completed';
                        return (
                          <Chip
                            key={i}
                            label={prereqNode?.title || reqId}
                            size="small"
                            color={isComplete ? 'success' : 'default'}
                            variant={isComplete ? 'filled' : 'outlined'}
                            icon={isComplete
                              ? <CheckCircle sx={{ fontSize: 16 }} />
                              : <RadioButtonUnchecked sx={{ fontSize: 16 }} />
                            }
                          />
                        );
                      })}
                    </Box>
                  </Box>
                )}
              </Box>
            </DialogContent>
            <DialogActions>
              <ModernButton variant="glass" onClick={() => setDetailsOpen(false)}>
                Kapat
              </ModernButton>
              {selectedNode.status === 'available' && (
                <ModernButton
                  variant="gradient"
                  gradient={modernColors.gradients.primary}
                  icon={<PlayArrow />}
                  glow
                >
                  Başla
                </ModernButton>
              )}
            </DialogActions>
          </>
        )}
      </Dialog>
    </Box>
  );
}

export default ModernLearningPathVisualizer;
