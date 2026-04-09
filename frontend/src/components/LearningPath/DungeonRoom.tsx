import React, { useEffect, useRef } from 'react';
import rough from 'roughjs';
import { AnimatePresence, motion } from 'framer-motion';
import type { DungeonProgressData, RoomLevel } from '@/types/dungeon';
import { getRoomLevel } from '@/types/dungeon';

interface DungeonRoomProps {
  topicId: string;
  code: string;
  nameTr: string;
  x: number;
  y: number;
  progress: DungeonProgressData;
  questionCount: number;
  onClick: () => void;
}

const ROOM_WIDTH = 100;
const ROOM_HEIGHT = 70;

const LEVEL_STYLES: Record<RoomLevel, {
  roughness: number;
  strokeWidth: number;
  stroke: string;
  fill?: string;
}> = {
  0: { roughness: 3, strokeWidth: 1, stroke: '#666' },
  1: { roughness: 2, strokeWidth: 2, stroke: '#8B7355' },
  2: { roughness: 1, strokeWidth: 2, stroke: '#DAA520', fill: 'rgba(255,215,0,0.1)' },
  3: { roughness: 0.5, strokeWidth: 3, stroke: '#FFD700', fill: 'rgba(255,215,0,0.2)' },
};

const LEVEL_ICONS: Record<RoomLevel, string> = {
  0: '\u{1F512}', // lock
  1: '\u{1F6E1}', // shield
  2: '\u2B50',     // star
  3: '\u{1F451}',  // crown
};

export const DungeonRoom: React.FC<DungeonRoomProps> = ({
  topicId,
  code: _code,
  nameTr,
  x,
  y,
  progress,
  questionCount,
  onClick,
}) => {
  const gRef = useRef<SVGGElement>(null);
  const level = getRoomLevel(progress);
  const style = LEVEL_STYLES[level];

  useEffect(() => {
    const g = gRef.current;
    if (!g) return;

    const svg = g.ownerSVGElement;
    if (!svg) return;

    // Clear previous Rough.js rendering
    while (g.firstChild) g.removeChild(g.firstChild);

    const rc = rough.svg(svg);
    const rect = rc.rectangle(
      -ROOM_WIDTH / 2,
      -ROOM_HEIGHT / 2,
      ROOM_WIDTH,
      ROOM_HEIGHT,
      {
        roughness: style.roughness,
        strokeWidth: style.strokeWidth,
        stroke: style.stroke,
        fill: style.fill,
        fillStyle: style.fill ? 'solid' : undefined,
      },
    );
    g.appendChild(rect);

    return () => {
      while (g.firstChild) g.removeChild(g.firstChild);
    };
  }, [level, style]);

  return (
    <AnimatePresence mode="wait">
      <motion.g
        key={`room-${topicId}-${level}`}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.3 }}
        transform={`translate(${x}, ${y})`}
        onClick={onClick}
        style={{ cursor: 'pointer' }}
        role="button"
        aria-label={`${nameTr} — ${LEVEL_ICONS[level]}`}
      >
        {/* Rough.js rendered rectangle */}
        <g ref={gRef} />

        {/* Icon */}
        <text
          textAnchor="middle"
          dominantBaseline="central"
          y={-15}
          fontSize="18"
        >
          {LEVEL_ICONS[level]}
        </text>

        {/* Topic name */}
        <text
          textAnchor="middle"
          dominantBaseline="central"
          y={8}
          fontSize="11"
          fontFamily="serif"
          fill="#3E2723"
        >
          {nameTr.length > 16 ? nameTr.slice(0, 14) + '...' : nameTr}
        </text>

        {/* Question count */}
        <text
          textAnchor="middle"
          y={28}
          fontSize="9"
          fill="#795548"
        >
          {questionCount} soru
        </text>
      </motion.g>
    </AnimatePresence>
  );
};
