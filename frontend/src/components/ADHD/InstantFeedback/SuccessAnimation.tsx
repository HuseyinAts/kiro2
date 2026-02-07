/**
 * Task 92.1: Success Animation Component
 * DEHB için anında pozitif geri bildirim animasyonları
 */
import { useEffect, useState, useMemo } from 'react';
import type { FC } from 'react';
import './SuccessAnimation.css';

interface SuccessAnimationProps {
  isVisible: boolean;
  message?: string;
  type?: 'correct' | 'streak' | 'achievement' | 'levelup';
  onComplete?: () => void;
  duration?: number; // milliseconds
  showConfetti?: boolean;
  soundEnabled?: boolean;
}

const SUCCESS_MESSAGES = {
  correct: ['Harika! 🎉', 'Mükemmel! ⭐', 'Süper! 🌟', 'Bravo! 👏', 'Aferin! 🎯'],
  streak: ['Seri devam! 🔥', 'Durdurulamazsın! ⚡', 'Süpersin! 💪'],
  achievement: ['Başarı kazandın! 🏆', 'Tebrikler! 🎊'],
  levelup: ['Seviye atladın! 🚀', 'Level Up! 🌠'],
};

// Helper function - moved outside component to avoid recreation
const playSuccessSound = (type: string): void => {
  try {
    const audioContext = new (window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext)();
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();

    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);

    const frequencies: Record<string, number[]> = {
      correct: [523.25, 659.25, 783.99],
      streak: [659.25, 783.99, 987.77],
      achievement: [523.25, 698.46, 880.00],
      levelup: [523.25, 659.25, 783.99, 1046.50],
    };

    const notes = frequencies[type] || frequencies.correct;

    oscillator.frequency.value = notes[0];
    oscillator.type = 'sine';
    gainNode.gain.value = 0.3;

    oscillator.start(audioContext.currentTime);

    notes.forEach((freq, index) => {
      setTimeout(() => {
        oscillator.frequency.value = freq;
      }, index * 100);
    });

    oscillator.stop(audioContext.currentTime + 0.5);
  } catch (error) {
    console.warn('Audio playback not supported:', error);
  }
};

const CONFETTI_COLORS = [
  '#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A',
  '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E2',
];

export const SuccessAnimation: FC<SuccessAnimationProps> = ({
  isVisible,
  message,
  type = 'correct',
  onComplete,
  duration = 2000,
  showConfetti = true,
  soundEnabled = true,
}) => {
  const [displayMessage, setDisplayMessage] = useState('');
  const [confettiPieces, setConfettiPieces] = useState<number[]>([]);

  useEffect(() => {
    if (isVisible) {
      // Random message selection
      const messages = SUCCESS_MESSAGES[type];
      const randomMessage = message || messages[Math.floor(Math.random() * messages.length)];
      setDisplayMessage(randomMessage);

      // Generate confetti
      if (showConfetti) {
        setConfettiPieces(Array.from({ length: 30 }, (_, i) => i));
      }

      // Play success sound
      if (soundEnabled) {
        playSuccessSound(type);
      }

      // Auto-hide after duration
      const timer = setTimeout(() => {
        onComplete?.();
      }, duration);

      return () => clearTimeout(timer);
    } else {
      setConfettiPieces([]);
    }
  }, [isVisible, message, type, onComplete, duration, showConfetti, soundEnabled]);

  // Pre-compute confetti styles to avoid Math.random() in render
  const confettiStyles = useMemo(() =>
    confettiPieces.map((piece) => ({
      left: `${(piece * 3.33) % 100}%`,
      animationDelay: `${(piece * 0.017) % 0.5}s`,
      backgroundColor: CONFETTI_COLORS[piece % CONFETTI_COLORS.length],
    })),
    [confettiPieces],
  );

  if (!isVisible) {return null;}

  return (
    <div className={`success-animation ${type}`}>
      {/* Confetti */}
      {showConfetti && (
        <div className="confetti-container">
          {confettiPieces.map((piece, index) => (
            <div
              key={piece}
              className="confetti-piece"
              style={confettiStyles[index]}
            />
          ))}
        </div>
      )}

      {/* Main animation */}
      <div className="success-content">
        <div className="success-icon-container">
          {type === 'correct' && <span className="success-icon">✓</span>}
          {type === 'streak' && <span className="success-icon">🔥</span>}
          {type === 'achievement' && <span className="success-icon">🏆</span>}
          {type === 'levelup' && <span className="success-icon">🚀</span>}
        </div>

        <div className="success-message">{displayMessage}</div>

        {/* Ripple effect */}
        <div className="ripple-effect">
          <div className="ripple ripple-1"></div>
          <div className="ripple ripple-2"></div>
          <div className="ripple ripple-3"></div>
        </div>
      </div>

      {/* Star burst */}
      <div className="star-burst">
        {Array.from({ length: 8 }).map((_, i) => (
          <div
            key={i}
            className="star-ray"
            style={{ transform: `rotate(${i * 45}deg)` }}
          />
        ))}
      </div>
    </div>
  );
};

export default SuccessAnimation;
