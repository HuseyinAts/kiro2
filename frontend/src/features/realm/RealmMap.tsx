/**
 * RealmMap — Animated SVG world map of 12 YKS subject realms
 * FAZ-5: Alem Haritasi + NPC Sistemi
 */
import React, { useState, useCallback } from 'react';

export interface RealmData {
  id: string;
  slug: string;
  name: string;
  era: string;
  npc_name: string;
  color_primary: string;
  color_secondary: string;
  order_index: number;
  is_active: boolean;
  progress?: {
    bkt_score: number;
    quest_stop: number;
    xp_earned: number;
    completed: boolean;
  };
}

interface RealmMapProps {
  realms: RealmData[];
  onRealmSelect: (realm: RealmData) => void;
  selectedSlug?: string;
  className?: string;
}

// Hexagonal grid positions for 12 realms (SVG viewBox 0 0 800 600)
const REALM_POSITIONS: Record<string, { cx: number; cy: number; r: number }> = {
  matematik:  { cx: 400, cy: 120, r: 52 },   // center-top (biggest, most important)
  fizik:      { cx: 220, cy: 200, r: 44 },
  kimya:      { cx: 580, cy: 200, r: 44 },
  biyoloji:   { cx: 130, cy: 330, r: 40 },
  geometri:   { cx: 310, cy: 280, r: 44 },
  cografya:   { cx: 490, cy: 280, r: 44 },
  tarih:      { cx: 670, cy: 330, r: 40 },
  turkce:     { cx: 220, cy: 420, r: 44 },
  edebiyat:   { cx: 400, cy: 400, r: 44 },
  felsefe:    { cx: 580, cy: 420, r: 40 },
  din:        { cx: 140, cy: 520, r: 36 },
  oba:        { cx: 660, cy: 510, r: 36 },
};

const SUBJECT_ICONS: Record<string, string> = {
  matematik: '∑',
  fizik: 'ϕ',
  kimya: '⚗',
  biyoloji: '🧬',
  geometri: '△',
  cografya: '🗺',
  tarih: '⚔',
  turkce: 'Aa',
  edebiyat: '📖',
  felsefe: '💡',
  din: '☪',
  oba: '🛡',
};

function getMasteryRing(bkt: number) {
  if (bkt >= 0.80) return { stroke: '#10B981', width: 3, dash: '' };
  if (bkt >= 0.60) return { stroke: '#F59E0B', width: 2.5, dash: '6 3' };
  if (bkt >= 0.40) return { stroke: '#3B82F6', width: 2, dash: '4 4' };
  return { stroke: '#E5E7EB', width: 1.5, dash: '3 3' };
}

function hexPath(cx: number, cy: number, r: number) {
  const pts = Array.from({ length: 6 }, (_, i) => {
    const angle = (Math.PI / 3) * i - Math.PI / 6;
    return `${cx + r * Math.cos(angle)},${cy + r * Math.sin(angle)}`;
  });
  return `M${pts.join('L')}Z`;
}

export const RealmMap: React.FC<RealmMapProps> = ({
  realms,
  onRealmSelect,
  selectedSlug,
  className = '',
}) => {
  const [hovered, setHovered] = useState<string | null>(null);

  const realmMap = Object.fromEntries(realms.map((r) => [r.slug, r]));

  const handleClick = useCallback(
    (slug: string) => {
      const realm = realmMap[slug];
      if (realm) onRealmSelect(realm);
    },
    [realmMap, onRealmSelect]
  );

  return (
    <div className={`relative w-full ${className}`}>
      <svg
        viewBox="0 0 800 620"
        className="w-full h-auto"
        aria-label="YKS Alemler Haritası"
        role="img"
      >
        {/* Background gradient */}
        <defs>
          <radialGradient id="bg-grad" cx="50%" cy="40%" r="70%">
            <stop offset="0%" stopColor="#1E1B4B" />
            <stop offset="100%" stopColor="#0F0C29" />
          </radialGradient>
          <filter id="glow">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <filter id="glow-lg">
            <feGaussianBlur stdDeviation="6" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        <rect width="800" height="620" fill="url(#bg-grad)" rx="20" />

        {/* Star field */}
        {Array.from({ length: 60 }, (_, i) => (
          <circle
            key={`star-${i}`}
            cx={(i * 137.508) % 800}
            cy={(i * 97.32) % 620}
            r={Math.random() > 0.85 ? 1.5 : 0.8}
            fill="white"
            opacity={0.2 + (i % 5) * 0.08}
          />
        ))}

        {/* Connection lines between adjacent realms */}
        {[
          ['matematik', 'fizik'], ['matematik', 'kimya'],
          ['fizik', 'biyoloji'], ['fizik', 'geometri'],
          ['kimya', 'geometri'], ['kimya', 'cografya'],
          ['geometri', 'edebiyat'], ['cografya', 'edebiyat'],
          ['biyoloji', 'turkce'], ['turkce', 'edebiyat'],
          ['edebiyat', 'felsefe'], ['tarih', 'cografya'],
          ['turkce', 'din'], ['felsefe', 'oba'],
        ].map(([a, b], i) => {
          const pa = REALM_POSITIONS[a];
          const pb = REALM_POSITIONS[b];
          if (!pa || !pb) return null;
          return (
            <line
              key={`conn-${i}`}
              x1={pa.cx} y1={pa.cy}
              x2={pb.cx} y2={pb.cy}
              stroke="rgba(255,255,255,0.06)"
              strokeWidth="1"
              strokeDasharray="4 6"
            />
          );
        })}

        {/* Realm hexagons */}
        {Object.entries(REALM_POSITIONS).map(([slug, pos]) => {
          const realm = realmMap[slug];
          if (!realm) return null;

          const bkt = realm.progress?.bkt_score ?? 0;
          const ring = getMasteryRing(bkt);
          const isSelected = selectedSlug === slug;
          const isHovered = hovered === slug;
          const completed = realm.progress?.completed ?? false;
          const fillOpacity = completed ? 0.85 : isSelected ? 0.75 : isHovered ? 0.65 : 0.45;

          return (
            <g
              key={slug}
              onClick={() => handleClick(slug)}
              onMouseEnter={() => setHovered(slug)}
              onMouseLeave={() => setHovered(null)}
              style={{ cursor: 'pointer' }}
              role="button"
              aria-label={`${realm.name} - ${Math.round(bkt * 100)}% ustalık`}
              tabIndex={0}
              onKeyDown={(e) => e.key === 'Enter' && handleClick(slug)}
            >
              {/* Outer glow when selected/hovered */}
              {(isSelected || isHovered) && (
                <path
                  d={hexPath(pos.cx, pos.cy, pos.r + 8)}
                  fill="none"
                  stroke={realm.color_primary}
                  strokeWidth="2"
                  opacity="0.4"
                  filter="url(#glow)"
                />
              )}

              {/* Hex fill */}
              <path
                d={hexPath(pos.cx, pos.cy, pos.r)}
                fill={realm.color_primary}
                fillOpacity={fillOpacity}
                stroke={isSelected ? realm.color_primary : ring.stroke}
                strokeWidth={isSelected ? 3 : ring.width}
                strokeDasharray={ring.dash}
                filter={completed ? 'url(#glow)' : undefined}
                style={{
                  transition: 'fill-opacity 0.2s, stroke 0.2s',
                  transform: isSelected || isHovered ? `scale(1.08)` : 'scale(1)',
                  transformOrigin: `${pos.cx}px ${pos.cy}px`,
                }}
              />

              {/* Inner hex (lighter) */}
              <path
                d={hexPath(pos.cx, pos.cy, pos.r * 0.72)}
                fill={realm.color_secondary}
                fillOpacity={0.25}
              />

              {/* Subject icon */}
              <text
                x={pos.cx}
                y={pos.cy - 6}
                textAnchor="middle"
                dominantBaseline="middle"
                fontSize={pos.r > 44 ? 22 : pos.r > 40 ? 18 : 15}
                fill="white"
                style={{ userSelect: 'none' }}
              >
                {SUBJECT_ICONS[slug] ?? '⭐'}
              </text>

              {/* Realm name */}
              <text
                x={pos.cx}
                y={pos.cy + pos.r * 0.45}
                textAnchor="middle"
                fontSize={pos.r > 44 ? 10 : 8.5}
                fontWeight="600"
                fill="rgba(255,255,255,0.9)"
                style={{ userSelect: 'none' }}
              >
                {realm.name}
              </text>

              {/* BKT progress arc */}
              {bkt > 0 && (
                <circle
                  cx={pos.cx}
                  cy={pos.cy}
                  r={pos.r - 4}
                  fill="none"
                  stroke={ring.stroke}
                  strokeWidth="2"
                  strokeOpacity="0.6"
                  strokeDasharray={`${bkt * 2 * Math.PI * (pos.r - 4)} ${2 * Math.PI * (pos.r - 4)}`}
                  strokeDashoffset={Math.PI * (pos.r - 4) * 0.5}
                  style={{ transition: 'stroke-dasharray 0.8s ease' }}
                />
              )}

              {/* Completed checkmark */}
              {completed && (
                <text
                  x={pos.cx + pos.r * 0.55}
                  y={pos.cy - pos.r * 0.55}
                  fontSize="12"
                  fill="#10B981"
                  filter="url(#glow)"
                >
                  ✓
                </text>
              )}
            </g>
          );
        })}

        {/* Map title */}
        <text
          x="400"
          y="590"
          textAnchor="middle"
          fontSize="11"
          fill="rgba(255,255,255,0.3)"
          fontFamily="system-ui"
        >
          YKS Evren Haritası — 12 Konu Alemi
        </text>
      </svg>

      {/* Hovered realm tooltip */}
      {hovered && realmMap[hovered] && (
        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 pointer-events-none z-10">
          <div className="bg-gray-900/90 backdrop-blur-sm text-white text-xs px-3 py-2 rounded-lg border border-white/10 shadow-modern whitespace-nowrap">
            <span className="font-bold">{realmMap[hovered].name}</span>
            <span className="mx-1 opacity-50">·</span>
            <span className="opacity-70">{realmMap[hovered].era}</span>
            {realmMap[hovered].progress && (
              <>
                <span className="mx-1 opacity-50">·</span>
                <span className="text-emerald-400">
                  %{Math.round((realmMap[hovered].progress?.bkt_score ?? 0) * 100)} ustalık
                </span>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default RealmMap;
