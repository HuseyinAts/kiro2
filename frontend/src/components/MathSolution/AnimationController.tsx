/**
 * Animasyon Kontrol Bileşeni
 * Requirements: REQ-51.26-51.30 (Animasyonlu geçişler)
 * 
 * Bu bileşen:
 * - Animasyon hızı kontrolü (yavaş/normal/hızlı)
 * - Animasyonları açma/kapama
 * - Smooth transitions (300-500ms)
 * - Visual transformation effects
 */

import React, { createContext, useContext, useState, ReactNode } from 'react';
import { Zap, ZapOff } from 'lucide-react';
import './AnimationController.css';

// Animation speed presets
export const ANIMATION_SPEEDS = {
  slow: {
    duration: 800,
    label: 'Yavaş',
    icon: '🐢'
  },
  normal: {
    duration: 400,
    label: 'Normal',
    icon: '🚶'
  },
  fast: {
    duration: 200,
    label: 'Hızlı',
    icon: '🏃'
  }
} as const;

export type AnimationSpeed = keyof typeof ANIMATION_SPEEDS;

interface AnimationContextType {
  enabled: boolean;
  speed: AnimationSpeed;
  duration: number;
  toggleAnimations: () => void;
  setSpeed: (speed: AnimationSpeed) => void;
  getTransitionConfig: () => {
    duration: number;
    ease: string;
  };
}

const AnimationContext = createContext<AnimationContextType | undefined>(undefined);

export const useAnimationContext = () => {
  const context = useContext(AnimationContext);
  if (!context) {
    throw new Error('useAnimationContext must be used within AnimationProvider');
  }
  return context;
};

interface AnimationProviderProps {
  children: ReactNode;
  defaultEnabled?: boolean;
  defaultSpeed?: AnimationSpeed;
}

export const AnimationProvider: React.FC<AnimationProviderProps> = ({
  children,
  defaultEnabled = true,
  defaultSpeed = 'normal'
}) => {
  const [enabled, setEnabled] = useState(defaultEnabled);
  const [speed, setSpeed] = useState<AnimationSpeed>(defaultSpeed);

  const toggleAnimations = () => {
    setEnabled(!enabled);
  };

  const getTransitionConfig = () => ({
    duration: enabled ? ANIMATION_SPEEDS[speed].duration / 1000 : 0,
    ease: 'easeOut'
  });

  const value: AnimationContextType = {
    enabled,
    speed,
    duration: ANIMATION_SPEEDS[speed].duration,
    toggleAnimations,
    setSpeed,
    getTransitionConfig
  };

  return (
    <AnimationContext.Provider value={value}>
      {children}
    </AnimationContext.Provider>
  );
};

interface AnimationControllerProps {
  className?: string;
}

const AnimationController: React.FC<AnimationControllerProps> = ({ className = '' }) => {
  const { enabled, speed, toggleAnimations, setSpeed } = useAnimationContext();

  const handleSpeedKeyDown = (e: React.KeyboardEvent, currentSpeed: AnimationSpeed) => {
    const speeds = Object.keys(ANIMATION_SPEEDS) as AnimationSpeed[];
    const currentIndex = speeds.indexOf(currentSpeed);

    if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
      e.preventDefault();
      const nextIndex = (currentIndex + 1) % speeds.length;
      setSpeed(speeds[nextIndex]);
    } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
      e.preventDefault();
      const prevIndex = (currentIndex - 1 + speeds.length) % speeds.length;
      setSpeed(speeds[prevIndex]);
    }
  };

  return (
    <div className={`animation-controller bg-white rounded-lg shadow-md p-4 ${className}`}>
      <div className="flex items-center justify-between gap-4">
        {/* Animation Toggle */}
        <div className="flex items-center gap-3">
          <button
            onClick={toggleAnimations}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all ${
              enabled
                ? 'bg-blue-600 text-white hover:bg-blue-700'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
            aria-label={enabled ? 'Animasyonları Kapat' : 'Animasyonları Aç'}
            title={enabled ? 'Animasyonları Kapat' : 'Animasyonları Aç'}
          >
            {enabled ? <Zap size={20} aria-hidden="true" /> : <ZapOff size={20} aria-hidden="true" />}
            <span>{enabled ? 'Animasyonlar Açık' : 'Animasyonlar Kapalı'}</span>
          </button>

          {/* Status Indicator */}
          <div 
            className={`w-3 h-3 rounded-full ${
              enabled ? 'bg-green-500 animate-pulse' : 'bg-gray-400'
            }`}
            role="status"
            aria-label={enabled ? 'Animasyonlar aktif' : 'Animasyonlar kapalı'}
          />
        </div>

        {/* Speed Control */}
        {enabled && (
          <div className="flex items-center gap-2" role="group" aria-label="Animasyon hızı seçimi">
            <span id="speed-label" className="text-sm font-medium text-gray-700">Hız:</span>
            <div className="flex gap-2" role="radiogroup" aria-labelledby="speed-label">
              {(Object.keys(ANIMATION_SPEEDS) as AnimationSpeed[]).map((speedKey) => {
                const speedConfig = ANIMATION_SPEEDS[speedKey];
                const isActive = speed === speedKey;
                
                return (
                  <button
                    key={speedKey}
                    onClick={() => setSpeed(speedKey)}
                    onKeyDown={(e) => handleSpeedKeyDown(e, speedKey)}
                    className={`px-3 py-2 rounded-lg font-medium transition-all ${
                      isActive
                        ? 'bg-blue-600 text-white ring-2 ring-blue-300'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                    role="radio"
                    aria-checked={isActive}
                    aria-label={`${speedConfig.label} hız: ${speedConfig.duration} milisaniye`}
                    title={`${speedConfig.label} (${speedConfig.duration}ms)`}
                    tabIndex={isActive ? 0 : -1}
                  >
                    <span className="text-lg mr-1" aria-hidden="true">{speedConfig.icon}</span>
                    <span className="text-sm">{speedConfig.label}</span>
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* Info Text */}
      <div 
        className="mt-3 text-xs text-gray-700"
        role="status"
        aria-live="polite"
        aria-atomic="true"
      >
        {enabled ? (
          <p>
            <span aria-hidden="true">✨</span> Animasyonlar aktif - Geçişler {ANIMATION_SPEEDS[speed].duration}ms sürecek
          </p>
        ) : (
          <p>
            <span aria-hidden="true">⚡</span> Animasyonlar kapalı - Anında geçişler yapılacak
          </p>
        )}
      </div>
    </div>
  );
};

export default AnimationController;
