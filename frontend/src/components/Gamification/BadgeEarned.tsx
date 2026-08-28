/**
 * BadgeEarned — Animated badge unlock modal/toast
 * FAZ-4: Gamification micro-interaction components
 */
import React, { useEffect, useState, useCallback } from 'react';

import { useFocusTrap } from '../../hooks/useFocusTrap';

interface BadgeEarnedProps {
  badge: {
    name: string;
    icon: string;       // emoji or URL
    category?: string;
    description?: string;
  };
  onClose?: () => void;
  autoCloseMs?: number;
  mode?: 'modal' | 'toast';
}

const RARITY_STYLES: Record<string, { ring: string; glow: string; label: string; labelColor: string }> = {
  common:    { ring: 'ring-gray-300',   glow: 'shadow-gray-200',   label: 'Yaygın',    labelColor: 'text-gray-500' },
  rare:      { ring: 'ring-blue-400',   glow: 'shadow-blue-200',   label: 'Nadir',     labelColor: 'text-blue-600' },
  epic:      { ring: 'ring-purple-400', glow: 'shadow-purple-200', label: 'Epik',      labelColor: 'text-purple-600' },
  legendary: { ring: 'ring-amber-400',  glow: 'shadow-amber-200',  label: 'Efsanevi',  labelColor: 'text-amber-600' },
};

const CATEGORY_EMOJI: Record<string, string> = {
  streak:  '🔥',
  quiz:    '📝',
  realm:   '🌍',
  social:  '👥',
  special: '⭐',
  default: '🏅',
};

export const BadgeEarned: React.FC<BadgeEarnedProps> = ({
  badge,
  onClose,
  autoCloseMs = 5000,
  mode = 'modal',
}) => {
  const [visible, setVisible] = useState(false);
  const [confetti, setConfetti] = useState<{ x: number; y: number; color: string; rot: number }[]>([]);

  const rarity = RARITY_STYLES[badge.category ?? 'common'] ?? RARITY_STYLES.common;
  const catEmoji = CATEGORY_EMOJI[badge.category ?? ''] ?? CATEGORY_EMOJI.default;

  const handleClose = useCallback(() => {
    setVisible(false);
    setTimeout(() => onClose?.(), 300);
  }, [onClose]);

  // Spawn confetti
  useEffect(() => {
    const pieces = Array.from({ length: 18 }, (_, i) => ({
      x: 20 + Math.random() * 60,
      y: -10 + Math.random() * 20,
      color: ['#667EEA', '#A855F7', '#EC4899', '#F59E0B', '#10B981'][i % 5],
      rot: Math.random() * 360,
    }));
    setConfetti(pieces);

    const rafId = requestAnimationFrame(() => setVisible(true));
    const timer = setTimeout(handleClose, autoCloseMs);

    return () => {
      cancelAnimationFrame(rafId);
      clearTimeout(timer);
    };
  }, [autoCloseMs, handleClose]);

  const isUrl = badge.icon.startsWith('http') || badge.icon.startsWith('/');

  // Modal modunda klavye focus'u kart icinde tutar + ESC ile kapatir (WCAG 2.1 focus trap).
  const dialogRef = useFocusTrap<HTMLDivElement>({
    enabled: mode === 'modal',
    onEscape: handleClose,
  });

  if (mode === 'toast') {
    return (
      <div
        className={[
          'fixed bottom-6 right-6 z-[9999] flex items-center gap-3 px-5 py-3',
          'bg-white rounded-2xl shadow-modern-lg border border-gray-100',
          'transition-all duration-300',
          visible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4',
        ].join(' ')}
        role="alert"
        aria-live="polite"
      >
        <span className="text-3xl animate-badge-pop inline-block">
          {isUrl ? (
            <img src={badge.icon} alt={badge.name} className="w-10 h-10 rounded-full object-cover" />
          ) : (
            badge.icon
          )}
        </span>
        <div>
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
            {catEmoji} Rozet Kazanıldı!
          </p>
          <p className="text-sm font-bold text-gray-800">{badge.name}</p>
        </div>
        <button
          onClick={handleClose}
          className="ml-2 text-gray-300 hover:text-gray-500 transition-colors text-xl leading-none"
          aria-label="Kapat"
        >
          ×
        </button>
      </div>
    );
  }

  return (
    <div
      className={[
        'fixed inset-0 z-[9999] flex items-center justify-center',
        'bg-black/50 backdrop-blur-sm',
        'transition-opacity duration-300',
        visible ? 'opacity-100' : 'opacity-0',
      ].join(' ')}
      onClick={handleClose}
      role="dialog"
      aria-modal="true"
      aria-label={`${badge.name} rozeti kazanıldı`}
    >
      {/* Confetti */}
      {confetti.map((p, i) => (
        <div
          key={i}
          className="absolute pointer-events-none animate-confetti-fall"
          style={{
            left: `${p.x}%`,
            top: `${p.y}%`,
            width: 8,
            height: 8,
            background: p.color,
            borderRadius: Math.random() > 0.5 ? '50%' : '2px',
            transform: `rotate(${p.rot}deg)`,
            animationDelay: `${i * 0.04}s`,
            animationDuration: `${0.8 + Math.random() * 0.6}s`,
          }}
        />
      ))}

      {/* Card */}
      <div
        ref={dialogRef}
        className={[
          'relative flex flex-col items-center gap-4 p-8 rounded-3xl',
          'bg-white shadow-modern-xl border border-gray-100',
          'max-w-xs w-full mx-4',
          'transition-all duration-300',
          visible ? 'scale-100 opacity-100' : 'scale-90 opacity-0',
        ].join(' ')}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <p className="text-xs font-bold text-gray-400 uppercase tracking-widest">
          {catEmoji} Yeni Rozet!
        </p>

        {/* Badge icon */}
        <div
          className={[
            'relative flex items-center justify-center w-28 h-28 rounded-full',
            'ring-4 shadow-lg animate-badge-pop',
            rarity.ring,
            rarity.glow,
          ].join(' ')}
          style={{ background: 'linear-gradient(135deg, #f8f8ff 0%, #e8e0ff 100%)' }}
        >
          {isUrl ? (
            <img
              src={badge.icon}
              alt={badge.name}
              className="w-20 h-20 object-contain"
            />
          ) : (
            <span className="text-5xl leading-none select-none">{badge.icon}</span>
          )}

          {/* Ping ring */}
          <div
            className={[
              'absolute inset-0 rounded-full animate-ping-once opacity-30',
              rarity.ring.replace('ring-', 'bg-').replace('-400', '-300').replace('-300', '-200'),
            ].join(' ')}
          />
        </div>

        {/* Rarity label */}
        <span className={`text-xs font-bold uppercase tracking-wider ${rarity.labelColor}`}>
          {rarity.label}
        </span>

        {/* Name */}
        <h2 className="text-xl font-bold text-gray-800 text-center font-display">
          {badge.name}
        </h2>

        {/* Description */}
        {badge.description && (
          <p className="text-sm text-gray-500 text-center leading-relaxed">
            {badge.description}
          </p>
        )}

        {/* Close button */}
        <button
          onClick={handleClose}
          className="mt-2 px-6 py-2.5 rounded-xl bg-gradient-xp text-white text-sm font-semibold
                     hover:opacity-90 active:scale-95 transition-all duration-150 shadow-glow"
        >
          Harika!
        </button>
      </div>
    </div>
  );
};

export default BadgeEarned;
