/**
 * Task 92.1: Success Animation Component
 * DEHB için anında pozitif geri bildirim animasyonları
 */
import React, { useEffect, useState } from 'react';
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
  levelup: ['Seviye atladın! 🚀', 'Level Up! 🌠']
};

export const SuccessAnimation: React.FC<SuccessAnimationProps> = ({
  isVisible,
  message,
  type = 'correct',
  onComplete,
  duration = 2000,
  showConfetti = true,
  soundEnabled = true
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

  const playSuccessSound = (type: string) => {
    try {
      // Web Audio API için basit ses
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();

      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);

      // Farklı tiplar için farklı tonlar
      const frequencies = {
        correct: [523.25, 659.25, 783.99], // C, E, G (major chord)
        streak: [659.25, 783.99, 987.77], // E, G, B
        achievement: [523.25, 698.46, 880.00], // C, F, A
        levelup: [523.25, 659.25, 783.99, 1046.50] // C major scale up
      };

      const notes = frequencies[type as keyof typeof frequencies];
      let noteIndex = 0;

      oscillator.frequency.value = notes[noteIndex];
      oscillator.type = 'sine';
      gainNode.gain.value = 0.3;

      oscillator.start(audioContext.currentTime);

      // Play notes in sequence
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

  if (!isVisible) return null;

  return (
    <div className={`success-animation ${type}`}>
      {/* Confetti */}
      {showConfetti && (
        <div className="confetti-container">
          {confettiPieces.map((piece) => (
            <div
              key={piece}
              className="confetti-piece"
              style={{
                left: `${Math.random() * 100}%`,
                animationDelay: `${Math.random() * 0.5}s`,
                backgroundColor: getRandomColor()
              }}
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

function getRandomColor(): string {
  const colors = [
    '#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A',
    '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E2'
  ];
  return colors[Math.floor(Math.random() * colors.length)];
}

export default SuccessAnimation;
