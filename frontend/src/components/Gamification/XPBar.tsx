/**
 * XPBar — Animated XP progress bar
 * FAZ-4: Gamification micro-interaction components
 */
import React, { useEffect, useRef } from 'react';

interface XPBarProps {
  currentXP: number;
  maxXP: number;
  level: number;
  xpGained?: number;   // animate delta if provided
  showLabel?: boolean;
  className?: string;
}

export const XPBar: React.FC<XPBarProps> = ({
  currentXP,
  maxXP,
  level,
  xpGained,
  showLabel = true,
  className = '',
}) => {
  const fillRef = useRef<HTMLDivElement>(null);
  const prevXP = currentXP - (xpGained ?? 0);
  const prevPercent = Math.min(100, Math.max(0, (prevXP / maxXP) * 100));
  const currentPercent = Math.min(100, Math.max(0, (currentXP / maxXP) * 100));

  useEffect(() => {
    const el = fillRef.current;
    if (!el) {return;}

    // Start from previous value, animate to current
    el.style.width = `${prevPercent}%`;
    el.style.setProperty('--xp-percent', `${currentPercent}%`);

    const raf = requestAnimationFrame(() => {
      el.style.transition = 'width 0.8s cubic-bezier(0.22, 1, 0.36, 1)';
      el.style.width = `${currentPercent}%`;
    });

    return () => cancelAnimationFrame(raf);
  }, [currentXP, currentPercent, prevPercent]);

  return (
    <div className={`w-full ${className}`}>
      {showLabel && (
        <div className="flex items-center justify-between mb-1.5">
          <span className="flex items-center gap-1.5 text-sm font-semibold text-xp-text font-display">
            <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-xp-bg text-xs font-bold">
              {level}
            </span>
            Seviye {level}
          </span>
          <span className="text-xs text-gray-500 font-mono">
            {currentXP.toLocaleString('tr')} / {maxXP.toLocaleString('tr')} XP
          </span>
        </div>
      )}

      {/* Track */}
      <div className="relative h-3 w-full rounded-full bg-gray-100 overflow-hidden shadow-inner">
        {/* Shimmer overlay */}
        <div
          className="absolute inset-0 opacity-0 hover:opacity-100 transition-opacity duration-300"
          style={{
            background:
              'linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.4) 50%, transparent 100%)',
            animation: 'shimmer 2s infinite',
          }}
        />

        {/* Fill bar */}
        <div
          ref={fillRef}
          className="h-full rounded-full relative"
          style={{
            background: 'linear-gradient(90deg, #667EEA 0%, #A855F7 50%, #EC4899 100%)',
            width: `${prevPercent}%`,
            boxShadow: '0 0 8px rgba(168, 85, 247, 0.5)',
          }}
        >
          {/* Glint */}
          <div
            className="absolute top-0.5 left-2 right-4 h-1 rounded-full opacity-40"
            style={{ background: 'rgba(255,255,255,0.8)' }}
          />
        </div>

        {/* XP gained flash */}
        {xpGained && xpGained > 0 && (
          <div
            className="absolute top-0 h-full rounded-full animate-ping-once opacity-60"
            style={{
              left: `${prevPercent}%`,
              width: `${currentPercent - prevPercent}%`,
              background: 'rgba(168,85,247,0.5)',
            }}
          />
        )}
      </div>

      {/* XP gained badge */}
      {xpGained && xpGained > 0 && (
        <div className="mt-1 flex justify-end">
          <span className="inline-flex items-center gap-0.5 text-xs font-bold text-xp-text animate-fade-in-up">
            +{xpGained} XP
          </span>
        </div>
      )}
    </div>
  );
};

export default XPBar;
