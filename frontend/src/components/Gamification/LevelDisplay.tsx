/**
 * LevelDisplay Component - Task 91
 * Kullanıcı seviye ve XP gösterimi
 */
import * as React from 'react';
import {  useEffect, useRef, useState  } from 'react';

import { useLevel } from '../../hooks/useGamification';
import './LevelDisplay.css';

interface LevelDisplayProps {
  showMilestones?: boolean;
  compact?: boolean;
  onLevelUp?: (newLevel: number) => void;
}

export const LevelDisplay: React.FC<LevelDisplayProps> = ({
  showMilestones = true,
  compact = false,
  onLevelUp,
}) => {
  const { levelProgress, loading, error, getMilestones } = useLevel();
  const [milestones, setMilestones] = useState<number[]>([]);
  const [isLevelingUp, setIsLevelingUp] = useState(false);
  const [previousLevel, setPreviousLevel] = useState<number | null>(null);

  useEffect(() => {
    if (showMilestones) {
      getMilestones().then(setMilestones);
    }
  }, [showMilestones, getMilestones]);

  const levelUpTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (levelProgress && previousLevel !== null) {
      if (levelProgress.current_level > previousLevel) {
        setIsLevelingUp(true);
        onLevelUp?.(levelProgress.current_level);
        levelUpTimerRef.current = setTimeout(() => setIsLevelingUp(false), 3000);
      }
    }
    if (levelProgress) {
      setPreviousLevel(levelProgress.current_level);
    }
    return () => {
      if (levelUpTimerRef.current) {clearTimeout(levelUpTimerRef.current);}
    };
  }, [levelProgress, previousLevel, onLevelUp]);

  if (loading && !levelProgress) {
    return (
      <div className="level-display loading">
        <div className="spinner"></div>
      </div>
    );
  }

  if (error || !levelProgress) {
    return (
      <div className="level-display error">
        <span className="error-icon">⚠️</span>
        <span className="error-message">Seviye bilgisi yüklenemedi</span>
      </div>
    );
  }

  const {
    current_level,
    total_xp,
    xp_in_current_level,
    xp_needed_for_next,
    progress_percentage,
    next_level,
    next_milestone,
  } = levelProgress;

  const isMilestone = milestones.includes(current_level);

  if (compact) {
    return (
      <div className={`level-display compact ${isMilestone ? 'milestone' : ''}`}>
        <span className="level-badge">
          {isMilestone ? '🏆' : '⚡'}
          <span className="level-number">Lv {current_level}</span>
        </span>
      </div>
    );
  }

  return (
    <div className={`level-display ${isLevelingUp ? 'leveling-up' : ''}`}>
      {isLevelingUp && (
        <div className="level-up-animation">
          <div className="level-up-content">
            <div className="level-up-icon">🎉</div>
            <div className="level-up-text">Seviye Atladın!</div>
            <div className="level-up-level">Seviye {current_level}</div>
          </div>
        </div>
      )}

      <div className="level-header">
        <h3>Seviye & XP</h3>
        {isMilestone && (
          <div className="milestone-badge">
            <span className="milestone-icon">🏆</span>
            <span className="milestone-text">Milestone!</span>
          </div>
        )}
      </div>

      <div className="level-main">
        <div className={`level-badge-large ${isMilestone ? 'milestone' : ''}`}>
          <div className="level-badge-icon">
            {isMilestone ? '🏆' : '⚡'}
          </div>
          <div className="level-badge-number">{current_level}</div>
          <div className="level-badge-label">Seviye</div>
        </div>

        <div className="level-info">
          <div className="xp-display">
            <div className="xp-label">Toplam XP</div>
            <div className="xp-value">{total_xp.toLocaleString('tr-TR')}</div>
          </div>

          <div className="progress-section">
            <div className="progress-header">
              <span className="progress-label">Seviye {next_level}&apos;e İlerleme</span>
              <span className="progress-percentage">{Math.round(progress_percentage)}%</span>
            </div>
            <div className="progress-bar-container">
              <div
                className="progress-bar-fill"
                style={{ width: `${progress_percentage}%` }}
              >
                <div className="progress-bar-glow"></div>
              </div>
            </div>
            <div className="progress-footer">
              <span className="xp-current">{xp_in_current_level} XP</span>
              <span className="xp-needed">{xp_needed_for_next} XP gerekli</span>
            </div>
          </div>

          {next_milestone && (
            <div className="next-milestone">
              <span className="next-milestone-icon">🎯</span>
              <span className="next-milestone-text">
                Sonraki Milestone: <strong>Seviye {next_milestone}</strong>
              </span>
            </div>
          )}
        </div>
      </div>

      {showMilestones && milestones.length > 0 && (
        <div className="milestones-section">
          <h4>Milestone Seviyeleri</h4>
          <div className="milestones-list">
            {milestones.map((milestone) => (
              <div
                key={milestone}
                className={`milestone-item ${
                  current_level >= milestone ? 'achieved' : ''
                } ${current_level === milestone ? 'current' : ''}`}
              >
                <span className="milestone-level">{milestone}</span>
                {current_level >= milestone && (
                  <span className="milestone-check">✓</span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default LevelDisplay;
