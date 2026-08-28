import { useState, useCallback } from 'react';

export function useVideoControls(videoRef: React.RefObject<HTMLVideoElement>, announce: (message: string, priority?: 'assertive' | 'polite') => void) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(1);
  const [isMuted, setIsMuted] = useState(false);
  const [playbackRate, setPlaybackRate] = useState(1);

  const togglePlay = useCallback(() => {
    if (videoRef.current) {
      if (isPlaying) videoRef.current.pause();
      else videoRef.current.play();
    }
  }, [isPlaying, videoRef]);

  const handleSeek = useCallback((newTime: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = newTime;
      setCurrentTime(newTime);
      announce(`${Math.floor(newTime)} konumuna gidildi`, 'polite');
    }
  }, [videoRef, announce]);

  const toggleMute = useCallback(() => {
    if (videoRef.current) {
      const newMuted = !isMuted;
      videoRef.current.muted = newMuted;
      setIsMuted(newMuted);
      announce(newMuted ? 'Ses kapatıldı' : 'Ses açıldı', 'polite');
    }
  }, [isMuted, videoRef, announce]);

  return {
    isPlaying, setIsPlaying,
    currentTime, setCurrentTime,
    duration, setDuration,
    volume, setVolume,
    isMuted, setIsMuted,
    playbackRate, setPlaybackRate,
    togglePlay, handleSeek, toggleMute
  };
}
