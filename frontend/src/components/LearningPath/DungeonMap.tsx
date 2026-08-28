import React, { useState, useCallback } from 'react';
import { useGesture } from '@use-gesture/react';
import { Box, CircularProgress, Typography } from '@mui/material';
import { ParchmentBackground } from './ParchmentBackground';
import { FogOfWarDefs, FogWrapper } from './FogOfWar';
import { DungeonRoom } from './DungeonRoom';
import { OrganicPath } from './OrganicPath';
import { fogOpacity } from '@/types/dungeon';
import { useDungeonMap, type LayoutNode } from '@/hooks/useDungeonMap';

interface DungeonMapProps {
  subject: string;
  onNodeClick?: (node: LayoutNode) => void;
}

const SVG_PADDING = 100;

export const DungeonMap: React.FC<DungeonMapProps> = ({
  subject,
  onNodeClick,
}) => {
  const { nodes, edges, theta, loading, error } = useDungeonMap(subject);
  const [transform, setTransform] = useState({ x: 0, y: 0, scale: 1 });

  const bind = useGesture({
    onDrag: ({ delta: [dx, dy], event }) => {
      event.preventDefault();
      setTransform((t) => ({ ...t, x: t.x + dx, y: t.y + dy }));
    },
    onPinch: ({ offset: [scale] }) => {
      setTransform((t) => ({
        ...t,
        scale: Math.max(0.3, Math.min(3, scale)),
      }));
    },
  }, {
    drag: { filterTaps: true },
  });

  const handleNodeClick = useCallback(
    (node: LayoutNode) => {
      onNodeClick?.(node);
    },
    [onNodeClick],
  );

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ textAlign: 'center', py: 8 }}>
        <Typography color="error">{error}</Typography>
      </Box>
    );
  }

  if (nodes.length === 0) {
    return (
      <Box sx={{ textAlign: 'center', py: 8 }}>
        <Typography color="text.secondary">
          Bu ders icin henuz konu bulunamadi.
        </Typography>
      </Box>
    );
  }

  // Compute SVG viewBox from node positions
  const xs = nodes.map((n) => n.x);
  const ys = nodes.map((n) => n.y);
  const minX = Math.min(...xs) - SVG_PADDING;
  const minY = Math.min(...ys) - SVG_PADDING;
  const maxX = Math.max(...xs) + SVG_PADDING;
  const maxY = Math.max(...ys) + SVG_PADDING;
  const width = maxX - minX;
  const height = maxY - minY;

  return (
    <Box
      sx={{
        position: 'relative',
        width: '100%',
        height: 500,
        overflow: 'hidden',
        borderRadius: 2,
        touchAction: 'none',
      }}
    >
      <ParchmentBackground />

      <svg
        {...bind()}
        width="100%"
        height="100%"
        viewBox={`${minX} ${minY} ${width} ${height}`}
        style={{
          position: 'relative',
          zIndex: 1,
          transform: `translate(${transform.x}px, ${transform.y}px) scale(${transform.scale})`,
          transformOrigin: 'center center',
        }}
      >
        <defs>
          <FogOfWarDefs />
        </defs>

        {/* Edges (behind rooms) */}
        {edges.map((e) => (
          <OrganicPath
            key={`${e.from_topic}-${e.to_topic}`}
            fromX={e.fromX}
            fromY={e.fromY}
            toX={e.toX}
            toY={e.toY}
            fromTopic={e.from_topic}
            toTopic={e.to_topic}
            prereqType={e.prereq_type}
          />
        ))}

        {/* Rooms */}
        {nodes.map((node) => {
          const fog = fogOpacity(node, theta);
          return (
            <FogWrapper key={node.topic_id} opacity={fog}>
              <DungeonRoom
                topicId={node.topic_id}
                code={node.code}
                nameTr={node.name_tr}
                x={node.x}
                y={node.y}
                progress={node.progress}
                questionCount={node.question_count}
                onClick={() => handleNodeClick(node)}
              />
            </FogWrapper>
          );
        })}
      </svg>
    </Box>
  );
};
