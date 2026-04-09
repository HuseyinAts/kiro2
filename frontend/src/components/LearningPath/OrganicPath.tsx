import React, { useEffect, useRef } from 'react';
import rough from 'roughjs';
import { seededRandom } from '@/types/dungeon';

interface OrganicPathProps {
  fromX: number;
  fromY: number;
  toX: number;
  toY: number;
  fromTopic: string;
  toTopic: string;
  prereqType: 'hard' | 'soft';
}

export const OrganicPath: React.FC<OrganicPathProps> = ({
  fromX,
  fromY,
  toX,
  toY,
  fromTopic,
  toTopic,
  prereqType,
}) => {
  const gRef = useRef<SVGGElement>(null);

  useEffect(() => {
    const g = gRef.current;
    if (!g) return;

    const svg = g.ownerSVGElement;
    if (!svg) return;

    while (g.firstChild) g.removeChild(g.firstChild);

    const rc = rough.svg(svg);
    const seed = seededRandom(`${fromTopic}-${toTopic}`);
    const cx = (fromX + toX) / 2 + (seed - 0.5) * 30;
    const cy = (fromY + toY) / 2;

    const isHard = prereqType === 'hard';
    const pathNode = rc.path(
      `M ${fromX} ${fromY} Q ${cx} ${cy} ${toX} ${toY}`,
      {
        roughness: 1.5,
        stroke: isHard ? '#8B4513' : '#A0A0A0',
        strokeWidth: isHard ? 2 : 1,
      },
    );
    g.appendChild(pathNode);
  }, [fromX, fromY, toX, toY, fromTopic, toTopic, prereqType]);

  return <g ref={gRef} />;
};
