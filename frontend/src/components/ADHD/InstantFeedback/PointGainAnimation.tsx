/**
 * Task 92.2: Point Gain Animation Component
 * Puan kazanma görsel geri bildirimi
 */
import { useEffect, useState } from 'react';
import type { FC } from 'react';
import './PointGainAnimation.css';

interface PointGainAnimationProps {
  points: number;
  isVisible: boolean;
  onComplete?: () => void;
  position?: { x: number; y: number };
  color?: string;
  showMultiplier?: boolean;
  multiplier?: number;
}

export const PointGainAnimation: FC<PointGainAnimationProps> = ({
  points,
  isVisible,
  onComplete,
  position,
  color = '#4ade80',
  showMultiplier = false,
  multiplier = 1,
}) => {
  const [particles, setParticles] = useState<Array<{ id: number; angle: number }>>([]);

  useEffect(() => {
    if (isVisible && points > 0) {
      // Generate particles
      const particleCount = Math.min(Math.floor(points / 10) + 5, 20);
      const newParticles = Array.from({ length: particleCount }, (_, i) => ({
        id: i,
        angle: (360 / particleCount) * i,
      }));
      setParticles(newParticles);

      // Auto-complete after animation
      const timer = setTimeout(() => {
        onComplete?.();
        setParticles([]);
      }, 1500);

      return () => clearTimeout(timer);
    }
  }, [isVisible, points, onComplete]);

  if (!isVisible || points === 0) {return null;}

  const displayPoints = Math.round(points * multiplier);
  const style = position
    ? { top: `${position.y}px`, left: `${position.x}px` }
    : {};

  return (
    <div className="point-gain-animation" style={style}>
      {/* Main point display */}
      <div className="point-display" style={{ color }}>
        <span className="plus-sign">+</span>
        <span className="point-value">{displayPoints}</span>
        <span className="point-label">XP</span>

        {showMultiplier && multiplier > 1 && (
          <div className="multiplier-badge">x{multiplier}</div>
        )}
      </div>

      {/* Particle effects */}
      <div className="particles-container">
        {particles.map((particle) => (
          <div
            key={particle.id}
            className="particle"
            style={{
              transform: `rotate(${particle.angle}deg) translateY(-50px)`,
              backgroundColor: color,
            }}
          />
        ))}
      </div>

      {/* Glow effect */}
      <div className="glow-effect" style={{ backgroundColor: color }} />

      {/* Coin icons for visual appeal */}
      {displayPoints >= 50 && (
        <div className="coin-shower">
          {Array.from({ length: Math.min(Math.floor(displayPoints / 50), 5) }).map(
            (_, i) => (
              <div
                key={i}
                className="coin"
                style={{
                  left: `${20 + i * 15}%`,
                  animationDelay: `${i * 0.1}s`,
                }}
              >
                💰
              </div>
            ),
          )}
        </div>
      )}
    </div>
  );
};

export default PointGainAnimation;
