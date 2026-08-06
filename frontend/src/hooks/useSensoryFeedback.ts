import { useCallback, useEffect, useRef } from 'react';

/**
 * Advanced 2026 Web Audio API Procedural Sound Synthesizer
 * Generates ASMR-like haptic and sensory sound feedback entirely in code
 * No MP3s required -> Zero network cost, zero latency.
 */
export const useSensoryFeedback = () => {
  const audioCtxRef = useRef<AudioContext | null>(null);

  useEffect(() => {
    // Initialize lazily to respect browser autoplay policies
    const initAudio = () => {
      if (!audioCtxRef.current) {
        audioCtxRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
      }
    };

    window.addEventListener('click', initAudio, { once: true });
    window.addEventListener('keydown', initAudio, { once: true });
    return () => {
      window.removeEventListener('click', initAudio);
      window.removeEventListener('keydown', initAudio);
      if (audioCtxRef.current?.state !== 'closed') {
        audioCtxRef.current?.close();
      }
    };
  }, []);

  const playTone = useCallback((frequency: number, type: OscillatorType, duration: number, volume: number) => {
    if (!audioCtxRef.current) return;
    
    const ctx = audioCtxRef.current;
    if (ctx.state === 'suspended') ctx.resume();

    const osc = ctx.createOscillator();
    const gainNode = ctx.createGain();

    osc.type = type;
    osc.frequency.setValueAtTime(frequency, ctx.currentTime);

    // Envelope (ASMR smooth fade out)
    gainNode.gain.setValueAtTime(0, ctx.currentTime);
    gainNode.gain.linearRampToValueAtTime(volume, ctx.currentTime + 0.02);
    gainNode.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + duration);

    osc.connect(gainNode);
    gainNode.connect(ctx.destination);

    osc.start();
    osc.stop(ctx.currentTime + duration);
  }, []);

  const playSuccess = useCallback(() => {
    // Chime up (e.g. solving a question right)
    playTone(440, 'sine', 0.3, 0.1);
    setTimeout(() => playTone(554.37, 'sine', 0.4, 0.1), 100);
    setTimeout(() => playTone(659.25, 'sine', 0.6, 0.1), 200);
    
    // Attempt device haptic feedback if available
    if (navigator.vibrate) {
      navigator.vibrate([20, 30, 40]);
    }
  }, [playTone]);

  const playHover = useCallback(() => {
    // Very subtle tick (Tactile Brutalism feel)
    playTone(800, 'sine', 0.05, 0.02);
  }, [playTone]);

  const playClick = useCallback(() => {
    // Deep mechanical click
    playTone(150, 'triangle', 0.1, 0.05);
    if (navigator.vibrate) {
      navigator.vibrate(10);
    }
  }, [playTone]);

  const playError = useCallback(() => {
    // Low double bump
    playTone(200, 'sawtooth', 0.2, 0.05);
    setTimeout(() => playTone(150, 'sawtooth', 0.3, 0.05), 150);
    if (navigator.vibrate) {
      navigator.vibrate([40, 40, 40]);
    }
  }, [playTone]);

  return { playSuccess, playHover, playClick, playError };
};
