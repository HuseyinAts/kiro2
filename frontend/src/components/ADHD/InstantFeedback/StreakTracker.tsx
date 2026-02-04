/**
 * Task 92.3: Streak Tracker Component
 * Ardışık doğru cevap takibi ve gösterimi
 */
import React, { useEffect, useState } from 'react';
import './StreakTracker.css';

interface StreakTrackerProps {
  currentStreak: number;
  bestStreak?: number;
  onStreakUpdate?: (streak: number) => void;
  showFireAnimation?: boolean;
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left';
}

const STREAK_MILESTONES = [3, 5, 10, 15, 20, 30, 50, 100];

const STREAK_MESSAGES = {
  3: 'Harika başlangıç! 🔥',
  5: 'Devam et! ⚡',
  10: 'Süpersin! 🌟',
  15: 'İnanılmaz! 💪',
  20: 'Durdurulamazsın! 🚀',
  30: 'Efsane! 👑',
  50: 'Müthiş! 🏆',
  100: 'Rekor kırdın! 🎊'
};

export const StreakTracker: React.FC<StreakTrackerProps> = ({
  currentStreak,
  bestStreak = 0,
  onStreakUpdate,
  showFireAnimation = true,
  position = 'top-right'
}) => {
  const [previousStreak, setPreviousStreak] = useState(currentStreak);
  const [showMilestone, setShowMilestone] = useState(false);
  const [milestoneMessage, setMilestoneMessage] = useState('');
  const [flames, setFlames] = useState<number>(0);

  useEffect(() => {
    if (currentStreak !== previousStreak) {
      // Check if milestone reached
      const milestone = STREAK_MILESTONES.find(m =>
        currentStreak >= m && previousStreak < m
      );

      if (milestone) {
        setMilestoneMessage(STREAK_MESSAGES[milestone as keyof typeof STREAK_MESSAGES]);
        setShowMilestone(true);
        setTimeout(() => setShowMilestone(false), 3000);
      }

      // Update flames
      setFlames(Math.min(Math.floor(currentStreak / 3), 10));

      setPreviousStreak(currentStreak);
      onStreakUpdate?.(currentStreak);
    }
  }, [currentStreak, previousStreak, onStreakUpdate]);

  const isNewRecord = currentStreak > bestStreak;
  const progressToNextMilestone = STREAK_MILESTONES.find(m => m > currentStreak) || 100;
  const progressPercentage = Math.min((currentStreak / progressToNextMilestone) * 100, 100);

  return (
    <div className={`streak-tracker ${position}`}>
      {/* Compact display */}
      <div className={`streak-compact ${currentStreak > 0 ? 'active' : ''}`}>
        <div className="streak-icon-container">
          <span className="streak-icon">🔥</span>
          {showFireAnimation && currentStreak > 0 && (
            <div className="fire-animation">
              {Array.from({ length: flames }).map((_, i) => (
                <div
                  key={i}
                  className="flame"
                  style={{
                    left: `${(i * 10) - flames * 5}%`,
                    animationDelay: `${i * 0.1}s`
                  }}
                />
              ))}
            </div>
          )}
        </div>

        <div className="streak-info">
          <div className="streak-number">
            {currentStreak}
            {isNewRecord && currentStreak > 0 && (
              <span className="record-badge">REKOR!</span>
            )}
          </div>
          <div className="streak-label">Seri</div>
        </div>
      </div>

      {/* Progress bar */}
      {currentStreak > 0 && (
        <div className="streak-progress">
          <div className="progress-bar-container">
            <div
              className="progress-bar-fill"
              style={{ width: `${progressPercentage}%` }}
            />
          </div>
          <div className="progress-label">
            {progressToNextMilestone - currentStreak} adım kaldı
          </div>
        </div>
      )}

      {/* Best streak */}
      {bestStreak > 0 && (
        <div className="best-streak">
          <span className="best-streak-label">En İyi:</span>
          <span className="best-streak-value">{bestStreak}</span>
        </div>
      )}

      {/* Milestone celebration */}
      {showMilestone && (
        <div className="milestone-celebration">
          <div className="milestone-content">
            <div className="milestone-icon">🎉</div>
            <div className="milestone-message">{milestoneMessage}</div>
            <div className="milestone-streak">{currentStreak} Seri!</div>
          </div>

          {/* Fireworks */}
          <div className="fireworks">
            {Array.from({ length: 5 }).map((_, i) => (
              <div
                key={i}
                className="firework"
                style={{
                  left: `${20 + i * 15}%`,
                  animationDelay: `${i * 0.2}s`
                }}
              >
                ✨
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Streak multiplier indicator */}
      {currentStreak >= 5 && (
        <div className="multiplier-indicator">
          <span className="multiplier-icon">⚡</span>
          <span className="multiplier-text">
            x{Math.floor(1 + currentStreak / 10)} Puan
          </span>
        </div>
      )}
    </div>
  );
};

export default StreakTracker;
