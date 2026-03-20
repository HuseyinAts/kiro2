/**
 * StreakBadge — Animated daily streak indicator
 * FAZ-4: Gamification micro-interaction components
 */
import React from 'react';

interface StreakBadgeProps {
  streak: number;
  isActiveToday?: boolean;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
  className?: string;
}

const STREAK_TIERS = [
  { min: 0,   max: 2,   label: 'Yeni',      emoji: '🌱', color: 'text-green-600',  bg: 'bg-green-50',   border: 'border-green-200' },
  { min: 3,   max: 6,   label: 'Alev',      emoji: '🔥', color: 'text-orange-600', bg: 'bg-orange-50',  border: 'border-orange-200' },
  { min: 7,   max: 13,  label: 'Kor',       emoji: '🔥', color: 'text-red-600',    bg: 'bg-red-50',     border: 'border-red-200' },
  { min: 14,  max: 29,  label: 'Ejder',     emoji: '🐉', color: 'text-purple-600', bg: 'bg-purple-50',  border: 'border-purple-200' },
  { min: 30,  max: 99,  label: 'Efsane',    emoji: '⚡', color: 'text-yellow-600', bg: 'bg-yellow-50',  border: 'border-yellow-200' },
  { min: 100, max: Infinity, label: 'Tanrı', emoji: '👑', color: 'text-amber-600',  bg: 'bg-amber-50',   border: 'border-amber-200' },
];

const SIZE_CLASSES = {
  sm: { wrapper: 'px-2 py-1 gap-1', emoji: 'text-sm', count: 'text-sm', label: 'text-xs' },
  md: { wrapper: 'px-3 py-2 gap-1.5', emoji: 'text-xl', count: 'text-lg', label: 'text-sm' },
  lg: { wrapper: 'px-4 py-3 gap-2', emoji: 'text-3xl', count: 'text-2xl', label: 'text-base' },
};

function getTier(streak: number) {
  return (
    STREAK_TIERS.find((t) => streak >= t.min && streak <= t.max) ?? STREAK_TIERS[0]
  );
}

export const StreakBadge: React.FC<StreakBadgeProps> = ({
  streak,
  isActiveToday = true,
  size = 'md',
  showLabel = true,
  className = '',
}) => {
  const tier = getTier(streak);
  const sizes = SIZE_CLASSES[size];
  const isHot = streak >= 3;

  return (
    <div
      className={[
        'inline-flex items-center rounded-2xl border-2 font-display font-semibold',
        'transition-all duration-300 select-none',
        sizes.wrapper,
        tier.bg,
        tier.border,
        isActiveToday ? 'opacity-100' : 'opacity-50 grayscale',
        isHot && isActiveToday ? 'animate-streak-burn' : '',
        className,
      ]
        .filter(Boolean)
        .join(' ')}
      title={`${streak} günlük seri${isActiveToday ? '' : ' (bugün aktif değil)'}`}
    >
      {/* Emoji */}
      <span
        className={[sizes.emoji, isHot && isActiveToday ? 'animate-wiggle' : ''].join(' ')}
        aria-hidden="true"
      >
        {tier.emoji}
      </span>

      {/* Count */}
      <span className={`${sizes.count} ${tier.color} font-bold tabular-nums`}>
        {streak}
      </span>

      {/* Label */}
      {showLabel && (
        <span className={`${sizes.label} ${tier.color} opacity-80`}>
          {size === 'sm' ? 'gün' : `gün · ${tier.label}`}
        </span>
      )}

      {/* Active today dot */}
      {isActiveToday && (
        <span className="relative flex h-2 w-2 ml-0.5">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
          <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500" />
        </span>
      )}
    </div>
  );
};

/** Mini version for inline use (e.g. inside lists) */
export const StreakDot: React.FC<{ streak: number; className?: string }> = ({
  streak,
  className = '',
}) => {
  const tier = getTier(streak);
  return (
    <span
      className={`inline-flex items-center gap-0.5 text-xs font-bold ${tier.color} ${className}`}
    >
      {tier.emoji} {streak}
    </span>
  );
};

export default StreakBadge;
