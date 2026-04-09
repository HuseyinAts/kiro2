import React from 'react';

/** SVG filter definitions for fog of war effect. Place inside <svg><defs>. */
export const FogOfWarDefs: React.FC = () => (
  <filter id="dungeon-fog">
    <feGaussianBlur stdDeviation="4" />
    <feColorMatrix
      type="matrix"
      values="0.3 0 0 0 0.2
              0 0.3 0 0 0.2
              0 0 0.3 0 0.25
              0 0 0 1 0"
    />
  </filter>
);

interface FogWrapperProps {
  opacity: number;
  children: React.ReactNode;
}

/**
 * Wraps children in fog effect when opacity > 0.1.
 * opacity=0 → no fog, opacity=0.9 → near-opaque fog.
 */
export const FogWrapper: React.FC<FogWrapperProps> = ({ opacity, children }) => {
  const hasFog = opacity > 0.1;
  return (
    <g
      filter={hasFog ? 'url(#dungeon-fog)' : undefined}
      opacity={1 - opacity}
    >
      {children}
    </g>
  );
};
