import React from 'react';

const PARCHMENT_STYLE: React.CSSProperties = {
  position: 'absolute',
  inset: 0,
  background: `
    radial-gradient(ellipse at 50% 0%, rgba(255,248,220,0.9) 0%, transparent 70%),
    radial-gradient(ellipse at 80% 100%, rgba(210,180,140,0.3) 0%, transparent 50%),
    linear-gradient(180deg, #FFF8DC 0%, #F5E6C8 30%, #E8D5B0 70%, #DBC4A0 100%)
  `,
  zIndex: 0,
};

/** Full-size parchment background for the dungeon map viewport. */
export const ParchmentBackground: React.FC = () => (
  <div style={PARCHMENT_STYLE} aria-hidden="true" />
);
